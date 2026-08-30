"""CRBCL Platform — Bootstrap and Database Seeding Script.

Seeds:
- 11 Default Roles
- 35+ Capability-based Permissions (including Phase 2 field-level permissions)
- Role-Permission Mappings (IT Admin gets NO client/case permissions)
- 22 CRBCL Teams
- Standard Lookup Lists & Values
- Terminology baseline (English)
- Dev Administrator (ONLY when APP_ENV=development)
"""

from __future__ import annotations

import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.core.config import get_settings
from app.core.database import Base, async_session_factory, engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"

from app.models.config import LookupList, LookupValue
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import Team, TeamMembership
from app.models.terminology import TerminologyKey, TerminologyTranslation
from app.models.user import User
from app.permissions.constants import Permissions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crbcl.seed")

# ── 1. Default Roles ─────────────────────────────────────────
ROLES_DATA = [
    {
        "key": "executive_director",
        "name": "Executive Director",
        "description": "Executive leadership with organization-wide governance and oversight.",
        "is_system": True,
    },
    {
        "key": "director_manager",
        "name": "Director / Manager",
        "description": "Department and program directors managing teams and services.",
        "is_system": True,
    },
    {
        "key": "supervisor",
        "name": "Supervisor",
        "description": "Clinical and case supervisors reviewing and approving casework.",
        "is_system": True,
    },
    {
        "key": "caseworker",
        "name": "Caseworker",
        "description": "Primary case managers handling client files, plans, and case notes.",
        "is_system": True,
    },
    {
        "key": "case_aide",
        "name": "Case Aide",
        "description": "Support staff assisting caseworkers with administrative tasks.",
        "is_system": True,
    },
    {
        "key": "finance_staff",
        "name": "Finance Staff",
        "description": "Financial administration, funding management, and payments.",
        "is_system": True,
    },
    {
        "key": "hr_staff",
        "name": "HR Staff",
        "description": "Human resources and personnel management.",
        "is_system": True,
    },
    {
        "key": "it_admin",
        "name": "IT Admin",
        "description": "Technical system administrator. Manages users, configuration, and audit logs. NO access to case/client data.",
        "is_system": True,
    },
    {
        "key": "cultural_worker",
        "name": "Cultural Worker",
        "description": "Elders, Knowledge Keepers, and cultural connections staff.",
        "is_system": True,
    },
    {
        "key": "clinical_staff",
        "name": "LPN / Clinical Staff",
        "description": "Clinical practitioners, nurses, and wellness counsellors.",
        "is_system": True,
    },
    {
        "key": "external_worker",
        "name": "External Worker",
        "description": "Partner agency workers with restricted read-only case access.",
        "is_system": True,
    },
]

# ── 2. Permissions Definition ────────────────────────────────
PERMISSIONS_DATA = [
    # Intake & Referrals (Phase 3)
    {"key": Permissions.INTAKE_READ, "name": "Read Intake Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_CREATE, "name": "Create Intake Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_UPDATE, "name": "Update Intake Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_DELETE, "name": "Delete Intake Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_ASSIGN, "name": "Assign Intake Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_SUBMIT, "name": "Submit Intake for Supervisor Approval", "category": "intake"},
    {"key": Permissions.INTAKE_APPROVE, "name": "Approve Intake Referrals & Dispositions", "category": "intake"},
    {"key": Permissions.INTAKE_RETURN, "name": "Return Intake Referrals to Worker", "category": "intake"},
    {"key": Permissions.INTAKE_REPORTER_READ, "name": "Read Confidential Reporter Details", "category": "intake"},
    {"key": Permissions.INTAKE_REPORTER_WRITE, "name": "Write Confidential Reporter Details", "category": "intake"},
    {"key": Permissions.INTAKE_DECISION_READ, "name": "Read Intake Decisions & Dispositions", "category": "intake"},
    {"key": Permissions.INTAKE_DECISION_WRITE, "name": "Write Intake Decisions & Dispositions", "category": "intake"},
    {"key": Permissions.INTAKE_HISTORY_READ, "name": "Read Prior History across Cases & Referrals", "category": "intake"},
    {"key": Permissions.INTAKE_LINK_READ, "name": "Read Cross-Referral Links", "category": "intake"},
    {"key": Permissions.INTAKE_LINK_WRITE, "name": "Create / Manage Cross-Referral Links", "category": "intake"},
    # Clients
    {"key": Permissions.CLIENT_READ, "name": "Read Clients", "category": "clients"},
    {"key": Permissions.CLIENT_CREATE, "name": "Create Clients", "category": "clients"},
    {"key": Permissions.CLIENT_UPDATE, "name": "Update Clients", "category": "clients"},
    {"key": Permissions.CLIENT_DELETE, "name": "Delete Clients", "category": "clients"},
    # Field-level Client
    {"key": Permissions.CLIENT_IDENTIFIERS_READ, "name": "Read Sensitive Identifiers (Treaty, Health Card)", "category": "clients"},
    {"key": Permissions.CLIENT_IDENTIFIERS_WRITE, "name": "Write Sensitive Identifiers", "category": "clients"},
    {"key": Permissions.CLIENT_MEDICAL_READ, "name": "Read Client Medical Profile & Medications", "category": "clients"},
    {"key": Permissions.CLIENT_MEDICAL_WRITE, "name": "Write Client Medical Profile & Medications", "category": "clients"},
    {"key": Permissions.CLIENT_SCHOOL_READ, "name": "Read School & Enrolment Data", "category": "clients"},
    {"key": Permissions.CLIENT_SCHOOL_WRITE, "name": "Write School & Enrolment Data", "category": "clients"},
    {"key": Permissions.CLIENT_CULTURAL_READ, "name": "Read Cultural Connections & Identity", "category": "clients"},
    {"key": Permissions.CLIENT_CULTURAL_WRITE, "name": "Write Cultural Connections & Identity", "category": "clients"},
    {"key": Permissions.CLIENT_DOCUMENTS_READ, "name": "Read Client Documents", "category": "clients"},
    {"key": Permissions.CLIENT_DOCUMENTS_WRITE, "name": "Write Client Documents", "category": "clients"},
    # Families & Households
    {"key": Permissions.FAMILY_READ, "name": "Read Families", "category": "families"},
    {"key": Permissions.FAMILY_CREATE, "name": "Create Families", "category": "families"},
    {"key": Permissions.FAMILY_UPDATE, "name": "Update Families", "category": "families"},
    {"key": Permissions.FAMILY_DELETE, "name": "Delete Families", "category": "families"},
    {"key": Permissions.FAMILY_RELATIONSHIPS_READ, "name": "Read Family Relationships & Genograms", "category": "families"},
    {"key": Permissions.FAMILY_RELATIONSHIPS_WRITE, "name": "Write Family Relationships & Genograms", "category": "families"},
    {"key": Permissions.HOUSEHOLD_READ, "name": "Read Households & Locations", "category": "families"},
    {"key": Permissions.HOUSEHOLD_WRITE, "name": "Write Households & Locations", "category": "families"},
    # Providers & Schools
    {"key": Permissions.PROVIDER_READ, "name": "Read Providers Pool", "category": "providers"},
    {"key": Permissions.PROVIDER_WRITE, "name": "Write Providers Pool", "category": "providers"},
    {"key": Permissions.SCHOOL_READ, "name": "Read Schools Directory", "category": "schools"},
    {"key": Permissions.SCHOOL_WRITE, "name": "Write Schools Directory", "category": "schools"},
    # Cases
    {"key": Permissions.CASE_READ, "name": "Read Cases", "category": "cases"},
    {"key": Permissions.CASE_CREATE, "name": "Create Cases", "category": "cases"},
    {"key": Permissions.CASE_UPDATE, "name": "Update Cases", "category": "cases"},
    {"key": Permissions.CASE_DELETE, "name": "Delete Cases", "category": "cases"},
    {"key": Permissions.CASE_ASSIGN, "name": "Assign Cases", "category": "cases"},
    # Case Notes
    {"key": Permissions.CASE_NOTE_READ, "name": "Read Case Notes", "category": "case_notes"},
    {"key": Permissions.CASE_NOTE_CREATE, "name": "Create Case Notes", "category": "case_notes"},
    {"key": Permissions.CASE_NOTE_UPDATE, "name": "Update Case Notes", "category": "case_notes"},
    {"key": Permissions.CASE_NOTE_LOCK, "name": "Lock Case Notes", "category": "case_notes"},
    {"key": Permissions.CASE_NOTE_UNLOCK, "name": "Unlock Case Notes", "category": "case_notes"},
    # Documents
    {"key": Permissions.DOCUMENT_READ, "name": "Read Documents", "category": "documents"},
    {"key": Permissions.DOCUMENT_UPLOAD, "name": "Upload Documents", "category": "documents"},
    {"key": Permissions.DOCUMENT_DELETE, "name": "Delete Documents", "category": "documents"},
    # Administration
    {"key": Permissions.ADMIN_USERS_MANAGE, "name": "Manage Users", "category": "admin"},
    {"key": Permissions.ADMIN_ROLES_MANAGE, "name": "Manage Roles", "category": "admin"},
    {"key": Permissions.ADMIN_TEAMS_MANAGE, "name": "Manage Teams", "category": "admin"},
    {"key": Permissions.ADMIN_CONFIGURATION_MANAGE, "name": "Manage Configuration", "category": "admin"},
    # Audit & Timeline
    {"key": Permissions.AUDIT_READ, "name": "Read Audit Logs", "category": "audit"},
    {"key": Permissions.ACCESS_EVENT_READ, "name": "Read Access Events", "category": "audit"},
    {"key": Permissions.TIMELINE_READ, "name": "Read Sacred Timeline", "category": "timeline"},
]

# ── 3. Role-Permission Mappings ──────────────────────────────
ROLE_PERMISSIONS_MAP = {
    "executive_director": [p["key"] for p in PERMISSIONS_DATA],
    "director_manager": [
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_ASSIGN, Permissions.INTAKE_SUBMIT, Permissions.INTAKE_APPROVE, Permissions.INTAKE_RETURN,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_CULTURAL_READ,
        Permissions.CLIENT_DOCUMENTS_READ, Permissions.CLIENT_DOCUMENTS_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE, Permissions.CASE_ASSIGN,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE, Permissions.CASE_NOTE_LOCK,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
        Permissions.ADMIN_TEAMS_MANAGE,
        Permissions.TIMELINE_READ,
    ],
    "supervisor": [
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_ASSIGN, Permissions.INTAKE_SUBMIT, Permissions.INTAKE_APPROVE, Permissions.INTAKE_RETURN,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_SCHOOL_WRITE,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.CLIENT_DOCUMENTS_READ, Permissions.CLIENT_DOCUMENTS_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE, Permissions.CASE_ASSIGN,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE, Permissions.CASE_NOTE_UPDATE, Permissions.CASE_NOTE_LOCK,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
        Permissions.TIMELINE_READ,
    ],
    "caseworker": [
        Permissions.INTAKE_READ, Permissions.INTAKE_CREATE, Permissions.INTAKE_UPDATE,
        Permissions.INTAKE_SUBMIT,
        Permissions.INTAKE_REPORTER_READ, Permissions.INTAKE_REPORTER_WRITE,
        Permissions.INTAKE_DECISION_READ, Permissions.INTAKE_DECISION_WRITE,
        Permissions.INTAKE_HISTORY_READ, Permissions.INTAKE_LINK_READ, Permissions.INTAKE_LINK_WRITE,
        Permissions.CLIENT_READ, Permissions.CLIENT_CREATE, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_IDENTIFIERS_READ, Permissions.CLIENT_IDENTIFIERS_WRITE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_SCHOOL_WRITE,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.CLIENT_DOCUMENTS_READ, Permissions.CLIENT_DOCUMENTS_WRITE,
        Permissions.FAMILY_READ, Permissions.FAMILY_CREATE, Permissions.FAMILY_UPDATE,
        Permissions.FAMILY_RELATIONSHIPS_READ, Permissions.FAMILY_RELATIONSHIPS_WRITE,
        Permissions.HOUSEHOLD_READ, Permissions.HOUSEHOLD_WRITE,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.SCHOOL_READ, Permissions.SCHOOL_WRITE,
        Permissions.CASE_READ, Permissions.CASE_CREATE, Permissions.CASE_UPDATE,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE, Permissions.CASE_NOTE_UPDATE,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
        Permissions.TIMELINE_READ,
    ],
    "case_aide": [
        Permissions.INTAKE_READ, Permissions.INTAKE_HISTORY_READ,
        Permissions.CLIENT_READ,
        Permissions.CLIENT_SCHOOL_READ, Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_DOCUMENTS_READ,
        Permissions.FAMILY_READ,
        Permissions.FAMILY_RELATIONSHIPS_READ,
        Permissions.HOUSEHOLD_READ,
        Permissions.PROVIDER_READ, Permissions.SCHOOL_READ,
        Permissions.CASE_READ,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
        Permissions.TIMELINE_READ,
    ],
    "finance_staff": [
        Permissions.CLIENT_READ,
        Permissions.PROVIDER_READ,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
    ],
    "hr_staff": [
        Permissions.ADMIN_USERS_MANAGE,
        Permissions.ADMIN_TEAMS_MANAGE,
    ],
    # IT Admin gets ONLY system admin & audit logs — strictly NO clinical or client access
    "it_admin": [
        Permissions.ADMIN_USERS_MANAGE,
        Permissions.ADMIN_ROLES_MANAGE,
        Permissions.ADMIN_TEAMS_MANAGE,
        Permissions.ADMIN_CONFIGURATION_MANAGE,
        Permissions.AUDIT_READ,
        Permissions.ACCESS_EVENT_READ,
    ],
    "cultural_worker": [
        Permissions.CLIENT_READ,
        Permissions.CLIENT_CULTURAL_READ, Permissions.CLIENT_CULTURAL_WRITE,
        Permissions.FAMILY_READ,
        Permissions.FAMILY_RELATIONSHIPS_READ,
        Permissions.CASE_READ,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.DOCUMENT_READ,
        Permissions.TIMELINE_READ,
    ],
    "clinical_staff": [
        Permissions.CLIENT_READ, Permissions.CLIENT_UPDATE,
        Permissions.CLIENT_MEDICAL_READ, Permissions.CLIENT_MEDICAL_WRITE,
        Permissions.FAMILY_READ,
        Permissions.PROVIDER_READ, Permissions.PROVIDER_WRITE,
        Permissions.CASE_READ,
        Permissions.CASE_NOTE_READ, Permissions.CASE_NOTE_CREATE,
        Permissions.DOCUMENT_READ, Permissions.DOCUMENT_UPLOAD,
        Permissions.TIMELINE_READ,
    ],
    "external_worker": [
        Permissions.CLIENT_READ,
        Permissions.CASE_READ,
        Permissions.CASE_NOTE_READ,
    ],
}

# ── 4. The 22 CRBCL Teams ────────────────────────────────────
TEAMS_DATA = [
    {"code": "cfs_protection", "name": "Child & Family Services (Protection)", "short_name": "CFS Protection", "sort_order": 1, "color": "bg-orange-700", "description": "Case management, child safety, family plans, assessments, intervention, family reunification, kinship support."},
    {"code": "prevention", "name": "Prevention", "short_name": "Prevention", "sort_order": 2, "color": "bg-amber-700", "description": "Counselling, family wellness, parenting programs, traditional healing, advocacy, youth and family programs."},
    {"code": "post_majority", "name": "Post-Majority", "short_name": "Post-Majority", "sort_order": 3, "color": "bg-indigo-800", "description": "Young adult transition support, independent living skills, aftercare services, life skills for youth aging out of care."},
    {"code": "intake_investigations", "name": "Intake & Investigations", "short_name": "Intake & Investigations", "sort_order": 4, "color": "bg-blue-700", "description": "Receiving concerns, screening, initial assessments, assigning cases, emergency responses."},
    {"code": "cultural_connections", "name": "Cultural Connections", "short_name": "Cultural Connections", "sort_order": 5, "color": "bg-teal-700", "description": "Elders, Knowledge Keepers, ceremonies, land-based activities, language, cultural teachings."},
    {"code": "youth_engagement", "name": "Youth Engagement", "short_name": "Youth Engagement", "sort_order": 6, "color": "bg-cyan-700", "description": "Child development, youth engagement, education support, healthy relationship programs, recreation."},
    {"code": "growing_up_well", "name": "Growing Up Well", "short_name": "Growing Up Well", "sort_order": 7, "color": "bg-blue-800", "description": "Social worker intervention, child development monitoring, family intervention planning, protective services."},
    {"code": "sacred_wolf_lodge", "name": "Sacred Wolf Lodge", "short_name": "Sacred Wolf Lodge", "sort_order": 8, "color": "bg-yellow-700", "description": "Residential family support, life skills coaching, cultural teachings, recovery support, family stabilization."},
    {"code": "navigation_coordination", "name": "Navigation / Case Coordination", "short_name": "Navigation", "sort_order": 9, "color": "bg-emerald-700", "description": "System navigation support, referral coordination, service access guidance, community resource connection."},
    {"code": "good_life_program", "name": "Good Life Program", "short_name": "Good Life Program", "sort_order": 10, "color": "bg-green-700", "description": "Frontline family workers, ongoing family relationships, service coordination, referrals, progress tracking."},
    {"code": "quality_assurance", "name": "Quality Assurance & Practice", "short_name": "QA & Practice", "sort_order": 11, "color": "bg-indigo-700", "description": "Policy compliance, service standards, data quality, audits, reporting, continuous improvement."},
    {"code": "legal_jurisdiction", "name": "Legal & Jurisdiction", "short_name": "Legal & Jurisdiction", "sort_order": 12, "color": "bg-violet-700", "description": "Miyo Pimatisowin Act compliance, legal matters, child welfare legislation, court coordination."},
    {"code": "finance", "name": "Finance", "short_name": "Finance", "sort_order": 13, "color": "bg-fuchsia-700", "description": "Budgets, accounting, payroll, procurement, contracts, financial reporting."},
    {"code": "human_resources", "name": "Human Resources", "short_name": "Human Resources", "sort_order": 14, "color": "bg-purple-700", "description": "Recruitment, employee relations, training, wellness, workplace policies."},
    {"code": "housing", "name": "Housing", "short_name": "Housing", "sort_order": 15, "color": "bg-lime-700", "description": "Housing support, emergency shelter assistance, housing advocacy, home maintenance education."},
    {"code": "maintenance_facilities", "name": "Maintenance & Facilities", "short_name": "Facilities", "sort_order": 16, "color": "bg-stone-700", "description": "Facilities management, building maintenance, logistics, physical lodge infrastructure."},
    {"code": "it_asset_mgmt", "name": "IT & Asset Management", "short_name": "IT & Asset", "sort_order": 17, "color": "bg-pink-700", "description": "Case management systems, cybersecurity, AI tools, data warehouse, analytics, Microsoft 365, digital transformation."},
    {"code": "donations_fundraising", "name": "Donations & Fundraising", "short_name": "Donations", "sort_order": 18, "color": "bg-rose-700", "description": "Fundraising campaigns, donor relations, grant submissions, community sponsorships."},
    {"code": "volunteer_coordination", "name": "Volunteer Coordination", "short_name": "Volunteers", "sort_order": 19, "color": "bg-red-700", "description": "Volunteer onboarding, screening, scheduling, community volunteer initiatives."},
    {"code": "communications", "name": "Communications", "short_name": "Communications", "sort_order": 20, "color": "bg-rose-700", "description": "Community relations, events, public communications, social media, awareness campaigns."},
    {"code": "administration", "name": "Administration", "short_name": "Administration", "sort_order": 21, "color": "bg-slate-700", "description": "Office management, records administration, intake logistics, administrative operational support."},
    {"code": "executive_leadership", "name": "Executive Leadership", "short_name": "Executive Leadership", "sort_order": 22, "color": "bg-red-900", "description": "Strategic planning, governance, partnerships, funding, organizational leadership."},
]

# ── 5. Standard Lookups ──────────────────────────────────────
LOOKUPS_DATA = {
    "case_statuses": [
        {"key": "Open", "label": "Open", "sort_order": 1},
        {"key": "In Progress", "label": "In Progress", "sort_order": 2},
        {"key": "Under Review", "label": "Under Review", "sort_order": 3},
        {"key": "Pending", "label": "Pending", "sort_order": 4},
        {"key": "Escalated", "label": "Escalated", "sort_order": 5},
        {"key": "Closed", "label": "Closed", "sort_order": 6},
    ],
    "risk_levels": [
        {"key": "Low", "label": "Low", "sort_order": 1},
        {"key": "Medium", "label": "Medium", "sort_order": 2},
        {"key": "High", "label": "High", "sort_order": 3},
        {"key": "Critical", "label": "Critical", "sort_order": 4},
    ],
    "client_statuses": [
        {"key": "Active", "label": "Active", "sort_order": 1},
        {"key": "Inactive", "label": "Inactive", "sort_order": 2},
        {"key": "Pending Intake", "label": "Pending Intake", "sort_order": 3},
        {"key": "Closed", "label": "Closed", "sort_order": 4},
        {"key": "Referred", "label": "Referred", "sort_order": 5},
    ],
    "indigenous_identities": [
        {"key": "First Nations", "label": "First Nations", "sort_order": 1},
        {"key": "Métis", "label": "Métis", "sort_order": 2},
        {"key": "Inuit", "label": "Inuit", "sort_order": 3},
        {"key": "Non-Indigenous", "label": "Non-Indigenous", "sort_order": 4},
        {"key": "Prefer Not to Say", "label": "Prefer Not to Say", "sort_order": 5},
    ],
    "strengths": [
        {"key": "trustworthy", "label": "Trustworthy & Honest", "sort_order": 1},
        {"key": "responsible", "label": "Responsible & Dependable", "sort_order": 2},
        {"key": "good_attendance", "label": "Good School / Program Attendance", "sort_order": 3},
        {"key": "cultural_engagement", "label": "Strong Cultural & Community Pride", "sort_order": 4},
        {"key": "family_connection", "label": "Close Kinship & Family Bond", "sort_order": 5},
        {"key": "artistic_athletic", "label": "Artistic & Athletic Talents", "sort_order": 6},
    ],
    "challenges": [
        {"key": "attendance_concerns", "label": "Attendance & Truancy Concerns", "sort_order": 1},
        {"key": "substance_misuse", "label": "Substance Misuse Concern", "sort_order": 2},
        {"key": "running_away", "label": "High-Risk Runaway Behaviour", "sort_order": 3},
        {"key": "justice_involvement", "label": "Justice System Involvement", "sort_order": 4},
        {"key": "mental_health_distress", "label": "Mental Health & Emotional Distress", "sort_order": 5},
        {"key": "housing_instability", "label": "Housing Instability / Overcrowding", "sort_order": 6},
    ],
    # ── Phase 3: Intake & Referral Lookups ────────────────────
    "referral_methods": [
        {"key": "phone", "label": "Telephone Call", "sort_order": 1},
        {"key": "in_person", "label": "In Person / Walk-In", "sort_order": 2},
        {"key": "electronic", "label": "Electronic / Web Intake Portal", "sort_order": 3},
        {"key": "law_enforcement", "label": "Law Enforcement / Police Referral", "sort_order": 4},
        {"key": "school", "label": "School / Educator Referral", "sort_order": 5},
        {"key": "healthcare", "label": "Healthcare / Hospital Referral", "sort_order": 6},
        {"key": "self_referral", "label": "Child / Youth Self-Referral", "sort_order": 7},
        {"key": "community_member", "label": "Community Member / Relative", "sort_order": 8},
        {"key": "other", "label": "Other Referral Source", "sort_order": 9},
    ],
    "referral_priorities": [
        {"key": "Crisis", "label": "Crisis (Immediate Safety Intervention Required)", "sort_order": 1},
        {"key": "High", "label": "High (Response Required within 24 Hours)", "sort_order": 2},
        {"key": "Medium", "label": "Medium (Response Required within 5 Days)", "sort_order": 3},
        {"key": "Low", "label": "Low (Standard Intake Assessment)", "sort_order": 4},
    ],
    "referral_concern_types": [
        {"key": "physical_abuse", "label": "Physical Abuse / Non-Accidental Injury", "sort_order": 1},
        {"key": "neglect", "label": "Severe Neglect / Basic Needs Unmet", "sort_order": 2},
        {"key": "emotional_harm", "label": "Emotional Harm / Mental Cruelty", "sort_order": 3},
        {"key": "sexual_abuse", "label": "Sexual Abuse / Child Exploitation", "sort_order": 4},
        {"key": "domestic_violence", "label": "Domestic / Intimate Partner Violence in Home", "sort_order": 5},
        {"key": "substance_use", "label": "Caregiver Substance Misuse / Impairment", "sort_order": 6},
        {"key": "food_insecurity", "label": "Severe Food Insecurity", "sort_order": 7},
        {"key": "housing_insecurity", "label": "Housing Insecurity / Inadequate Shelter", "sort_order": 8},
        {"key": "caregiver_incapacity", "label": "Caregiver Incapacity / Abandonment", "sort_order": 9},
        {"key": "welfare_concern", "label": "General Family Welfare / Support Concern", "sort_order": 10},
        {"key": "other", "label": "Other Structured Concern", "sort_order": 11},
    ],
    "child_dispositions": [
        {"key": "PROTECTION", "label": "Child Protection Investigation (Open Protection Case)", "sort_order": 1},
        {"key": "PREVENTION", "label": "Family Prevention & Wellness Services (Open Prevention Case)", "sort_order": 2},
        {"key": "POST_MAJORITY", "label": "Post-Majority Transition Services", "sort_order": 3},
        {"key": "SCREEN_OUT", "label": "Screen Out (Unsubstantiated / No Services Required)", "sort_order": 4},
        {"key": "EXTERNAL_REFERRAL", "label": "External Agency / Community Referral", "sort_order": 5},
    ],
    "referral_person_roles": [
        {"key": "child", "label": "Child / Youth (Subject of Intake)", "sort_order": 1},
        {"key": "parent", "label": "Parent / Biological Parent", "sort_order": 2},
        {"key": "guardian", "label": "Legal Guardian / Custodian", "sort_order": 3},
        {"key": "alleged_person_of_concern", "label": "Alleged Person of Concern", "sort_order": 4},
        {"key": "relative", "label": "Extended Kin / Relative", "sort_order": 5},
        {"key": "other_adult", "label": "Household Adult / Other", "sort_order": 6},
        {"key": "collateral", "label": "Collateral Contact / Witness", "sort_order": 7},
    ],
    "referral_link_types": [
        {"key": "duplicate_report", "label": "Duplicate / Secondary Report of Same Incident", "sort_order": 1},
        {"key": "related_incident", "label": "Related Incident / Concurrent Referral", "sort_order": 2},
        {"key": "prior_history", "label": "Prior Intake History", "sort_order": 3},
        {"key": "split_family", "label": "Cross-Household / Sibling Split Connection", "sort_order": 4},
        {"key": "subsequent_report", "label": "Subsequent Report on Open Case", "sort_order": 5},
    ],
}


async def seed_database(db: AsyncSession) -> None:
    """Seed initial data into a clean or existing database."""
    logger.info("Seeding Permissions...")
    perm_models = {}
    for p_data in PERMISSIONS_DATA:
        res = await db.execute(select(Permission).where(Permission.key == p_data["key"]))
        perm = res.scalar_one_or_none()
        if not perm:
            perm = Permission(**p_data)
            db.add(perm)
            await db.flush()
        perm_models[p_data["key"]] = perm

    logger.info("Seeding Roles and Role-Permission Mappings...")
    role_models = {}
    for r_data in ROLES_DATA:
        res = await db.execute(select(Role).where(Role.key == r_data["key"]))
        role = res.scalar_one_or_none()
        if not role:
            role = Role(**r_data)
            db.add(role)
            await db.flush()
        role_models[r_data["key"]] = role

        target_perm_keys = ROLE_PERMISSIONS_MAP.get(r_data["key"], [])
        for p_key in target_perm_keys:
            perm = perm_models.get(p_key)
            if perm:
                rp_res = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if not rp_res.scalar_one_or_none():
                    rp = RolePermission(role_id=role.id, permission_id=perm.id)
                    db.add(rp)
        await db.flush()

    logger.info("Seeding 22 CRBCL Teams...")
    for t_data in TEAMS_DATA:
        res = await db.execute(select(Team).where(Team.code == t_data["code"]))
        if not res.scalar_one_or_none():
            team = Team(**t_data)
            db.add(team)
    await db.flush()

    logger.info("Seeding Lookup Lists and Values...")
    for list_key, values in LOOKUPS_DATA.items():
        res = await db.execute(select(LookupList).where(LookupList.key == list_key))
        lookup_list = res.scalar_one_or_none()
        if not lookup_list:
            lookup_list = LookupList(
                key=list_key,
                name=list_key.replace("_", " ").title(),
                is_system=True,
                is_active=True,
            )
            db.add(lookup_list)
            await db.flush()

        for v_data in values:
            v_res = await db.execute(
                select(LookupValue).where(
                    LookupValue.list_id == lookup_list.id,
                    LookupValue.key == v_data["key"],
                )
            )
            if not v_res.scalar_one_or_none():
                val = LookupValue(list_id=lookup_list.id, is_active=True, **v_data)
                db.add(val)
    await db.flush()

    # Seeding dev administrator ONLY when APP_ENV=development
    settings = get_settings()
    if settings.is_development:
        logger.info("Development mode detected: seeding default development admin user...")
        admin_email = "admin@crbcl.ca"
        admin_normalized = admin_email.lower()
        res = await db.execute(select(User).where(User.email_normalized == admin_normalized))
        admin_user = res.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                email_normalized=admin_normalized,
                password_hash=hash_password("crbcl_admin_2026"),
                full_name="System Administrator",
                display_name="Admin",
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            await db.flush()

            exec_role = role_models.get("executive_director")
            if exec_role:
                ur = UserRole(user_id=admin_user.id, role_id=exec_role.id)
                db.add(ur)
                await db.flush()

    await db.commit()
    logger.info("Database bootstrap completed successfully.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        await seed_database(session)


if __name__ == "__main__":
    asyncio.run(main())
