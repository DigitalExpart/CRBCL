"""Permission constants for CRBCL Platform."""

from enum import StrEnum


class Permissions(StrEnum):
    # Intake & Referral permissions (Phase 3)
    INTAKE_READ = "intake.read"
    INTAKE_CREATE = "intake.create"
    INTAKE_UPDATE = "intake.update"
    INTAKE_DELETE = "intake.delete"
    INTAKE_ASSIGN = "intake.assign"
    INTAKE_SUBMIT = "intake.submit"
    INTAKE_APPROVE = "intake.approve"
    INTAKE_RETURN = "intake.return"
    INTAKE_REPORTER_READ = "intake.reporter.read"
    INTAKE_REPORTER_WRITE = "intake.reporter.write"
    INTAKE_DECISION_READ = "intake.decision.read"
    INTAKE_DECISION_WRITE = "intake.decision.write"
    INTAKE_HISTORY_READ = "intake.history.read"
    INTAKE_LINK_READ = "intake.link.read"
    INTAKE_LINK_WRITE = "intake.link.write"

    # Client permissions
    CLIENT_READ = "client.read"
    CLIENT_CREATE = "client.create"
    CLIENT_UPDATE = "client.update"
    CLIENT_DELETE = "client.delete"

    # Field-level client permissions
    CLIENT_IDENTIFIERS_READ = "client.identifiers.read"
    CLIENT_IDENTIFIERS_WRITE = "client.identifiers.write"
    CLIENT_MEDICAL_READ = "client.medical.read"
    CLIENT_MEDICAL_WRITE = "client.medical.write"
    CLIENT_SCHOOL_READ = "client.school.read"
    CLIENT_SCHOOL_WRITE = "client.school.write"
    CLIENT_CULTURAL_READ = "client.cultural.read"
    CLIENT_CULTURAL_WRITE = "client.cultural.write"
    CLIENT_DOCUMENTS_READ = "client.documents.read"
    CLIENT_DOCUMENTS_WRITE = "client.documents.write"

    # Family permissions
    FAMILY_READ = "family.read"
    FAMILY_CREATE = "family.create"
    FAMILY_UPDATE = "family.update"
    FAMILY_DELETE = "family.delete"
    FAMILY_RELATIONSHIPS_READ = "family.relationships.read"
    FAMILY_RELATIONSHIPS_WRITE = "family.relationships.write"

    # Household permissions
    HOUSEHOLD_READ = "household.read"
    HOUSEHOLD_WRITE = "household.write"

    # Provider permissions
    PROVIDER_READ = "provider.read"
    PROVIDER_WRITE = "provider.write"

    # School permissions
    SCHOOL_READ = "school.read"
    SCHOOL_WRITE = "school.write"

    # Core Case permissions (Phase 4)
    CASE_READ = "case.read"
    CASE_CREATE = "case.create"
    CASE_UPDATE = "case.update"
    CASE_DELETE = "case.delete"
    CASE_ASSIGN = "case.assign"
    CASE_CLOSE = "case.close"
    CASE_REOPEN = "case.reopen"

    # Case Sub-domain permissions (Phase 4)
    CASE_PEOPLE_READ = "case.people.read"
    CASE_PEOPLE_WRITE = "case.people.write"
    CASE_ASSIGNMENT_READ = "case.assignment.read"
    CASE_ASSIGNMENT_WRITE = "case.assignment.write"
    CASE_EXTERNAL_WORKER_READ = "case.external_worker.read"
    CASE_EXTERNAL_WORKER_WRITE = "case.external_worker.write"
    CASE_SOURCE_READ = "case.source.read"
    CASE_SOURCE_WRITE = "case.source.write"
    CASE_LINK_READ = "case.link.read"
    CASE_LINK_WRITE = "case.link.write"
    CASE_RESTRICTION_READ = "case.restriction.read"
    CASE_RESTRICTION_MANAGE = "case.restriction.manage"
    CASE_TRANSFER_READ = "case.transfer.read"
    CASE_TRANSFER_CREATE = "case.transfer.create"
    CASE_TRANSFER_APPROVE = "case.transfer.approve"

    # Case note permissions (Phase 4)
    CASE_NOTE_READ = "case_note.read"
    CASE_NOTE_CREATE = "case_note.create"
    CASE_NOTE_UPDATE = "case_note.update"
    CASE_NOTE_COMPLETE = "case_note.complete"
    CASE_NOTE_LOCK = "case_note.lock"
    CASE_NOTE_UNLOCK = "case_note.unlock"
    CASE_NOTE_ADDENDUM = "case_note.addendum"
    CASE_NOTE_EXPORT = "case_note.export"

    # Document permissions
    DOCUMENT_READ = "document.read"
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_DELETE = "document.delete"

    # Assessment Engine permissions (Phase 5)
    ASSESSMENT_READ = "assessment.read"
    ASSESSMENT_CREATE = "assessment.create"
    ASSESSMENT_UPDATE = "assessment.update"
    ASSESSMENT_COMPLETE = "assessment.complete"
    ASSESSMENT_LOCK = "assessment.lock"
    ASSESSMENT_UNLOCK = "assessment.unlock"
    ASSESSMENT_REASSIGN = "assessment.reassign"
    ASSESSMENT_PRINT = "assessment.print"
    ASSESSMENT_COMPARE = "assessment.compare"
    ASSESSMENT_HOME_READ = "assessment.home.read"
    ASSESSMENT_HOME_WRITE = "assessment.home.write"
    ASSESSMENT_THREAT_READ = "assessment.threat.read"
    ASSESSMENT_THREAT_WRITE = "assessment.threat.write"
    ASSESSMENT_AIEI_READ = "assessment.aiei.read"
    ASSESSMENT_AIEI_WRITE = "assessment.aiei.write"
    ASSESSMENT_TEMPLATE_READ = "assessment.template.read"
    ASSESSMENT_TEMPLATE_MANAGE = "assessment.template.manage"

    # Team & User Admin permissions
    ADMIN_USERS_MANAGE = "admin.users.manage"
    ADMIN_ROLES_MANAGE = "admin.roles.manage"
    ADMIN_TEAMS_MANAGE = "admin.teams.manage"
    ADMIN_CONFIGURATION_MANAGE = "admin.configuration.manage"

    # Audit & Timeline permissions
    AUDIT_READ = "audit.read"
    ACCESS_EVENT_READ = "access_event.read"
    TIMELINE_READ = "timeline.read"
