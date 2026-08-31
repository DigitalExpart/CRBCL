"""Tests for Court Events, Hearings, Orders, and Band Representation."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_court_events_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Talia", "last_name": "Pelly", "date_of_birth": "2014-06-11", "gender": "Female"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Pelly Legal Custody Case", "case_type": "Child Protection", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Record court hearing event
    court_payload = {
        "child_id": child_id,
        "hearing_type": "BAND_REPRESENTATION_HEARING",
        "court_docket_number": "YKT-CIV-2026-0442",
        "court_location": "Yorkton Provincial Court",
        "judge_name": "Judge H. Morrison",
        "hearing_date": "2026-08-25",
        "hearing_time": "10:00:00",
        "outcome_summary": "Band representative made oral submissions affirming Customary Care plan.",
        "orders_issued": "Temporary custody granted to Cote First Nation Customary Care Lodge for 6 months.",
        "legal_counsel_info": "Ms. D. Keshane (Band Counsel) & Mr. G. Taylor (Crown Counsel)",
        "band_representative_present": True,
        "next_court_date": "2027-02-25",
        "status": "COMPLETED",
    }
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/court-events",
        headers=headers,
        json=court_payload,
    )
    assert create_res.status_code == 201
    event = create_res.json()
    event_id = event["id"]
    assert event["hearing_type"] == "BAND_REPRESENTATION_HEARING"
    assert event["band_representative_present"] is True
    assert event["court_docket_number"] == "YKT-CIV-2026-0442"

    # 3. Retrieve court event
    get_res = await client.get(f"/api/v1/court-events/{event_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["judge_name"] == "Judge H. Morrison"

    # 4. Update court event
    update_res = await client.patch(
        f"/api/v1/court-events/{event_id}",
        headers=headers,
        json={"outcome_summary": "Formal written order signed and sealed by the presiding judge."},
    )
    assert update_res.status_code == 200
    assert "Formal written order" in update_res.json()["outcome_summary"]

    # 5. List court events for the case
    list_res = await client.get(f"/api/v1/cases/{case_id}/court-events", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert any(e["id"] == event_id for e in data["items"])
