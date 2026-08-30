"""Health check and configuration lookup test suite."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import LookupList, LookupValue


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "CRBCL Platform"
    assert "status" in data


@pytest.mark.asyncio
async def test_get_lookups_endpoint(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    # Setup lookup list and items
    ll = LookupList(key="case_statuses", name="Case Statuses", is_system=True, is_active=True)
    db_session.add(ll)
    await db_session.flush()

    v1 = LookupValue(list_id=ll.id, key="Open", label="Open", sort_order=1, is_active=True)
    v2 = LookupValue(list_id=ll.id, key="Closed", label="Closed", sort_order=2, is_active=True)
    v3_inactive = LookupValue(list_id=ll.id, key="Archived", label="Archived", sort_order=3, is_active=False)
    db_session.add_all([v1, v2, v3_inactive])
    await db_session.commit()

    response = await client.get("/api/v1/lookups/case_statuses", headers=caseworker_user["headers"])
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2  # Only active items returned
    assert items[0]["key"] == "Open"
    assert items[1]["key"] == "Closed"
