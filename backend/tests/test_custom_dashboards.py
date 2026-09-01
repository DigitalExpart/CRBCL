"""Tests for Role-Aware & Customizable User Dashboards (Phase 11)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_custom_user_dashboard_layout_and_widget_permissions(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    it_admin_user: dict,
):
    """Verify user widget layout persistence, drag/drop ordering, and capability checking."""
    # 1. Caseworker fetches custom dashboard
    res = await client.get("/api/v1/dashboard/user-layout", headers=caseworker_user["headers"])
    assert res.status_code == 200
    dash = res.json()
    assert "layout" in dash
    assert "metrics" in dash
    assert len(dash["layout"]) >= 1

    # 2. Caseworker saves customized widget layout order
    layout_data = [
        {"widget_key": "my_assigned_cases", "position": 0, "width": 2, "height": 1, "is_visible": True},
        {"widget_key": "active_cases", "position": 1, "width": 1, "height": 1, "is_visible": True},
        {"widget_key": "children_out_of_home", "position": 2, "width": 1, "height": 1, "is_visible": False},
    ]
    save_res = await client.post("/api/v1/dashboard/layout", json=layout_data, headers=caseworker_user["headers"])
    assert save_res.status_code == 200

    # 3. Re-querying user layout confirms updated order and visibility persist
    refetch = await client.get("/api/v1/dashboard/user-layout", headers=caseworker_user["headers"])
    assert refetch.status_code == 200
    new_layout = refetch.json()["layout"]

    my_cases_w = next(w for w in new_layout if w["widget_key"] == "my_assigned_cases")
    assert my_cases_w["position"] == 0

    hidden_w = next(w for w in new_layout if w["widget_key"] == "children_out_of_home")
    assert hidden_w["is_visible"] is False

    # 4. IT Admin without DASHBOARD_CUSTOMIZE permission -> HTTP 403
    it_res = await client.get("/api/v1/dashboard/user-layout", headers=it_admin_user["headers"])
    assert it_res.status_code == 403
