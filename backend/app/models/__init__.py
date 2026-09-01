"""CRBCL Platform — SQLAlchemy Models Package.

All models are imported here so Alembic can discover them.
"""

from app.models.assessment import (  # noqa: F401
    Assessment,
    AssessmentAnswer,
    AssessmentAnswerOption,
    AssessmentQuestion,
    AssessmentQuestionOption,
    AssessmentSection,
    AssessmentSequence,
    AssessmentStatusHistory,
    AssessmentTemplate,
    AssessmentTemplateVersion,
    AssessmentUnlockEvent,
)
from app.models.audit import AccessEvent, AuditEvent  # noqa: F401
from app.models.calendar import (  # noqa: F401
    CalendarEvent,
    CalendarRecurrenceRule,
)
from app.models.case import Case  # noqa: F401
from app.models.case_management import (  # noqa: F401
    CaseAssignment,
    CaseExternalWorker,
    CaseLink,
    CasePerson,
    CaseRestriction,
    CaseSequence,
    CaseSource,
    CaseStatusHistory,
    CaseTransfer,
)
from app.models.case_note import (  # noqa: F401
    CaseNote,
    CaseNoteAddendum,
    CaseNoteAttachment,
    CaseNotePerson,
)
from app.models.client import Client  # noqa: F401
from app.models.config import LookupList, LookupValue, SystemConfig  # noqa: F401
from app.models.document import Document, DocumentAccessEvent, DocumentLink, DocumentVersion  # noqa: F401
from app.models.family import Family  # noqa: F401
from app.models.idempotency import IdempotencyKey  # noqa: F401
from app.models.medical import (  # noqa: F401
    ClientAllergy,
    ClientMedicalCondition,
    ClientMedicalProfile,
    ClientMedication,
)
from app.models.notification import (  # noqa: F401
    Notification,
    NotificationDelivery,
    NotificationPreference,
    NotificationTemplate,
)
from app.models.outbox import OutboxEvent  # noqa: F401
from app.models.person import (  # noqa: F401
    Person,
    PersonAddress,
    PersonChallenge,
    PersonContact,
    PersonCulturalProfile,
    PersonMerge,
    PersonPhysicalDescription,
    PersonStrength,
)
from app.models.placement import (  # noqa: F401
    ActiveEffort,
    BackgroundCheck,
    CourtEvent,
    DischargeEpisode,
    InHomePlacement,
    PermanencyPlan,
    PlacementEpisode,
    RemovalEpisode,
    RespiteEpisode,
    VisitationPlan,
)
from app.models.placement_home import (  # noqa: F401
    PlacementHome,
    PlacementHomeContactLog,
    PlacementHomeLicense,
    PlacementHomeMember,
    PlacementHomeVisit,
)
from app.models.plan import (  # noqa: F401
    GoalProgressUpdate,
    Plan,
    PlanActivity,
    PlanAssessment,
    PlanConcern,
    PlanGoal,
    PlanParticipant,
    PlanSequence,
    PlanSignature,
    PlanStrength,
    PlanVersion,
)
from app.models.provider import (  # noqa: F401
    ClientProvider,
    Provider,
    ProviderLocation,
    ProviderSpecialty,
)
from app.models.referral import (  # noqa: F401
    ChildDisposition,
    IntakeDecision,
    Referral,
    ReferralConcern,
    ReferralIncident,
    ReferralLink,
    ReferralPerson,
    ReferralReporter,
    ReferralSequence,
)
from app.models.relationship import (  # noqa: F401
    FamilyMember,
    FamilyRelationship,
    Household,
    HouseholdMembership,
)
from app.models.role import Permission, Role, RolePermission, UserRole  # noqa: F401
from app.models.school import (  # noqa: F401
    ClientSchoolEnrolment,
    School,
)
from app.models.staffing import (  # noqa: F401
    StaffingAttendee,
    StaffingCase,
    StaffingSession,
)
from app.models.team import Team, TeamMembership, UserTeamAccess  # noqa: F401
from app.models.terminology import TerminologyKey, TerminologyTranslation  # noqa: F401
from app.models.timeline import TimelineEvent  # noqa: F401
from app.models.user import EmailVerificationCode, Session, User, UserPreference  # noqa: F401
