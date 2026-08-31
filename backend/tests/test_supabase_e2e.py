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

        # =====================================================================
        # PHASE 5: CONFIGURABLE ASSESSMENT ENGINE (HOME, THREAT, AIEI)
        # =====================================================================

        # 18. List Published Assessment Templates
        tmpl_list_resp = await client.get("/api/v1/assessment-templates", headers=headers)
        assert tmpl_list_resp.status_code == 200
        templates = tmpl_list_resp.json()
        template_keys = [t["key"] for t in templates]
        assert "HOME_ASSESSMENT" in template_keys
        assert "THREAT_ASSESSMENT" in template_keys
        assert "AIEI_ASSESSMENT" in template_keys
        print(f"[LIVE SUPABASE] 19. Assessment Templates verified: {template_keys}")

        # 19. Initiate Home Assessment
        home_init_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/assessments",
            headers=headers,
            json={
                "case_id": resulting_case_id,
                "template_key": "HOME_ASSESSMENT",
                "person_id": person_id,
                "title": "Live Supabase E2E Home Safety Assessment",
            },
        )
        assert home_init_resp.status_code == 201
        home_asm = home_init_resp.json()
        home_asm_id = home_asm["id"]
        assert home_asm["assessment_number"].startswith("ASM-")
        print(f"[LIVE SUPABASE] 20. Initiated Home Assessment: {home_asm['assessment_number']}")

        # 20. Save Home Assessment Answers
        home_answers_payload = {
            "answers": [
                {"question_key": "substance_use_detected", "boolean_value": False},
                {"question_key": "hazardous_chemicals", "boolean_value": False},
                {"question_key": "sanitation_concerns", "boolean_value": False},
                {"question_key": "broken_windows", "boolean_value": False},
                {"question_key": "running_water", "boolean_value": True},
                {"question_key": "adequate_heat", "boolean_value": True},
                {"question_key": "overcrowding", "boolean_value": False},
                {"question_key": "structural_concerns", "boolean_value": False},
                {"question_key": "recognizes_hazards", "boolean_value": True},
                {"question_key": "willing_to_remedy", "boolean_value": True},
                {"question_key": "support_network_present", "boolean_value": True},
                {"question_key": "home_safety_outcome", "selected_option_keys": ["CHILD_SAFE_AT_HOME"]},
                {"question_key": "physical_condition_notes", "text_value": "Clean and well-maintained family home."},
            ]
        }
        save_home_resp = await client.put(
            f"/api/v1/assessments/{home_asm_id}/answers",
            headers=headers,
            json=home_answers_payload,
        )
        assert save_home_resp.status_code == 200, f"Failed saving home answers: {save_home_resp.text}"
        print("[LIVE SUPABASE] 21. Saved Home Assessment structured answers")

        # 21. Complete Home Assessment
        comp_home_resp = await client.post(
            f"/api/v1/assessments/{home_asm_id}/complete",
            headers=headers,
            json={
                "determination": "SAFE_WITH_SERVICES",
                "clinical_summary": "Residence is safe and suitable with active family support.",
                "action_recommendations": "Provide standard community wellness drop-in support.",
            },
        )
        assert comp_home_resp.status_code == 200, f"Failed completing home assessment: {comp_home_resp.text}"
        assert comp_home_resp.json()["status"] == "COMPLETED"
        print("[LIVE SUPABASE] 22. Completed Home Assessment with SAFE_WITH_SERVICES determination")

        # 22. Initiate Threat Assessment
        threat_init_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/assessments",
            headers=headers,
            json={
                "case_id": resulting_case_id,
                "template_key": "THREAT_ASSESSMENT",
                "person_id": person_id,
                "title": "Live Supabase E2E Threat & Danger Screening",
            },
        )
        assert threat_init_resp.status_code == 201, f"Failed creating threat assessment: {threat_init_resp.text}"
        threat_asm = threat_init_resp.json()
        threat_asm_id = threat_asm["id"]
        print(f"[LIVE SUPABASE] 23. Initiated Threat Assessment: {threat_asm['assessment_number']}")

        # 23. Save Threat Assessment Answers & Check Deterministic Indicators
        threat_answers_payload = {
            "answers": [
                {"question_key": "immediate_physical_harm", "boolean_value": False},
                {"question_key": "caregiver_incapacitated", "boolean_value": False},
                {"question_key": "child_in_acute_peril", "boolean_value": False},
                {"question_key": "present_danger_notes", "text_value": "No present danger threats observed."},
                {"question_key": "uncontrolled_escalating_threat", "boolean_value": False},
                {"question_key": "vulnerable_child", "boolean_value": False},
                {"question_key": "impending_danger_notes", "text_value": "No impending danger identified."},
                {"question_key": "kinship_safety_placement", "boolean_value": True},
                {"question_key": "community_supports_active", "boolean_value": True},
                {"question_key": "intervention_details", "text_value": "Elder kinship circle actively engaged and monitoring."},
                {"question_key": "threat_determination_outcome", "selected_option_keys": ["SAFE"]},
                {"question_key": "clinical_safety_rationale", "text_value": "No active threats. Elder kinship circle providing protective support."},
            ]
        }
        save_threat_resp = await client.put(
            f"/api/v1/assessments/{threat_asm_id}/answers",
            headers=headers,
            json=threat_answers_payload,
        )
        assert save_threat_resp.status_code == 200, f"Failed saving threat answers: {save_threat_resp.text}"
        threat_detail = save_threat_resp.json()
        ind_summary = threat_detail.get("indicator_summary", {})
        assert ind_summary.get("protective_capacities_count", 0) >= 1
        print(f"[LIVE SUPABASE] 24. Saved Threat Assessment answers. Deterministic indicator summary: {ind_summary}")

        # 24. Lock Assessment (Governance & Immutability)
        lock_asm_resp = await client.post(
            f"/api/v1/assessments/{home_asm_id}/lock",
            headers=headers,
            json={"reason": "Formal clinical sign-off complete."},
        )
        assert lock_asm_resp.status_code == 200
        assert lock_asm_resp.json()["status"] == "LOCKED"
        print("[LIVE SUPABASE] 25. Locked Home Assessment for immutability")

        # Verify mutation fails on locked assessment
        mut_fail_resp = await client.put(
            f"/api/v1/assessments/{home_asm_id}/answers",
            headers=headers,
            json={"answers": [{"question_key": "broken_windows", "boolean_value": True}]},
        )
        assert mut_fail_resp.status_code == 400
        print("[LIVE SUPABASE] 26. Verified locked assessment prohibits mutations (400 Bad Request)")

        # 25. Time-Series Delta Comparison (Follow-up Assessment)
        home_init_2_resp = await client.post(
            f"/api/v1/cases/{resulting_case_id}/assessments",
            headers=headers,
            json={
                "case_id": resulting_case_id,
                "template_key": "HOME_ASSESSMENT",
                "person_id": person_id,
                "title": "Live Supabase E2E Follow-up Home Inspection",
            },
        )
        assert home_init_2_resp.status_code == 201
        home_asm_2_id = home_init_2_resp.json()["id"]

        compare_resp = await client.get(
            f"/api/v1/assessments/compare?ids={home_asm_id},{home_asm_2_id}",
            headers=headers,
        )
        assert compare_resp.status_code == 200
        compare_data = compare_resp.json()
        assert len(compare_data["assessments"]) == 2
        print(f"[LIVE SUPABASE] 27. Cross-assessment time-series comparison verified ({len(compare_data['assessments'])} assessments compared)")

        # 26. Director Unlock with Mandatory Justification
        unlock_resp = await client.post(
            f"/api/v1/assessments/{home_asm_id}/unlock",
            headers=headers,
            json={"justification": "Director authorized correction of electrical hazard clarification."},
        )
        assert unlock_resp.status_code == 200
        assert unlock_resp.json()["status"] in ("COMPLETED", "IN_PROGRESS")
        print("[LIVE SUPABASE] 28. Director unlocked assessment with mandatory justification")

        print("\n================================================================================")
        print(">>> ALL 28 STEPS OF LIVE SUPABASE POSTGRESQL VERIFICATION PASSED SUCCESSFULLY! <<<")
        print("================================================================================\n")
