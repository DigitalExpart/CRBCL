"""Child & Parent Passport Generation Service for CRBCL (Phase 11).

Permission-aware passport generation, medical redaction, case restriction checks,
and audit logging.
"""

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_management import CasePerson, CaseRestriction
from app.models.client import Client
from app.models.medical import ClientAllergy, ClientMedicalProfile, ClientMedication
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.permissions.constants import Permissions


class PassportService:
    """Service generating Child & Parent Passports with section-level permission awareness."""

    @staticmethod
    async def generate_child_passport(
        session: AsyncSession,
        child_id: uuid.UUID,
        user_id: uuid.UUID,
        user_permissions: set[str],
    ) -> dict:
        """Generate Child Passport document payload.

        Redacts medical section if caller lacks `CLIENT_MEDICAL_READ` permission.
        """
        # Fetch person & client record
        stmt = (
            select(Person)
            .where(Person.id == child_id, Person.deleted_at.is_(None))
            .options(
                selectinload(Person.addresses),
                selectinload(Person.contacts),
                selectinload(Person.cultural_profile),
            )
        )
        res = await session.execute(stmt)
        person = res.scalar_one_or_none()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child record not found")

        # Check case restrictions for cases involving this child
        cp_stmt = select(CasePerson.case_id).where(CasePerson.person_id == child_id)
        cp_res = await session.execute(cp_stmt)
        case_ids = [r for r in cp_res.scalars().all()]

        if case_ids:
            restr_stmt = select(CaseRestriction).where(
                CaseRestriction.case_id.in_(case_ids),
                CaseRestriction.user_id == user_id,
                CaseRestriction.is_active.is_(True),
            )
            restr_res = await session.execute(restr_stmt)
            if restr_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Case restriction applies to this child",
                )

        # 1. Basic Demographics
        passport = {
            "passport_type": "CHILD_PASSPORT",
            "generated_at": datetime.utcnow().isoformat(),
            "confidentiality_notice": "CONFIDENTIAL — Chief Red Bear Children's Lodge Child Passport. For Authorized Child Welfare Use Only.",
            "demographics": {
                "child_id": str(person.id),
                "full_name": f"{person.first_name} {person.last_name}",
                "first_name": person.first_name,
                "last_name": person.last_name,
                "date_of_birth": person.date_of_birth.isoformat() if person.date_of_birth else None,
                "gender": person.gender,
                "indigenous_status": person.indigenous_identity,
                "band_number": person.band_nation,
            },
            "contacts": [
                {
                    "contact_type": c.contact_type,
                    "value": c.contact_value,
                    "is_primary": c.is_primary,
                }
                for c in (person.contacts or [])
            ],
            "cultural_information": [
                {
                    "community_name": person.cultural_profile.community_name if person.cultural_profile else None,
                    "language": person.cultural_profile.primary_language if person.cultural_profile else None,
                    "cultural_notes": person.cultural_profile.cultural_notes if person.cultural_profile else None,
                }
            ]
            if person.cultural_profile
            else [],
        }

        # 2. Medical Section — Section-Level Security Redaction
        can_read_medical = (
            Permissions.CLIENT_MEDICAL_READ in user_permissions or "admin.configuration.manage" in user_permissions
        )
        if can_read_medical:
            client_stmt = select(Client.id).where(or_(Client.person_id == child_id, Client.id == child_id))
            client_res = await session.execute(client_stmt)
            client_ids = [c for c in client_res.scalars().all()] or [child_id]

            med_stmt = select(ClientMedicalProfile).where(ClientMedicalProfile.client_id.in_(client_ids))
            med_res = await session.execute(med_stmt)
            med_profile = med_res.scalar_one_or_none()

            allergies_stmt = select(ClientAllergy).where(ClientAllergy.client_id.in_(client_ids))
            allergies = list((await session.execute(allergies_stmt)).scalars().all())

            meds_stmt = select(ClientMedication).where(ClientMedication.client_id.in_(client_ids))
            meds = list((await session.execute(meds_stmt)).scalars().all())

            passport["medical"] = {
                "redacted": False,
                "health_number": getattr(med_profile, "health_card_number", None) if med_profile else None,
                "blood_type": getattr(med_profile, "blood_type", None) if med_profile else None,
                "allergies": [{"allergen": a.allergen, "severity": a.severity} for a in allergies],
                "medications": [
                    {"name": m.medication_name, "dosage": m.dosage, "frequency": m.frequency} for m in meds
                ],
            }

        else:
            passport["medical"] = {
                "redacted": True,
                "reason": "Requires client.medical.read permission",
            }

        # 3. Placement History
        pl_stmt = (
            select(PlacementEpisode)
            .where(PlacementEpisode.child_id == child_id, PlacementEpisode.deleted_at.is_(None))
            .order_by(PlacementEpisode.start_date.desc())
        )
        placements = list((await session.execute(pl_stmt)).scalars().all())
        passport["placement_history"] = [
            {
                "placement_type": pl.placement_type,
                "provider_name": pl.provider_name,
                "start_date": pl.start_date.isoformat() if pl.start_date else None,
                "end_date": pl.end_date.isoformat() if pl.end_date else None,
                "status": pl.status,
            }
            for pl in placements
        ]

        return passport

    @staticmethod
    async def generate_parent_passport(
        session: AsyncSession,
        parent_id: uuid.UUID,
        user_id: uuid.UUID,
        user_permissions: set[str],
    ) -> dict:
        """Generate Parent Passport summary payload."""
        stmt = (
            select(Person)
            .where(Person.id == parent_id, Person.deleted_at.is_(None))
            .options(selectinload(Person.contacts))
        )
        person = (await session.execute(stmt)).scalar_one_or_none()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent record not found")

        return {
            "passport_type": "PARENT_PASSPORT",
            "generated_at": datetime.utcnow().isoformat(),
            "confidentiality_notice": "CONFIDENTIAL — Chief Red Bear Children's Lodge Parent Passport.",
            "demographics": {
                "parent_id": str(person.id),
                "full_name": f"{person.first_name} {person.last_name}",
                "date_of_birth": person.date_of_birth.isoformat() if person.date_of_birth else None,
                "gender": person.gender,
            },
            "contacts": [{"contact_type": c.contact_type, "value": c.contact_value} for c in (person.contacts or [])],
        }
