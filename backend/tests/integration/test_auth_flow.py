from __future__ import annotations

from httpx import AsyncClient


async def test_auth_flow_register_login_me_logout(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "analyst@test.dev", "password": "Demo1234!", "role": "analyst"},
    )
    assert register_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@test.dev", "password": "Demo1234!"},
    )
    assert login_response.status_code == 200

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == "analyst@test.dev"

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200


async def test_invalid_access_token_returns_401_not_500(client: AsyncClient) -> None:
    client.cookies.set("fairsight_access_token", "invalid-token")
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_invalid_reset_token_returns_400(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password/confirm",
        json={"token": "invalid-token", "new_password": "Demo1234!"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_token"


async def test_cors_allows_local_preview_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://localhost:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"
