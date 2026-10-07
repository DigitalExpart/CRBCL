"""Automated test suite for User Preferences & Personalization security boundaries."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_unauthenticated_preferences_rejected(client: AsyncClient):
    """Ensure preference endpoints strictly require authentication."""
    get_res = await client.get("/api/v1/users/me/preferences")
    assert get_res.status_code == 401

    put_res = await client.put(
        "/api/v1/users/me/preferences",
        json={"appearance": {"theme_mode": "dark"}},
    )
    assert put_res.status_code == 401


@pytest.mark.asyncio
async def test_default_preferences_returned(client: AsyncClient, caseworker_user):
    """Ensure default preferences are returned if none are explicitly set."""
    res = await client.get("/api/v1/users/me/preferences", headers=caseworker_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "appearance" in data
    app = data["appearance"]
    assert app["theme_mode"] == "system"
    assert app["accent_theme"] == "crbcl"
    assert app["density"] == "comfortable"
    assert app["card_radius"] == "rounded"
    assert app["sidebar_collapsed"] is False
    assert app["reduced_motion"] is False
    assert app["high_contrast"] is False
    assert app["default_landing_dashboard"] is None


@pytest.mark.asyncio
async def test_update_preferences_success_and_persisted(client: AsyncClient, caseworker_user):
    """Ensure authenticated user can update valid appearance preferences and they persist."""
    payload = {
        "appearance": {
            "theme_mode": "dark",
            "accent_theme": "forest",
            "density": "compact",
            "sidebar_collapsed": True,
            "card_radius": "subtle",
            "reduced_motion": True,
            "high_contrast": True,
            "default_landing_dashboard": "/dashboard",
        },
        "dashboard_widgets": [{"widget_key": "active_cases", "position": 0, "is_visible": True}],
    }

    put_res = await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json=payload,
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["appearance"]["theme_mode"] == "dark"
    assert updated["appearance"]["accent_theme"] == "forest"
    assert updated["appearance"]["density"] == "compact"
    assert updated["appearance"]["sidebar_collapsed"] is True
    assert updated["appearance"]["card_radius"] == "subtle"
    assert updated["appearance"]["reduced_motion"] is True
    assert updated["appearance"]["high_contrast"] is True
    assert updated["appearance"]["default_landing_dashboard"] == "/dashboard"

    # Verify persisted via GET
    get_res = await client.get("/api/v1/users/me/preferences", headers=caseworker_user["headers"])
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["appearance"]["theme_mode"] == "dark"
    assert get_data["appearance"]["accent_theme"] == "forest"
    assert len(get_data["dashboard_widgets"]) == 1


@pytest.mark.asyncio
async def test_auth_me_includes_preferences(client: AsyncClient, caseworker_user):
    """Ensure GET /auth/me returns preferences dictionary without requiring extra round-trip."""
    # Set preferences first
    payload = {
        "appearance": {
            "theme_mode": "light",
            "accent_theme": "prairie",
            "density": "comfortable",
            "sidebar_collapsed": False,
            "card_radius": "rounded",
            "reduced_motion": False,
            "high_contrast": False,
            "default_landing_dashboard": None,
        }
    }
    await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json=payload,
    )

    me_res = await client.get("/api/v1/auth/me", headers=caseworker_user["headers"])
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "preferences" in me_data
    assert "appearance" in me_data["preferences"]
    assert me_data["preferences"]["appearance"]["accent_theme"] == "prairie"
    assert me_data["preferences"]["appearance"]["theme_mode"] == "light"


@pytest.mark.asyncio
async def test_invalid_preferences_rejected(client: AsyncClient, caseworker_user):
    """Ensure invalid theme modes, accents, and dangerous payloads are rejected (HTTP 422)."""
    # 1. Invalid theme mode
    res1 = await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"theme_mode": "neon_rainbow"}},
    )
    assert res1.status_code == 422

    # 2. Invalid accent palette
    res2 = await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"accent_theme": "hot_pink"}},
    )
    assert res2.status_code == 422

    # 3. Disallowed script / HTML injection in default_landing_dashboard
    res3 = await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"default_landing_dashboard": "<script>alert(1)</script>"}},
    )
    assert res3.status_code == 422

    # 4. Extra unapproved keys forbidden (no arbitrary CSS / JS)
    res4 = await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"theme_mode": "dark"}, "arbitrary_css": "body { display: none; }"},
    )
    assert res4.status_code == 422


@pytest.mark.asyncio
async def test_user_isolation_preferences(client: AsyncClient, db_session: AsyncSession, caseworker_user):
    """Ensure User A's appearance customization never mutates User B's settings."""
    from app.auth.security import create_access_token

    # Create User B
    user_b = User(
        email="secondworker@crbcl.ca",
        email_normalized="secondworker@crbcl.ca",
        password_hash=hash_password("Secret123!"),
        full_name="Second Caseworker",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token(user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A sets accent to 'burgundy'
    await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"accent_theme": "burgundy", "theme_mode": "dark"}},
    )

    # User B queries preferences - should be default, unaffected by User A
    res_b = await client.get("/api/v1/users/me/preferences", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["appearance"]["accent_theme"] == "crbcl"
    assert data_b["appearance"]["theme_mode"] == "system"


@pytest.mark.asyncio
async def test_preferences_never_alter_rbac(client: AsyncClient, caseworker_user):
    """Critical security test: Setting a landing dashboard or widget layout MUST NEVER grant RBAC access."""
    # Caseworker sets landing preference to an IT Admin area
    await client.put(
        "/api/v1/users/me/preferences",
        headers=caseworker_user["headers"],
        json={"appearance": {"default_landing_dashboard": "/admin/dashboards"}},
    )

    # Attempt to access IT Admin dashboard registry endpoint as caseworker
    res = await client.get("/api/v1/admin/dashboards", headers=caseworker_user["headers"])
    # Must be forbidden (403)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_new_color_palettes_accepted(client: AsyncClient, caseworker_user):
    """Ensure Pink, Light Pink, Purple, Light Purple, Sky Blue, and Yellow palettes are accepted and normalized."""
    test_cases = [
        ("pink", "pink"),
        ("light-pink", "light-pink"),
        ("light_pink", "light-pink"),
        ("purple", "purple"),
        ("light-purple", "light-purple"),
        ("light_purple", "light-purple"),
        ("sky-blue", "sky-blue"),
        ("sky_blue", "sky-blue"),
        ("yellow", "yellow"),
    ]
    for input_val, expected_val in test_cases:
        res = await client.put(
            "/api/v1/users/me/preferences",
            headers=caseworker_user["headers"],
            json={"appearance": {"accent_theme": input_val}},
        )
        assert res.status_code == 200, f"Failed for palette {input_val}: {res.text}"
        data = res.json()
        assert data["appearance"]["accent_theme"] == expected_val
