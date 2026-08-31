"""Referral history service discovering prior intakes and cases for involved persons."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.client import Client
from app.models.referral import Referral, ReferralPerson


class ReferralHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_prior_history_for_referral(
        self,
        referral_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> dict:
        """Discover authorized prior cases and prior intakes for all people on a referral."""
        # 1. Fetch people on current referral
        people_stmt = (
            select(ReferralPerson)
            .options(selectinload(ReferralPerson.person))
            .where(ReferralPerson.referral_id == referral_id)
        )
        people_res = await self.db.execute(people_stmt)
        referral_people = list(people_res.scalars().all())

        person_ids = [rp.person_id for rp in referral_people]
        person_names = {rp.person_id: f"{rp.person.first_name} {rp.person.last_name}" if rp.person else "Unknown" for rp in referral_people}

        if not person_ids:
            return {"prior_referrals": [], "prior_cases": []}

        # 2. Find prior referrals involving these persons (excluding the current referral)
        prior_ref_stmt = (
            select(ReferralPerson)
            .options(
                selectinload(ReferralPerson.referral).selectinload(Referral.concerns),
                selectinload(ReferralPerson.person),
            )
            .join(Referral, Referral.id == ReferralPerson.referral_id)
            .where(
                ReferralPerson.person_id.in_(person_ids),
                ReferralPerson.referral_id != referral_id,
                Referral.deleted_at.is_(None),
            )
            .order_by(Referral.received_date.desc())
        )
        prior_ref_res = await self.db.execute(prior_ref_stmt)
        prior_ref_rows = list(prior_ref_res.scalars().all())

        prior_referrals_map = {}
        for row in prior_ref_rows:
            ref = row.referral
            if not ref:
                continue
            if ref.id not in prior_referrals_map:
                primary_concern = next((c.concern_type for c in ref.concerns if c.is_primary), None)
                if not primary_concern and ref.concerns:
                    primary_concern = ref.concerns[0].concern_type

                prior_referrals_map[ref.id] = {
                    "referral_id": str(ref.id),
                    "referral_number": ref.referral_number,
                    "status": ref.status,
                    "received_date": str(ref.received_date),
                    "community": ref.community,
                    "primary_concern": primary_concern,
                    "summary": ref.summary,
                    "involved_person_ids": [str(row.person_id)],
                    "involved_person_names": [person_names.get(row.person_id, "")],
                }
            else:
                p_id_str = str(row.person_id)
                if p_id_str not in prior_referrals_map[ref.id]["involved_person_ids"]:
                    prior_referrals_map[ref.id]["involved_person_ids"].append(p_id_str)
                    prior_referrals_map[ref.id]["involved_person_names"].append(person_names.get(row.person_id, ""))

        # 3. Find prior cases where person is client or linked via person names
        first_names = [rp.person.first_name for rp in referral_people if rp.person]
        last_names = [rp.person.last_name for rp in referral_people if rp.person]

        prior_cases = []
        if first_names and last_names:
            client_stmt = select(Client).where(
                Client.first_name.in_(first_names),
                Client.last_name.in_(last_names),
                Client.deleted_at.is_(None),
            )
            client_res = await self.db.execute(client_stmt)
            clients = list(client_res.scalars().all())
            client_ids = [c.id for c in clients]

            if client_ids:
                case_stmt = (
                    select(Case)
                    .where(Case.client_id.in_(client_ids), Case.deleted_at.is_(None))
                    .order_by(Case.created_at.desc())
                )
                case_res = await self.db.execute(case_stmt)
                cases = list(case_res.scalars().all())

                for cs in cases:
                    prior_cases.append({
                        "case_id": str(cs.id),
                        "case_number": cs.case_number,
                        "title": cs.title,
                        "case_type": cs.case_type,
                        "status": cs.status,
                        "priority": cs.priority,
                        "intake_date": str(cs.intake_date) if cs.intake_date else None,
                        "client_id": str(cs.client_id) if cs.client_id else None,
                    })

        return {
            "prior_referrals": list(prior_referrals_map.values()),
            "prior_cases": prior_cases,
        }
