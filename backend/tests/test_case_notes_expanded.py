"""Tests for Expanded Case Notes, Immutability Locking, Addenda, Cloning, and Metrics."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_case_notes_lifecycle_and_immutability(client: AsyncClient, supervisor_user: dict):
    headers = supervisor_user["headers"]

    # 1. Create Case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Case for Clinical Documentation", "case_type": "PREVENTION"},
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Draft Case Note
    note_payload = {
        "subject": "Home Safety Checkup",
        "content": "Conducted face to face home visit with caregiver and child.",
        "note_type": "Progress Note",
        "contact_type": "FACE_TO_FACE",
        "location": "COMMUNITY_HOME",
        "duration_minutes": 45,
        "is_well_child_checkup": True,
        "appointment_status": "ATTENDED",
        "next_appointment_at": "2026-09-15T10:00:00Z",
        "notify_team": True,
        "status": "DRAFT",
    }
    create_note_res = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json=note_payload,
        headers=headers,
    )
    assert create_note_res.status_code == 201
    note = create_note_res.json()
    note_id = note["id"]
    assert note["status"] == "DRAFT"
    assert note["is_locked"] is False
    assert note["contact_type"] == "FACE_TO_FACE"
    assert note["duration_minutes"] == 45

    # 3. Update Draft Note
    update_res = await client.patch(
        f"/api/v1/case-notes/{note_id}",
        json={"duration_minutes": 60},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["duration_minutes"] == 60

    # 4. Complete Note
    complete_res = await client.post(f"/api/v1/case-notes/{note_id}/complete", headers=headers)
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"

    # 5. Lock Note (Legal Immutability)
    lock_res = await client.post(f"/api/v1/case-notes/{note_id}/lock", headers=headers)
    assert lock_res.status_code == 200
    locked_note = lock_res.json()
    assert locked_note["is_locked"] is True
    assert locked_note["status"] == "LOCKED"
    assert locked_note["locked_at"] is not None

    # 6. Attempt to mutate locked note (Must be rejected with 409 Conflict)
    mutate_res = await client.patch(
        f"/api/v1/case-notes/{note_id}",
        json={"content": "Attempting to change locked narrative!"},
        headers=headers,
    )
    assert mutate_res.status_code == 409
    assert "legally locked and immutable" in mutate_res.text

    # 7. Add Addendum to Locked Note
    addendum_payload = {
        "content": "Correction: Caregiver confirmed subsequent medical follow-up was completed.",
        "reason": "Clarification of medical visit timeline.",
    }
    addendum_res = await client.post(
        f"/api/v1/case-notes/{note_id}/addenda",
        json=addendum_payload,
        headers=headers,
    )
    assert addendum_res.status_code == 201
    addendum = addendum_res.json()
    assert addendum["content"] == addendum_payload["content"]

    # Verify Note Details now include the Addendum
    note_details = await client.get(f"/api/v1/case-notes/{note_id}", headers=headers)
    assert note_details.status_code == 200
    assert len(note_details.json()["addenda"]) == 1

    # 8. Clone Note
    clone_res = await client.post(f"/api/v1/case-notes/{note_id}/clone", headers=headers)
    assert clone_res.status_code == 201
    cloned_note = clone_res.json()
    assert cloned_note["id"] != note_id
    assert cloned_note["status"] == "DRAFT"
    assert cloned_note["is_locked"] is False
    assert cloned_note["contact_type"] == "FACE_TO_FACE"
    assert cloned_note["content"] == ""  # Narrative is not blindly duplicated

    # 9. Attendance and Service Metrics
    metrics_res = await client.get(f"/api/v1/cases/{case_id}/notes/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_notes"] >= 2
    assert metrics["attendance"]["attended"] >= 1
    assert "FACE_TO_FACE" in metrics["contact_types"]

    # 10. Export Notes to CSV
    export_res = await client.get(f"/api/v1/cases/{case_id}/notes/export", headers=headers)
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert "Home Safety Checkup" in export_res.text
