"""Resource Unit Canned Reports and Analytics Service (Sprint 3).

Provides pre-built canned reports for:
- Resource Home Directory
- Available Capacity
- Recruitment Pipeline & Conversion
- Expiring Compliance (Clearances & Screenings)
- Caregiver Training Compliance
- Licensing & Renewal
- Resource Home Monitoring
- Complaints & Investigations (field-level privacy redaction)
- Caregiver Supports
- Placement Stability
- Resource Growth & Retention
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.caregiver_support import CaregiverSupport
from app.models.caregiver_training import CaregiverTraining
from app.models.placement import BackgroundCheck, PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.resource_complaint import ResourceComplaint
from app.models.resource_monitoring import ResourceHomeMonitoring
from app.models.resource_recruitment import ResourceRecruitment


class ResourceReportsService:
    """Service providing canned reports for the Resource Unit."""

    @classmethod
    async def run_home_directory_report(
        cls, session: AsyncSession, can_read_contact: bool = False
    ) -> dict[str, Any]:
        """Directory of all registered placement homes, licensing status, and contacts."""
        stmt = (
            select(PlacementHome)
            .where(PlacementHome.deleted_at.is_(None))
            .order_by(PlacementHome.home_code)
        )
        homes = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(h.id),
                "home_code": h.home_code,
                "name": h.name,
                "home_type": h.home_type,
                "status": h.status,
                "licensing_status": h.licensing_status,
                "total_capacity": h.total_capacity,
                "primary_caregiver_name": h.primary_caregiver_name,
                "city": h.city,
                "community": h.community,
                "phone": h.phone if can_read_contact else None,
                "email": h.email if can_read_contact else None,
            }
            for h in homes
        ]
        return {
            "report_name": "Resource Home Directory",
            "generated_at": datetime.utcnow().isoformat(),
            "contact_details_unmasked": can_read_contact,
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_available_capacity_report(cls, session: AsyncSession) -> dict[str, Any]:
        """Available capacity by home type and community."""
        stmt = (
            select(PlacementHome)
            .where(
                PlacementHome.status == "ACTIVE",
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
            )
            .order_by(PlacementHome.city, PlacementHome.name)
        )
        homes = list((await session.execute(stmt)).scalars().all())

        items = []
        total_capacity = 0
        total_occupied = 0
        total_available = 0

        for h in homes:
            occ_stmt = select(func.count(PlacementEpisode.id)).where(
                PlacementEpisode.placement_home_id == h.id,
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
            )
            occupied = int((await session.execute(occ_stmt)).scalar() or 0)
            available = max(0, h.total_capacity - occupied)

            total_capacity += h.total_capacity
            total_occupied += occupied
            total_available += available

            items.append({
                "home_id": str(h.id),
                "home_code": h.home_code,
                "name": h.name,
                "home_type": h.home_type,
                "city": h.city,
                "community": h.community,
                "total_capacity": h.total_capacity,
                "occupied_beds": occupied,
                "available_beds": available,
            })

        return {
            "report_name": "Available Resource Capacity",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_homes": len(homes),
                "total_capacity": total_capacity,
                "total_occupied": total_occupied,
                "total_available": total_available,
            },
            "items": items,
        }

    @classmethod
    async def run_recruitment_conversion_report(cls, session: AsyncSession) -> dict[str, Any]:
        """Recruitment pipeline stages and conversion rate."""
        stmt = select(ResourceRecruitment).where(ResourceRecruitment.deleted_at.is_(None))
        apps = list((await session.execute(stmt)).scalars().all())

        stage_counts: dict[str, int] = {}
        for app in apps:
            stage_counts[app.current_state] = stage_counts.get(app.current_state, 0) + 1

        total = len(apps)
        approved = stage_counts.get("APPROVED", 0)
        conversion_rate = round(approved / total * 100.0, 1) if total > 0 else 0.0

        return {
            "report_name": "Recruitment Pipeline & Conversion",
            "generated_at": datetime.utcnow().isoformat(),
            "total_applications": total,
            "approved_applications": approved,
            "conversion_rate_pct": conversion_rate,
            "stage_breakdown": stage_counts,
        }

    @classmethod
    async def run_compliance_expiring_report(
        cls, session: AsyncSession, days_ahead: int = 30
    ) -> dict[str, Any]:
        """Clearances and screenings expiring in the next N days or already expired."""
        today = date.today()
        threshold = today + timedelta(days=days_ahead)

        stmt = (
            select(BackgroundCheck)
            .where(
                BackgroundCheck.placement_home_id.isnot(None),
                BackgroundCheck.deleted_at.is_(None),
                (
                    (BackgroundCheck.renewal_status == "EXPIRED")
                    | (BackgroundCheck.expiry_date.isnot(None) & (BackgroundCheck.expiry_date <= threshold))
                ),
            )
            .options(selectinload(BackgroundCheck.placement_home))
            .order_by(BackgroundCheck.expiry_date)
        )
        checks = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(chk.id),
                "home_id": str(chk.placement_home_id),
                "home_name": chk.placement_home.name if chk.placement_home else None,
                "home_code": chk.placement_home.home_code if chk.placement_home else None,
                "subject_name": chk.subject_name,
                "check_type": chk.check_type,
                "expiry_date": str(chk.expiry_date) if chk.expiry_date else None,
                "status": "EXPIRED" if (chk.expiry_date and chk.expiry_date < today) or chk.renewal_status == "EXPIRED" else "EXPIRING_SOON",
            }
            for chk in checks
        ]
        return {
            "report_name": f"Expiring & Expired Compliance Screenings ({days_ahead} Days)",
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_caregiver_training_report(cls, session: AsyncSession) -> dict[str, Any]:
        """Caregiver training completions, due certifications, and expiry status."""
        stmt = (
            select(CaregiverTraining)
            .where(CaregiverTraining.deleted_at.is_(None))
            .options(
                selectinload(CaregiverTraining.placement_home),
                selectinload(CaregiverTraining.caregiver),
            )
            .order_by(desc(CaregiverTraining.completion_date))
        )
        trainings = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(t.id),
                "home_name": t.placement_home.name if t.placement_home else None,
                "caregiver_name": f"{t.caregiver.first_name} {t.caregiver.last_name}".strip() if t.caregiver else None,
                "training_name": t.training_name,
                "training_type": t.training_type,
                "completion_date": str(t.completion_date) if t.completion_date else None,
                "expiry_date": str(t.expiry_date) if t.expiry_date else None,
                "status": t.status,
                "hours_completed": float(t.hours_completed),
            }
            for t in trainings
        ]
        return {
            "report_name": "Caregiver Training Compliance",
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_licensing_renewal_report(
        cls, session: AsyncSession, days_ahead: int = 90
    ) -> dict[str, Any]:
        """Licenses nearing expiration or renewal within N days."""
        today = date.today()
        threshold = today + timedelta(days=days_ahead)

        stmt = (
            select(PlacementHomeLicense)
            .where(
                PlacementHomeLicense.deleted_at.is_(None),
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.expiry_date <= threshold,
            )
            .options(selectinload(PlacementHomeLicense.placement_home))
            .order_by(PlacementHomeLicense.expiry_date)
        )
        licenses = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(lic.id),
                "home_id": str(lic.placement_home_id),
                "home_name": lic.placement_home.name if lic.placement_home else None,
                "home_code": lic.placement_home.home_code if lic.placement_home else None,
                "license_number": lic.license_number,
                "license_type": lic.license_type,
                "expiry_date": str(lic.expiry_date),
                "days_remaining": (lic.expiry_date - today).days,
                "max_capacity": lic.max_capacity,
            }
            for lic in licenses
        ]
        return {
            "report_name": f"Licensing Expirations & Renewals ({days_ahead} Days)",
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_home_monitoring_report(cls, session: AsyncSession) -> dict[str, Any]:
        """Ongoing monitoring visits log and follow-up requirements."""
        stmt = (
            select(ResourceHomeMonitoring)
            .where(ResourceHomeMonitoring.deleted_at.is_(None))
            .options(
                selectinload(ResourceHomeMonitoring.placement_home),
                selectinload(ResourceHomeMonitoring.worker),
            )
            .order_by(desc(ResourceHomeMonitoring.contact_date))
        )
        visits = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(v.id),
                "home_name": v.placement_home.name if v.placement_home else None,
                "home_code": v.placement_home.home_code if v.placement_home else None,
                "worker_name": (v.worker.full_name or v.worker.email) if v.worker else None,
                "contact_date": str(v.contact_date),
                "contact_type": v.contact_type,
                "child_interview_completed": v.child_interview_completed,
                "caregiver_interview_completed": v.caregiver_interview_completed,
                "safety_review_completed": v.safety_review_completed,
                "follow_up_required": v.follow_up_required,
                "next_review_date": str(v.next_review_date) if v.next_review_date else None,
                "status": v.status,
            }
            for v in visits
        ]
        return {
            "report_name": "Resource Home Ongoing Monitoring",
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_complaints_report(
        cls, session: AsyncSession, can_read_sensitive: bool = False
    ) -> dict[str, Any]:
        """Complaints and investigations with strict field-level privacy redaction."""
        stmt = (
            select(ResourceComplaint)
            .where(ResourceComplaint.deleted_at.is_(None))
            .options(selectinload(ResourceComplaint.placement_home))
            .order_by(desc(ResourceComplaint.received_date))
        )
        complaints = list((await session.execute(stmt)).scalars().all())

        items = []
        for c in complaints:
            item: dict[str, Any] = {
                "id": str(c.id),
                "complaint_number": c.complaint_number,
                "home_name": c.placement_home.name if c.placement_home else None,
                "home_code": c.placement_home.home_code if c.placement_home else None,
                "complainant_category": c.complainant_category,
                "received_date": str(c.received_date),
                "complaint_type": c.complaint_type,
                "severity": c.severity,
                "status": c.status,
                "disposition": c.disposition,
                "closure_date": str(c.closure_date) if c.closure_date else None,
            }
            # Only disclose sensitive details if authorized
            if can_read_sensitive:
                item["complainant_name"] = c.complainant_name
                item["complainant_contact"] = c.complainant_contact
                item["allegation_summary"] = c.allegation_summary
                item["findings"] = c.findings
                item["findings_finalized"] = c.findings_finalized
                item["recommendations"] = c.recommendations
                item["corrective_actions"] = c.corrective_actions
            items.append(item)

        return {
            "report_name": "Resource Complaints & Investigations",
            "generated_at": datetime.utcnow().isoformat(),
            "is_sensitive_unmasked": can_read_sensitive,
            "total_count": len(items),
            "items": items,
        }

    @classmethod
    async def run_caregiver_supports_report(
        cls, session: AsyncSession, can_read_financial: bool = False
    ) -> dict[str, Any]:
        """Caregiver supports provided and financial linkages."""
        stmt = (
            select(CaregiverSupport)
            .where(CaregiverSupport.deleted_at.is_(None))
            .options(
                selectinload(CaregiverSupport.placement_home),
                selectinload(CaregiverSupport.caregiver),
            )
            .order_by(desc(CaregiverSupport.requested_date))
        )
        supports = list((await session.execute(stmt)).scalars().all())

        items = [
            {
                "id": str(s.id),
                "support_number": s.support_number,
                "home_name": s.placement_home.name if s.placement_home else None,
                "home_code": s.placement_home.home_code if s.placement_home else None,
                "caregiver_name": f"{s.caregiver.first_name} {s.caregiver.last_name}".strip() if s.caregiver else None,
                "support_type": s.support_type,
                "title": s.title,
                "requested_date": str(s.requested_date),
                "provided_date": str(s.provided_date) if s.provided_date else None,
                "status": s.status,
                "amount": (float(s.amount) if s.amount else None) if can_read_financial else None,
                "has_financial_link": s.service_request_id is not None,
            }
            for s in supports
        ]
        return {
            "report_name": "Caregiver Supports & Assistance",
            "generated_at": datetime.utcnow().isoformat(),
            "financial_amounts_unmasked": can_read_financial,
            "total_count": len(items),
            "items": items,
        }
