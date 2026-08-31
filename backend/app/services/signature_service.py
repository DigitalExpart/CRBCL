"""Signature and Document Hashing Service for Family Wellness Plans (Phase 6)."""

import hashlib
import json
from datetime import date, datetime
from typing import Any

from app.models.plan import PlanVersion


class SignatureService:
    """Computes deterministic SHA-256 canonical document hashes and verifies signatures."""

    @staticmethod
    def _json_serial(obj: Any) -> Any:
        """JSON serializer for date/datetime objects."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    @classmethod
    def build_canonical_payload(cls, version: PlanVersion) -> dict[str, Any]:
        """Construct deterministic dictionary of all finalized plan content."""
        plan = version.plan
        payload: dict[str, Any] = {
            "plan_id": str(plan.id) if plan else str(version.plan_id),
            "plan_type": plan.plan_type if plan else "UNKNOWN",
            "version_number": version.version_number,
            "meeting_date": version.meeting_date.isoformat() if version.meeting_date else None,
            "meeting_location": version.meeting_location,
            "narrative": version.narrative,
            "participants": [
                {
                    "name": p.name,
                    "participant_type": p.participant_type,
                    "relationship": p.relationship,
                    "role": p.role,
                    "attendance_status": p.attendance_status,
                    "signature_required": p.signature_required,
                }
                for p in sorted(version.participants, key=lambda x: (x.name or "", str(x.id)))
            ],
            "concerns": [
                {
                    "concern_type": c.concern_type,
                    "statement": c.statement,
                    "severity": c.severity,
                    "sort_order": c.sort_order,
                }
                for c in sorted(version.concerns, key=lambda x: (x.sort_order, str(x.id)))
            ],
            "strengths": [
                {
                    "category": s.category,
                    "statement": s.statement,
                    "sort_order": s.sort_order,
                }
                for s in sorted(version.strengths, key=lambda x: (x.sort_order, str(x.id)))
            ],
            "goals": [
                {
                    "goal_text": g.goal_text,
                    "category": g.category,
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                    "status": g.status,
                    "sort_order": g.sort_order,
                    "activities": [
                        {
                            "activity_text": a.activity_text,
                            "responsible_type": a.responsible_type,
                            "responsible_name": a.responsible_name,
                            "due_date": a.due_date.isoformat() if a.due_date else None,
                            "status": a.status,
                            "sort_order": a.sort_order,
                        }
                        for a in sorted(g.activities, key=lambda x: (x.sort_order, str(x.id)))
                    ],
                }
                for g in sorted(version.goals, key=lambda x: (x.sort_order, str(x.id)))
            ],
        }
        return payload

    @classmethod
    def compute_document_hash(cls, version: PlanVersion) -> str:
        """Generate 64-char hex SHA-256 hash of canonical plan representation."""
        payload = cls.build_canonical_payload(version)
        canonical_json = json.dumps(
            payload,
            sort_keys=True,
            default=cls._json_serial,
            ensure_ascii=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def verify_integrity(cls, version: PlanVersion) -> bool:
        """Check if current plan content exactly matches the stored document hash."""
        if not version.document_hash:
            return False
        current_hash = cls.compute_document_hash(version)
        return current_hash == version.document_hash
