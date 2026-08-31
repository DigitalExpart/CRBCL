"""Genogram graph building service for interactive family tree visualization."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.person import Person
from app.models.relationship import FamilyMember, FamilyRelationship, HouseholdMembership


class GenogramService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_family_genogram(self, family_id: uuid.UUID) -> dict:
        """
        Builds React Flow / Genogram node & edge representation for a family.
        """
        # 1. Fetch Family Members
        members_res = await self.db.execute(
            select(FamilyMember)
            .where(FamilyMember.family_id == family_id, FamilyMember.is_active == True)  # noqa: E712
            .options(selectinload(FamilyMember.person))
        )
        members = list(members_res.scalars().all())

        # Collect person IDs
        person_ids = {m.person_id for m in members if m.person}

        # 2. Fetch Relationships within or connected to this family
        relationships_res = await self.db.execute(
            select(FamilyRelationship)
            .where(
                (FamilyRelationship.family_id == family_id) |
                (FamilyRelationship.person_a_id.in_(person_ids)) |
                (FamilyRelationship.person_b_id.in_(person_ids)),
                FamilyRelationship.is_active == True,  # noqa: E712
            )
            .options(
                selectinload(FamilyRelationship.person_a),
                selectinload(FamilyRelationship.person_b),
            )
        )
        relationships = list(relationships_res.scalars().all())

        # Also include any connected persons who might not be direct family members
        for r in relationships:
            if r.person_a_id:
                person_ids.add(r.person_a_id)
            if r.person_b_id:
                person_ids.add(r.person_b_id)

        # 3. Load all unique persons
        persons_res = await self.db.execute(
            select(Person).where(Person.id.in_(person_ids), Person.deleted_at.is_(None))
        )
        persons = {p.id: p for p in persons_res.scalars().all()}

        # 4. Fetch Household Memberships for these persons
        households_res = await self.db.execute(
            select(HouseholdMembership)
            .where(HouseholdMembership.person_id.in_(person_ids), HouseholdMembership.is_current == True)  # noqa: E712
            .options(selectinload(HouseholdMembership.household))
        )
        household_memberships = list(households_res.scalars().all())
        person_households = {}
        household_details = {}
        for hm in household_memberships:
            person_households[str(hm.person_id)] = str(hm.household_id)
            if hm.household:
                household_details[str(hm.household_id)] = {
                    "id": str(hm.household.id),
                    "name": hm.household.name,
                    "address": hm.household.address_line_1,
                    "city": hm.household.city,
                    "latitude": hm.household.latitude,
                    "longitude": hm.household.longitude,
                }

        # 5. Build Genogram Nodes
        nodes = []
        for p_id, p in persons.items():
            member_role = next((m.role for m in members if m.person_id == p_id), "Relative / Contact")
            nodes.append({
                "id": str(p.id),
                "type": "personNode",
                "data": {
                    "personId": str(p.id),
                    "fullName": f"{p.first_name} {p.last_name}",
                    "preferredName": p.preferred_name,
                    "gender": p.gender or "Unknown",
                    "dateOfBirth": str(p.date_of_birth) if p.date_of_birth else None,
                    "role": member_role,
                    "householdId": person_households.get(str(p.id)),
                    "photoUrl": p.photo_url,
                },
            })

        # 6. Build Genogram Edges
        edges = []
        for r in relationships:
            edges.append({
                "id": f"rel-{r.id}",
                "source": str(r.person_a_id),
                "target": str(r.person_b_id),
                "type": "smoothstep",
                "label": r.relationship_type.replace("_", " ").title(),
                "data": {
                    "relationshipType": r.relationship_type,
                    "notes": r.notes,
                },
            })

        return {
            "familyId": str(family_id),
            "nodes": nodes,
            "edges": edges,
            "households": list(household_details.values()),
        }
