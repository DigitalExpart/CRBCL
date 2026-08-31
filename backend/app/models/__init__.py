"""CRBCL Platform — SQLAlchemy Models Package.

All models are imported here so Alembic can discover them.
"""

from app.models.user import User, Session, UserPreference  # noqa: F401
from app.models.role import Role, Permission, RolePermission, UserRole  # noqa: F401
from app.models.team import Team, TeamMembership, UserTeamAccess  # noqa: F401
from app.models.audit import AuditEvent, AccessEvent  # noqa: F401
from app.models.timeline import TimelineEvent  # noqa: F401
from app.models.outbox import OutboxEvent  # noqa: F401
from app.models.config import SystemConfig, LookupList, LookupValue  # noqa: F401
from app.models.terminology import TerminologyKey, TerminologyTranslation  # noqa: F401
from app.models.document import Document, DocumentVersion, DocumentLink, DocumentAccessEvent  # noqa: F401
from app.models.person import (  # noqa: F401
    Person,
    PersonAddress,
    PersonContact,
    PersonPhysicalDescription,
    PersonCulturalProfile,
    PersonStrength,
    PersonChallenge,
    PersonMerge,
)
from app.models.client import Client  # noqa: F401
from app.models.medical import (  # noqa: F401
    ClientMedicalProfile,
    ClientAllergy,
    ClientMedicalCondition,
    ClientMedication,
)
from app.models.provider import (  # noqa: F401
    Provider,
    ProviderLocation,
    ProviderSpecialty,
    ClientProvider,
)
from app.models.school import (  # noqa: F401
    School,
    ClientSchoolEnrolment,
)
from app.models.family import Family  # noqa: F401
from app.models.relationship import (  # noqa: F401
    FamilyMember,
    FamilyRelationship,
    Household,
    HouseholdMembership,
)
from app.models.case import Case  # noqa: F401
from app.models.case_management import (  # noqa: F401
    CaseSequence,
    CasePerson,
    CaseAssignment,
    CaseExternalWorker,
    CaseSource,
    CaseLink,
    CaseRestriction,
    CaseTransfer,
    CaseStatusHistory,
)
from app.models.case_note import (  # noqa: F401
    CaseNote,
    CaseNotePerson,
    CaseNoteAttachment,
    CaseNoteAddendum,
)
from app.models.idempotency import IdempotencyKey  # noqa: F401
from app.models.referral import (  # noqa: F401
    Referral,
    ReferralSequence,
    ReferralPerson,
    ReferralReporter,
    ReferralIncident,
    ReferralConcern,
    ChildDisposition,
    IntakeDecision,
    ReferralLink,
)
