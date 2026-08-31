"""Tests for Phase 6 Cryptographic Signatures, Document Hashing, and Physical Attestation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cryptographic_signatures_and_attestation(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Dakota", "last_name": "Redman", "date_of_birth": "2016-03-22", "gender": "Female"},
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Redman Safety Plan Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Plan
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/plans",
        headers=headers,
        json={
            "case_id": case_id,
            "primary_person_id": person_id,
            "plan_type": "SAFETY_PLAN",
            "title": "Redman Immediate Kinship Safety Agreement",
            "meeting_date": "2026-08-31T11:00:00Z",
            "narrative": "Aunt Sarah will provide protective supervision at residence.",
            "goals": [{"goal_text": "Maintain safe sober household environment."}],
        },
    )
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]

    # 3. Attempt signature while still in DRAFT -> MUST fail
    fail_sig = await client.post(
        f"/api/v1/plans/{plan_id}/signatures",
        headers=headers,
        json={
            "signer_type": "WORKER",
            "signer_name": "Caseworker Dan",
            "signer_role": "Primary Worker",
            "signature_data": "data:image/svg+xml;base64,sig1",
        },
    )
    assert fail_sig.status_code == 400
    assert "FINALIZED" in fail_sig.text

    # 4. Finalize Plan -> generates SHA-256 hash
    fin_res = await client.post(f"/api/v1/plans/{plan_id}/finalize", headers=headers, json={})
    assert fin_res.status_code == 200
    doc_hash = fin_res.json()["current_version"]["document_hash"]
    assert doc_hash is not None and len(doc_hash) == 64

    # 5. Worker signs electronically
    worker_sig = await client.post(
        f"/api/v1/plans/{plan_id}/signatures",
        headers=headers,
        json={
            "signer_type": "WORKER",
            "signer_name": "Caseworker Dan",
            "signer_role": "Primary Worker",
            "signature_data": "data:image/svg+xml;base64,worker_sig",
            "method": "ELECTRONIC_DRAW",
            "attestation_text": "I agree with this safety plan and will provide supportive case management.",
        },
    )
    assert worker_sig.status_code == 201
    w_data = worker_sig.json()
    assert w_data["document_hash"] == doc_hash
    assert w_data["signer_name"] == "Caseworker Dan"

    # 6. Caregiver/Aunt signs electronically
    caregiver_sig = await client.post(
        f"/api/v1/plans/{plan_id}/signatures",
        headers=headers,
        json={
            "signer_type": "PARENT_GUARDIAN",
            "signer_name": "Aunt Sarah Redman",
            "signer_role": "Kinship Caregiver",
            "signature_data": "data:image/svg+xml;base64,caregiver_sig",
            "method": "ELECTRONIC_DRAW",
            "attestation_text": "I agree to provide 24/7 sober supervision for Dakota.",
        },
    )
    assert caregiver_sig.status_code == 201
    c_data = caregiver_sig.json()
    assert c_data["document_hash"] == doc_hash

    # 7. Attach Physical Scanned Signature Document
    phys_sig = await client.post(
        f"/api/v1/plans/{plan_id}/physical-signature",
        headers=headers,
        json={
            "signer_name": "Elder George Redman",
            "signer_role": "Community Elder Witness",
            "signer_type": "ELDER",
            "document_url": "https://storage.crbcl.ca/documents/signed_plan_scan_001.pdf",
            "notes": "Elder signed paper copy in community hall.",
        },
    )
    assert phys_sig.status_code == 201
    p_data = phys_sig.json()
    assert p_data["method"] == "PHYSICAL_UPLOAD"
    assert p_data["signature_image_url"] == "https://storage.crbcl.ca/documents/signed_plan_scan_001.pdf"

    # 8. Fetch plan and verify all 3 signatures
    detail_res = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert detail_res.status_code == 200
    sigs = detail_res.json()["current_version"]["signatures"]
    assert len(sigs) == 3
