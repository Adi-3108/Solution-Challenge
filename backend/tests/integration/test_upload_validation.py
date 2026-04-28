from __future__ import annotations

from pathlib import Path

from httpx import AsyncClient


async def create_project(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "validator@test.dev", "password": "Demo1234!", "role": "analyst"},
    )
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Validation project", "description": "Validation test"},
    )
    return str(response.json()["data"]["id"])


async def test_malformed_file_upload_is_rejected(client: AsyncClient, fixtures_path: Path) -> None:
    project_id = await create_project(client)
    malformed = fixtures_path / "malformed.csv"
    with malformed.open("rb") as handle:
      response = await client.post(
          f"/api/v1/projects/{project_id}/datasets",
          files={"file": ("malformed.csv", handle.read(), "text/csv")},
          data={
              "target_column": "approved",
              "protected_columns": '["gender"]',
              "positive_label": "1",
          },
      )
    assert response.status_code == 400

