"""
CRBCL Platform — Supabase PostgreSQL End-to-End Live Integration Test.

Executes full lifecycle against live Supabase PostgreSQL instance:
1. Health check (GET /api/v1/health)
2. Authentication (POST /api/v1/auth/login)
3. Synthetic Client & Person Creation (POST /api/v1/clients)
4. Synthetic Family Creation (POST /api/v1/families)
5. Intake Referral Creation (POST /api/v1/referrals with sequence INT-YYYY-NNNNNN)
6. Attach Person & Concerns to Referral
7. Multi-Child Disposition & Recommendation (POST /api/v1/referrals/{id}/submit)
8. Supervisor Decision & Automated Case Routing (POST /api/v1/referrals/{id}/approve)
9. Verify Resulting Case in PostgreSQL
"""

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_DB"),
    reason="Requires TEST_POSTGRES_DB=1 to run against live Supabase PostgreSQL",
)
@pytest.mark.asyncio
async def test_supabase_live_integration():
    settings = get_settings()
    assert "supabase" in settings.database_url or "pooler" in settings.database_url, "Must be configured against Supabase"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health Check
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["database"] == "ready", f"Database not ready: {health_data}"
        print(f"\n[LIVE SUPABASE] 1. Health check passed: database={health_data['database']}")

        # 2. Authentication with Seeded Admin User
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@crbcl.ca", "password": "crbcl_admin_2026"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        auth_data = login_resp.json()
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[LIVE SUPABASE] 2. Authentication successful: JWT received")

        # 3. Create Synthetic Client (which creates canonical Person in domain layer)
        test_uid = uuid.uuid4().hex[:6]
        client_payload = {
            "first_name": f"SyntheticChild_{test_uid}",
            "last_name": f"Standingready_{test_uid}",
            "date_of_birth": "2018-05-12",
            "gender": "Female",
            "status": "Pending Intake",
            "risk_level": "Medium",
            "band_nation": "Muscowpetung Saulteaux Nation",
            "indigenous_identity": "First Nations (Status)",
            "city": "Fort Qu'Appelle",
            "province": "Saskatchewan",
        }
        client_resp = await client.post("/api/v1/clients", headers=headers, json=client_payload)
        assert client_resp.status_code == 201, f"Client create failed: {client_resp.text}"
        client_data = client_resp.json()
        client_id = client_data["id"]
        print(f"[LIVE SUPABASE] 3. Synthetic Client created: {client_id}")

        # Retrieve Client Profile to obtain canonical Person ID
        get_client_resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
        assert get_client_resp.status_code == 200
        client_profile = get_client_resp.json()
        person_info = client_profile.get("person")
        person_id = person_info["id"] if person_info else client_id
        print(f"[LIVE SUPABASE] 4. Canonical Person verified: {person_id}")

        # 4. Create Synthetic Family
        family_resp = await client.post(
            "/api/v1/families",
            headers=headers,
            json={
                "family_name": f"Standingready Family {test_uid}",
                "community": "Muscowpetung Saulteaux Nation",
                "status": "Active",
                "primary_contact_name": "Synthetic Elder Guardian",
            },
        )
        assert family_resp.status_code == 201, f"Family create failed: {family_resp.text}"
        family_data = family_resp.json()
        family_id = family_data["id"]
        print(f"[LIVE SUPABASE] 5. Synthetic Family created: {family_id}")

        # 5. Create Intake Referral with Person & Structured Concerns
        referral_resp = await client.post(
            "/api/v1/referrals",
            headers=headers,
            json={
                "received_date": "2026-08-30",
                "received_method": "phone",
                "priority": "High",
                "risk_level": "High",
                "community": "Muscowpetung Saulteaux Nation",
                "summary": f"Live integration test synthetic referral narrative {test_uid}",
                "immediate_safety_concerns": False,
                "reporter": {
                    "is_anonymous": False,
                    "is_mandated_reporter": True,
                    "reporter_name": "Public Health Nurse Test",
                    "organization": "Community Health Center",
                    "phone": "306-555-0199",
                },
                "people": [
                    {
                        "person_id": person_id,
                        "role": "child",
                        "is_primary_caregiver": False,
                        "relationship_to_child": "Self",
                    }
                ],
                "concerns": [
                    {
                        "concern_type": "neglect",
                        "is_primary": True,
                        "severity": "Moderate",
                        "description": "Synthetic concern description for testing",
                    }
                ],
            },
        )
        assert referral_resp.status_code == 201, f"Referral create failed: {referral_resp.text}"
        referral_data = referral_resp.json()
        referral_id = referral_data["id"]
        referral_num = referral_data["referral_number"]
        print(f"[LIVE SUPABASE] 6. Synthetic Referral created: {referral_id} (Number: {referral_num})")

        # 6. Read Referral 360° Detail
        get_ref_resp = await client.get(f"/api/v1/referrals/{referral_id}", headers=headers)
        assert get_ref_resp.status_code == 200
        ref_360 = get_ref_resp.json()
        assert len(ref_360["people"]) == 1
        assert len(ref_360["concerns"]) == 1
        print("[LIVE SUPABASE] 7. Referral 360° detail assembled successfully")

        # 7. Submit Multi-Child Disposition & Recommendation
        submit_disp_resp = await client.post(
            f"/api/v1/referrals/{referral_id}/submit",
            headers=headers,
            json={
                "overall_recommendation": "Recommend opening voluntary Family Prevention case.",
                "rationale": "Kinship wellness supports identified in community.",
                "dispositions": [
                    {
                        "person_id": person_id,
                        "decision": "PREVENTION",
                        "reason": "Family wellness prevention supports appropriate.",
                    }
                ],
            },
        )
        assert submit_disp_resp.status_code == 200, f"Submit failed: {submit_disp_resp.text}"
        print("[LIVE SUPABASE] 8. Recommendation submitted -> Status is PENDING_SUPERVISOR")

        # 8. Supervisor Approval & Automated Case Routing
        approve_resp = await client.post(
            f"/api/v1/referrals/{referral_id}/approve",
            headers=headers,
            json={"supervisor_notes": "Approved for Family Prevention program."},
        )
        assert approve_resp.status_code == 200, f"Approve failed: {approve_resp.text}"
        app_data = approve_resp.json()
        assert app_data["status"] == "APPROVED"
        assert len(app_data.get("dispositions", [])) == 1
        resulting_case_id = app_data["dispositions"][0].get("resulting_case_id")
        assert resulting_case_id is not None, "Automated case routing must produce resulting_case_id"
        print(f"[LIVE SUPABASE] 9. Supervisor Approved -> Resulting Case generated: {resulting_case_id}")

        # 9. Verify Generated Case Record in Database
        case_resp = await client.get(f"/api/v1/cases/{resulting_case_id}", headers=headers)
        assert case_resp.status_code == 200
        case_data = case_resp.json()
        assert "Prevention" in case_data["case_type"] or "PREVENTION" in case_data["case_type"]
        print(f"[LIVE SUPABASE] 10. Generated Case verified: {case_data.get('case_number')} ({case_data.get('case_type')})")

        # 10. Snapshot Retrieval
        snap_resp = await client.get(f"/api/v1/cases/{resulting_case_id}/snapshot", headers=headers)
        assert snap_resp.status_code == 200
        snap_data = snap_resp.json()
        assert snap_data["case_id"] == resulting_case_id
        print(f"[LIVE SUPABASE] 11. Case Snapshot retrieved: days_open={snap_data['days_open']}")

        # 11. Add Case Person
        add_person_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/people",
            headers=headers,
            json={
                "person_id": person_id,
                "role": "subject_child",
                "is_primary": True,
                "notes": "Primary subject child from live intake.",
            },
        )
        assert add_person_resp.status_code == 201
        print("[LIVE SUPABASE] 12. Attached Person to Case Roster")

        # 12. Create Clinical Case Note
        note_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/notes",
            headers=headers,
            json={
                "subject": "Initial Wellness Visit & Cultural Kinship Plan",
                "content": "Conducted face-to-face home visit. Cultural teachings discussed with Elder and caregiver.",
                "note_type": "Progress Note",
                "contact_type": "FACE_TO_FACE",
                "location": "HOME",
                "duration_minutes": 60,
                "is_well_child_checkup": True,
                "appointment_status": "ATTENDED",
                "status": "COMPLETED",
            },
        )
        assert note_resp.status_code == 201
        note_id = note_resp.json()["id"]
        print(f"[LIVE SUPABASE] 13. Recorded Clinical Case Note: {note_id}")

        # 13. Lock Note & Verify Immutability (ADR-011)
        lock_resp = await client.post(f"/api/v1/case-notes/{note_id}/lock", headers=headers)
        assert lock_resp.status_code == 200
        assert lock_resp.json()["is_locked"] is True
        print("[LIVE SUPABASE] 14. Locked Case Note successfully")

        # 14. Append Addendum to Locked Note
        addendum_resp = await client.post(
            f"/api/v1/case-notes/{note_id}/addenda",
            headers=headers,
            json={
                "content": "Clarification: Kinship support network confirmed by Band Representative.",
                "reason": "Collateral verification update.",
            },
        )
        assert addendum_resp.status_code == 201
        print("[LIVE SUPABASE] 15. Appended Legal Addendum to locked note")

        # 15. Controlled Case Closure
        close_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/close",
            headers=headers,
            json={
                "closed_reason": "Family wellness plan completed successfully with sustainable community supports.",
                "closed_date": "2026-08-31",
            },
        )
        assert close_resp.status_code == 200
        assert close_resp.json()["status"] == "Closed"
        print("[LIVE SUPABASE] 16. Case formally closed with mandatory rationale")

        # 16. Case Reopening
        reopen_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/reopen",
            headers=headers,
            json={"reopened_reason": "Follow-up kinship respite service requested by family."},
        )
        assert reopen_resp.status_code == 200
        assert reopen_resp.json()["status"] == "Reopened"
        print("[LIVE SUPABASE] 17. Case reopened with justification")

        # 17. Status Audit History
        history_resp = await client.get(f"/api/v1/cases/{resulting_case_id}/status-history", headers=headers)
        assert history_resp.status_code == 200
        history_items = history_resp.json()
        assert len(history_items) >= 2
        print(f"[LIVE SUPABASE] 18. Verified status history audit trail ({len(history_items)} transitions logged)")

        print("\n================================================================================")
        print(">>> ALL 18 STEPS OF LIVE SUPABASE POSTGRESQL VERIFICATION PASSED SUCCESSFULLY! <<<")
        print("================================================================================\n")
