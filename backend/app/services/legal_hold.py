"""Legal Hold Enforcement Service preventing deletion of records under active hold."""

import uuid
from datetime import datetime

from app.models.case import Case
from app.services.integrations.utils import db_commit, db_query_first


class LegalHoldError(Exception):
    """Raised when an operation is rejected due to an active legal hold."""

    pass


async def apply_legal_hold(db, case_id: uuid.UUID, user_id: uuid.UUID, reason: str) -> Case:
    """Place a Case and associated records under an active legal retention hold."""
    case = await db_query_first(db, Case, Case.id == case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found.")

    case.is_legal_hold = True
    case.legal_hold_reason = reason
    case.legal_hold_by_id = user_id
    case.legal_hold_at = datetime.utcnow()

    await db_commit(db)
    return case


async def remove_legal_hold(db, case_id: uuid.UUID) -> Case:
    """Remove active legal retention hold from a Case."""
    case = await db_query_first(db, Case, Case.id == case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found.")

    case.is_legal_hold = False
    case.legal_hold_reason = None
    case.legal_hold_by_id = None
    case.legal_hold_at = None

    await db_commit(db)
    return case


def check_legal_hold_protection(case: Case) -> None:
    """Raise LegalHoldError if the target case is under active legal hold."""
    if case and getattr(case, "is_legal_hold", False):
        raise LegalHoldError(
            f"Case {case.case_number} is under active legal hold ({case.legal_hold_reason}). Deletion or record disposal is prohibited."
        )
