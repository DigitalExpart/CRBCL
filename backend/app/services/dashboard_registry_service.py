"""Canonical Dashboard Registry and Control Service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.config import SystemConfig
from app.models.role import Permission, Role, RolePermission, UserRole
from app.permissions.constants import Permissions
from app.schemas.dashboard_control import DashboardRegistryItem

CANONICAL_WORKSPACES: list[dict[str, Any]] = [
    {
        "key": "staff_dashboard",
        "name": "Staff Dashboard",
        "category": "General Operations",
        "route": "/",
        "workspace_type": "dashboard",
        "primary_permission_key": None,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Universal staff workspace for personalized announcements, schedule, and assigned tasks.",
    },
    {
        "key": "admin_portal",
        "name": "Admin & IT Portal",
        "category": "Administration & IT",
        "route": "/admin",
        "workspace_type": "administrative",
        "primary_permission_key": Permissions.ADMIN_CONFIGURATION_MANAGE,
        "security_classification": "ADMINISTRATIVE",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Master administration portal for user directory, RBAC governance, and platform configuration.",
    },
    {
        "key": "front_desk",
        "name": "Front Desk / First Impression",
        "category": "Intake & Reception",
        "route": "/front-desk",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.PUBLIC_INTAKE_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Public community inquiries, Google Form ingestion triage, caller registration, and departmental referral drafting.",
    },
    {
        "key": "office_coordinator",
        "name": "Office Coordinator Workspace",
        "category": "Operations & Facilities",
        "route": "/office-coordinator",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Centralized operational request queue, advance vehicle reservations, key custody tracking, room scheduling, and supply inventory.",
    },
    {
        "key": "navigator",
        "name": "Navigator / System Navigation",
        "category": "Intake & Navigation",
        "route": "/navigator",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.NAVIGATOR_DASHBOARD_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "System navigation support, community referral coordination, and intake reception.",
    },
    {
        "key": "intake_referrals",
        "name": "Intake & Referrals",
        "category": "Intake & Referrals",
        "route": "/intake",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.INTAKE_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Formal child welfare intake investigations, referral screening, and intake safety determinations.",
    },
    {
        "key": "approvals_queue",
        "name": "Intake & Client Approvals",
        "category": "Intake & Referrals",
        "route": "/intake/approvals",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.INTAKE_APPROVE,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Supervisory approval queue for proposed clients and intake disposition determinations.",
    },
    {
        "key": "case_management",
        "name": "Case Management",
        "category": "Case & Client",
        "route": "/cases",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.CASE_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Active child welfare and family wellness case files, clinical case notes, and safety plans.",
    },
    {
        "key": "clients_registry",
        "name": "Clients & Longitudinal Profiles",
        "category": "Case & Client",
        "route": "/clients",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.CLIENT_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Canonical Person identities and active service enrollment profiles across all child welfare contexts.",
    },
    {
        "key": "families_registry",
        "name": "Families Registry",
        "category": "Case & Client",
        "route": "/families",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.FAMILY_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Kinship genealogies, household compositions, and extended family connection mapping.",
    },
    {
        "key": "resource_team",
        "name": "Resource Team & Licensing",
        "category": "Resource & Placements",
        "route": "/resource-team",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.RESOURCE_DASHBOARD_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Customary care licensing, kinship & foster caregiver recruitment pipeline, and placement capacity oversight.",
    },
    {
        "key": "placement_homes",
        "name": "Placement Homes & Capacity",
        "category": "Resource & Placements",
        "route": "/placement-homes",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.PLACEMENT_HOME_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Bed availability, background checks, annual license renewals, and home visit logs.",
    },
    {
        "key": "recruitment_pipeline",
        "name": "Caregiver Recruitment Pipeline",
        "category": "Resource & Placements",
        "route": "/resource-team/recruitment",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.RESOURCE_RECRUITMENT_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Prospective caregiver application tracking from initial inquiry through homestudy and approval.",
    },
    {
        "key": "placement_matching",
        "name": "Placement Matching Decision-Support",
        "category": "Resource & Placements",
        "route": "/placement-matching",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.RESOURCE_MATCHING_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Explainable matching decision support based on cultural affinity, sibling preservation, and proximity.",
    },
    {
        "key": "finance_billing",
        "name": "Finance, Billing & Procurement",
        "category": "Finance & Administration",
        "route": "/finance",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.FINANCE_REQUEST_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Purchase orders, per diem invoices, maintenance rate cards, and financial ledger audit tracking.",
    },
    {
        "key": "hr_dashboard",
        "name": "Human Resources Dashboard",
        "category": "Human Resources",
        "route": "/hr",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.HR_DASHBOARD_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Employee personnel directory, professional licenses, CPR/First Aid certifications, and staffing oversight.",
    },
    {
        "key": "fleet_management",
        "name": "Fleet & Vehicles",
        "category": "Operations & Facilities",
        "route": "/fleet",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.FLEET_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Vehicle asset registry, trip checkouts, scheduled maintenance, and insurance policies.",
    },
    {
        "key": "facilities_management",
        "name": "Facilities & Buildings",
        "category": "Operations & Facilities",
        "route": "/facilities",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.FACILITIES_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "CRBCL buildings, offices, program sites, fire safety inspections, and maintenance work orders.",
    },
    {
        "key": "housing_units",
        "name": "Housing Units & Shelters",
        "category": "Operations & Facilities",
        "route": "/housing",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.HOUSING_UNIT_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Emergency shelter beds, supportive transitional housing units, and occupancy management.",
    },
    {
        "key": "it_assets",
        "name": "IT Assets & Hardware Inventory",
        "category": "IT & Systems",
        "route": "/assets",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.ASSET_ITEM_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Hardware asset tags, laptop & mobile deployments, serial tracking, and warranty schedules.",
    },
    {
        "key": "ceo_command_centre",
        "name": "CEO Command Centre",
        "category": "Executive Leadership",
        "route": "/ceo",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.EXECUTIVE_DASHBOARD_READ,
        "security_classification": "GOVERNANCE_IN_CAMERA",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Strategic initiative milestones, capital allocation tracking, and executive leadership indicators.",
    },
    {
        "key": "executive_dashboard",
        "name": "Executive Director Dashboard",
        "category": "Executive Leadership",
        "route": "/executive",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.EXECUTIVE_DASHBOARD_READ,
        "security_classification": "GOVERNANCE_IN_CAMERA",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Cross-agency operations, service trends, caseload escalations, and executive governance oversight.",
    },
    {
        "key": "directors_dashboard",
        "name": "Director / Manager Dashboard",
        "category": "Executive Leadership",
        "route": "/director",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.EXECUTIVE_DASHBOARD_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Program-level metrics, operational workflow escalations, and supervisory reviews.",
    },
    {
        "key": "board_governance",
        "name": "Board Governance Portal",
        "category": "Board of Governors",
        "route": "/board",
        "workspace_type": "dashboard",
        "primary_permission_key": Permissions.BOARD_DASHBOARD_READ,
        "security_classification": "GOVERNANCE_IN_CAMERA",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Board of Governors governance portal, formal decision records, and in-camera publication controls.",
    },
    {
        "key": "team_dashboards",
        "name": "Team Dashboards Hub",
        "category": "Programs & Operations",
        "route": "/teams",
        "workspace_type": "workspace",
        "primary_permission_key": None,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Program team cards and departmental operational focus views.",
    },
    {
        "key": "scheduling_calendar",
        "name": "My Schedule & Team Calendar",
        "category": "General Operations",
        "route": "/schedule",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.CALENDAR_READ_OWN,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Personal casework schedule, team shifts, and community appointment calendars.",
    },
    {
        "key": "staffing_facilitator",
        "name": "Staffing Facilitator",
        "category": "Case & Operations",
        "route": "/staffing",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.STAFFING_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Multi-disciplinary team staffing conferences, case plan reviews, and clinical action items.",
    },
    {
        "key": "reporting_qa",
        "name": "Reporting Hub & QA Audits",
        "category": "Quality & Reporting",
        "route": "/reports",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.REPORT_READ,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Ad-hoc reporting, statutory filings, child/parent passports, and QA practice audit checklists.",
    },
    {
        "key": "clinical_notes",
        "name": "Clinical & Health Notes",
        "category": "Clinical & Health",
        "route": "/clinical-notes",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.CLINICAL_NOTE_READ,
        "security_classification": "RESTRICTED_HEALTH",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Practitioner clinical progress notes, therapeutic interventions, and psychiatric addenda.",
    },
    {
        "key": "incidents_log",
        "name": "Critical Incidents Log",
        "category": "Programs & Safety",
        "route": "/incidents",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.INCIDENT_MANAGE,
        "security_classification": "CONFIDENTIAL_OPERATIONAL",
        "has_protected_data": True,
        "status": "IMPLEMENTED",
        "description": "Safety incident recording, supervisor reviews, and critical event tracking.",
    },
    {
        "key": "volunteers_registry",
        "name": "Volunteers & Community Hours",
        "category": "Community & Volunteers",
        "route": "/volunteers",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.VOLUNTEER_RECORD_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Community volunteer onboarding, hours logging, and event assignments.",
    },
    {
        "key": "donations_funding",
        "name": "Donations & Funding Grants",
        "category": "Finance & Administration",
        "route": "/donations",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.DONATION_DONOR_READ,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Community donations, in-kind contributions, and external funding grant tracking.",
    },
    {
        "key": "communications_hub",
        "name": "Communications & Media",
        "category": "Communications",
        "route": "/communications",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.COMMUNICATIONS_MANAGE,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Community press releases, internal announcements, and media approvals.",
    },
    {
        "key": "ask_red_bear",
        "name": "Ask Red Bear AI Assistant",
        "category": "General Operations",
        "route": "/ask-red-bear",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.AI_QUERY,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Assistive AI assistant querying policy documents and cultural guidelines with strict privilege boundaries.",
    },
    {
        "key": "cultural_terminology",
        "name": "Cultural Terminology & Sacred Lexicon",
        "category": "Culture & Traditional",
        "route": "/terminology",
        "workspace_type": "workspace",
        "primary_permission_key": Permissions.TERMINOLOGY_MANAGE,
        "security_classification": "INTERNAL_OPERATIONS",
        "has_protected_data": False,
        "status": "IMPLEMENTED",
        "description": "Cree & Saulteaux indigenous terminology repository and culturally resonant definitions.",
    },
]


class DashboardRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_workspaces(self) -> list[DashboardRegistryItem]:
        """Load complete canonical workspace registry with live availability and authorized roles."""
        # 1. Load system config for all dashboard enable/disable keys
        config_res = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key.like("dashboard.%.enabled"))
        )
        configs = {cfg.key: cfg.value.lower() == "true" for cfg in config_res.scalars().all()}

        # 2. Load role permissions for all primary permissions
        perm_keys = [w["primary_permission_key"] for w in CANONICAL_WORKSPACES if w["primary_permission_key"]]
        role_perm_stmt = (
            select(Permission.key, Role.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .where(
                Permission.key.in_(perm_keys),
                Role.is_active.is_(True),
                Permission.is_active.is_(True),
            )
        )
        role_perm_res = await self.db.execute(role_perm_stmt)
        perm_to_roles: dict[str, set[str]] = {}
        for p_key, r_key in role_perm_res.all():
            perm_to_roles.setdefault(p_key, set()).add(r_key)

        # 3. Load active user counts per role
        user_role_stmt = (
            select(Role.key, func.count(UserRole.user_id.distinct()))
            .join(UserRole, UserRole.role_id == Role.id)
            .where(Role.is_active.is_(True))
            .group_by(Role.key)
        )
        user_role_res = await self.db.execute(user_role_stmt)
        role_user_counts = dict(user_role_res.all())

        items: list[DashboardRegistryItem] = []
        for w in CANONICAL_WORKSPACES:
            cfg_key = f"dashboard.{w['key']}.enabled"
            is_enabled = configs.get(cfg_key, True)  # Enabled by default

            p_key = w["primary_permission_key"]
            roles_set = perm_to_roles.get(p_key, set()) if p_key else {"*"}
            roles_list = sorted(roles_set)

            # Calculate total unique users with access
            if p_key is None:
                # Universal workspace
                user_count_res = await self.db.execute(select(func.count(UserRole.user_id.distinct())))
                users_count = user_count_res.scalar_one() or 0
            else:
                users_count = sum(role_user_counts.get(r, 0) for r in roles_set)

            items.append(
                DashboardRegistryItem(
                    key=w["key"],
                    name=w["name"],
                    category=w["category"],
                    route=w["route"],
                    workspace_type=w["workspace_type"],
                    is_enabled=is_enabled,
                    primary_permission_key=w["primary_permission_key"],
                    security_classification=w["security_classification"],
                    has_protected_data=w["has_protected_data"],
                    status=w["status"],
                    description=w["description"],
                    authorized_roles=roles_list,
                    authorized_users_count=users_count,
                )
            )

        return items

    async def is_workspace_enabled(self, workspace_key: str) -> bool:
        """Check whether a workspace is organizationally available."""
        cfg_key = f"dashboard.{workspace_key}.enabled"
        res = await self.db.execute(select(SystemConfig).where(SystemConfig.key == cfg_key))
        cfg = res.scalar_one_or_none()
        if cfg:
            return cfg.value.lower() == "true"
        return True  # Enabled by default

    async def update_workspace_status(
        self,
        workspace_key: str,
        is_enabled: bool,
        actor_user_id: uuid.UUID,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> DashboardRegistryItem:
        """Toggle workspace organizational availability and audit the action."""
        workspace = next((w for w in CANONICAL_WORKSPACES if w["key"] == workspace_key), None)
        if not workspace:
            raise ValueError(f"Unknown workspace key: {workspace_key}")

        cfg_key = f"dashboard.{workspace_key}.enabled"
        res = await self.db.execute(select(SystemConfig).where(SystemConfig.key == cfg_key))
        cfg = res.scalar_one_or_none()
        old_val = cfg.value.lower() == "true" if cfg else True

        if cfg:
            cfg.value = "true" if is_enabled else "false"
            cfg.updated_by = actor_user_id
        else:
            cfg = SystemConfig(
                key=cfg_key,
                value="true" if is_enabled else "false",
                value_type="boolean",
                description=f"Organization-wide availability toggle for {workspace['name']}",
                is_sensitive=False,
                updated_by=actor_user_id,
            )
            self.db.add(cfg)

        # Audit event
        audit = AuditService(self.db)
        await audit.log_event(
            event_type="WORKSPACE_STATUS_TOGGLED",
            user_id=actor_user_id,
            entity_type="workspace",
            entity_id=None,
            before_data={"workspace_key": workspace_key, "is_enabled": old_val},
            after_data={"workspace_key": workspace_key, "is_enabled": is_enabled, "reason": reason},
            ip_address=ip_address,
        )
        await self.db.flush()

        all_items = await self.get_all_workspaces()
        return next(i for i in all_items if i.key == workspace_key)

    async def update_workspace_roles(
        self,
        workspace_key: str,
        role_keys: list[str],
        actor_user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> DashboardRegistryItem:
        """Update role assignments for a workspace capability and audit the changes."""
        workspace = next((w for w in CANONICAL_WORKSPACES if w["key"] == workspace_key), None)
        if not workspace:
            raise ValueError(f"Unknown workspace key: {workspace_key}")

        p_key = workspace["primary_permission_key"]
        if not p_key:
            raise ValueError(f"Workspace {workspace['name']} is universal and does not require role permission assignments.")

        perm_res = await self.db.execute(select(Permission).where(Permission.key == p_key))
        perm = perm_res.scalar_one_or_none()
        if not perm:
            raise ValueError(f"Permission {p_key} not found in database.")

        roles_res = await self.db.execute(select(Role).where(Role.is_active.is_(True)))
        all_roles = {r.key: r for r in roles_res.scalars().all()}

        # Load existing role permissions for this permission
        existing_rp_res = await self.db.execute(
            select(RolePermission).where(RolePermission.permission_id == perm.id)
        )
        existing_rps = list(existing_rp_res.scalars().all())
        existing_role_ids = {rp.role_id for rp in existing_rps}
        old_role_keys = [all_roles[r_id].key for r_id in all_roles if all_roles[r_id].id in existing_role_ids]

        # Grant to requested roles
        target_role_ids = set()
        for r_key in role_keys:
            if r_key in all_roles:
                target_role_ids.add(all_roles[r_key].id)
                if all_roles[r_key].id not in existing_role_ids:
                    self.db.add(RolePermission(role_id=all_roles[r_key].id, permission_id=perm.id))

        # Revoke from removed roles
        for rp in existing_rps:
            if rp.role_id not in target_role_ids:
                await self.db.delete(rp)

        # Audit event
        audit = AuditService(self.db)
        await audit.log_event(
            event_type="WORKSPACE_ROLE_ACCESS_MODIFIED",
            user_id=actor_user_id,
            entity_type="workspace",
            entity_id=None,
            before_data={"workspace_key": workspace_key, "permission": p_key, "roles": old_role_keys},
            after_data={"workspace_key": workspace_key, "permission": p_key, "roles": role_keys},
            ip_address=ip_address,
        )
        await self.db.flush()

        all_items = await self.get_all_workspaces()
        return next(i for i in all_items if i.key == workspace_key)
