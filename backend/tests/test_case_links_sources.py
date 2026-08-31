"""Tests for Case Cross-Links, Sources (Other & Collateral), and External Workers."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_case_links_and_sources(client: AsyncClient, supervisor_user: dict):
    headers = supervisor_user["headers"]

    # 1. Create Case A and Case B
    case_a_res = await client.post(
        "/api/v1/cases",
        json={"title": "Primary Sibling Matter A", "case_type": "PROTECTION"},
        headers=headers,
    )
    assert case_a_res.status_code == 201
    case_a_id = case_a_res.json()["id"]

    case_b_res = await client.post(
        "/api/v1/cases",
        json={"title": "Linked Sibling Matter B", "case_type": "PROTECTION"},
        headers=headers,
    )
    assert case_b_res.status_code == 201
    case_b_id = case_b_res.json()["id"]

    # 2. Prevent Self-Link
    self_link_res = await client.post(
        f"/api/v1/cases/{case_a_id}/links",
        json={"target_case_id": case_a_id, "link_type": "same_incident"},
        headers=headers,
    )
    assert self_link_res.status_code == 400
    assert "Cannot link a case to itself" in self_link_res.text

    # 3. Create Valid Case Link
    link_res = await client.post(
        f"/api/v1/cases/{case_a_id}/links",
        json={
            "target_case_id": case_b_id,
            "link_type": "sibling_matter",
            "reason": "Concurrent matter involving sibling residing in separate household.",
        },
        headers=headers,
    )
    assert link_res.status_code == 201
    link = link_res.json()
    assert link["link_type"] == "sibling_matter"

    # 4. Prevent Duplicate Link
    dup_link_res = await client.post(
        f"/api/v1/cases/{case_a_id}/links",
        json={"target_case_id": case_b_id, "link_type": "sibling_matter"},
        headers=headers,
    )
    assert dup_link_res.status_code == 400
    assert "already linked" in dup_link_res.text

    # 5. Add Other Source (Grandmother)
    other_src_res = await client.post(
        f"/api/v1/cases/{case_a_id}/sources",
        json={
            "category": "OTHER_SOURCE",
            "name": "Evelyn Red Bear",
            "relationship_or_role": "Maternal Grandmother",
            "phone": "306-555-0199",
            "notes": "Key family wellness support provider.",
        },
        headers=headers,
    )
    assert other_src_res.status_code == 201
    assert other_src_res.json()["category"] == "OTHER_SOURCE"

    # 6. Add Collateral Source (Therapist / Provider)
    collateral_src_res = await client.post(
        f"/api/v1/cases/{case_a_id}/sources",
        json={
            "category": "COLLATERAL_SOURCE",
            "name": "Dr. Sarah Adams",
            "relationship_or_role": "Child Clinical Psychologist",
            "organization": "Qu'Appelle Health Region",
            "phone": "306-555-0188",
        },
        headers=headers,
    )
    assert collateral_src_res.status_code == 201
    assert collateral_src_res.json()["category"] == "COLLATERAL_SOURCE"

    # 7. Add External Worker (Band Representative)
    ext_worker_res = await client.post(
        f"/api/v1/cases/{case_a_id}/external-workers",
        json={
            "name": "Thomas Starblanket",
            "organization": "Muscowpetung Band Office",
            "role": "First Nation Child Welfare Band Representative",
            "phone": "306-555-0122",
            "email": "t.starblanket@muscowpetung.ca",
        },
        headers=headers,
    )
    assert ext_worker_res.status_code == 201
    assert ext_worker_res.json()["name"] == "Thomas Starblanket"
