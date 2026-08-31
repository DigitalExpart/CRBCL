"""Medical profiles, allergies, conditions, and medication repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical import (
    ClientAllergy,
    ClientMedicalCondition,
    ClientMedicalProfile,
    ClientMedication,
)


class MedicalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, client_id: uuid.UUID) -> ClientMedicalProfile:
        query = select(ClientMedicalProfile).where(ClientMedicalProfile.client_id == client_id)
        result = await self.db.execute(query)
        profile = result.scalar_one_or_none()
        if not profile:
            profile = ClientMedicalProfile(client_id=client_id)
            self.db.add(profile)
            await self.db.flush()
        return profile

    async def update_profile(self, client_id: uuid.UUID, **data) -> ClientMedicalProfile:
        profile = await self.get_or_create_profile(client_id)
        for k, v in data.items():
            if hasattr(profile, k) and v is not None:
                setattr(profile, k, v)
        await self.db.flush()
        return profile

    # Allergies
    async def list_allergies(self, client_id: uuid.UUID, active_only: bool = True) -> list[ClientAllergy]:
        query = select(ClientAllergy).where(ClientAllergy.client_id == client_id)
        if active_only:
            query = query.where(ClientAllergy.is_active == True)  # noqa: E712
        result = await self.db.execute(query.order_by(ClientAllergy.created_at.desc()))
        return list(result.scalars().all())

    async def add_allergy(self, client_id: uuid.UUID, **data) -> ClientAllergy:
        allergy = ClientAllergy(client_id=client_id, **data)
        self.db.add(allergy)
        await self.db.flush()
        return allergy

    # Conditions
    async def list_conditions(self, client_id: uuid.UUID, active_only: bool = False) -> list[ClientMedicalCondition]:
        query = select(ClientMedicalCondition).where(ClientMedicalCondition.client_id == client_id)
        if active_only:
            query = query.where(ClientMedicalCondition.is_active == True)  # noqa: E712
        result = await self.db.execute(query.order_by(ClientMedicalCondition.created_at.desc()))
        return list(result.scalars().all())

    async def add_condition(self, client_id: uuid.UUID, **data) -> ClientMedicalCondition:
        cond = ClientMedicalCondition(client_id=client_id, **data)
        self.db.add(cond)
        await self.db.flush()
        return cond

    # Medications
    async def list_medications(self, client_id: uuid.UUID, status: str | None = None) -> list[ClientMedication]:
        query = select(ClientMedication).where(ClientMedication.client_id == client_id)
        if status:
            query = query.where(ClientMedication.status == status)
        result = await self.db.execute(query.order_by(ClientMedication.created_at.desc()))
        return list(result.scalars().all())

    async def add_medication(self, client_id: uuid.UUID, **data) -> ClientMedication:
        med = ClientMedication(client_id=client_id, **data)
        self.db.add(med)
        await self.db.flush()
        return med

    async def update_medication_status(
        self, medication_id: uuid.UUID, status: str, notes: str | None = None
    ) -> ClientMedication | None:
        query = select(ClientMedication).where(ClientMedication.id == medication_id)
        result = await self.db.execute(query)
        med = result.scalar_one_or_none()
        if med:
            med.status = status
            if notes:
                med.notes = (med.notes or "") + f"\n[Status Change to {status}]: {notes}"
            await self.db.flush()
        return med
