from __future__ import annotations

import json
from pathlib import Path

from httpx import AsyncClient


async def bootstrap_project(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "runner@test.dev", "password": "Demo1234!", "role": "analyst"},
    )
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Runner project", "description": "End to end audit flow"},
    )
    return str(response.json()["data"]["id"])


async def test_full_audit_flow(client: AsyncClient, fixtures_path: Path) -> None:
    project_id = await bootstrap_project(client)

    dataset_file = fixtures_path / "adult_census_biased.csv"
    with dataset_file.open("rb") as handle:
        upload_response = await client.post(
            f"/api/v1/projects/{project_id}/datasets",
            files={"file": ("adult_census_biased.csv", handle.read(), "text/csv")},
            data={
                "target_column": "hired",
                "protected_columns": '["gender","race"]',
                "positive_label": "1",
                "prediction_column": "predicted_hired",
                "score_column": "score",
            },
        )
    assert upload_response.status_code == 200
    dataset_id = upload_response.json()["data"]["id"]

    run_response = await client.post(
        f"/api/v1/projects/{project_id}/runs",
        json={"dataset_id": dataset_id},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["data"]["id"]

    results_response = await client.get(f"/api/v1/runs/{run_id}/results")
    assert results_response.status_code == 200
    assert results_response.json()["data"]["metrics"]

    report_response = await client.post(f"/api/v1/runs/{run_id}/report", json={"format": "json"})
    assert report_response.status_code == 200
    report_download = await client.get(f"/api/v1/runs/{run_id}/report/json")
    assert report_download.status_code == 200
    assert report_download.headers["content-type"].startswith("application/json")
    report_payload = json.loads(report_download.text)
    assert "counterfactual" in report_payload
    assert "drift" in report_payload


async def test_results_include_counterfactual_and_drift_history(
    client: AsyncClient,
    fixtures_path: Path,
) -> None:
    project_id = await bootstrap_project(client)

    first_dataset = fixtures_path / "adult_census_biased.csv"
    with first_dataset.open("rb") as handle:
        first_upload = await client.post(
            f"/api/v1/projects/{project_id}/datasets",
            files={"file": ("adult_census_biased.csv", handle.read(), "text/csv")},
            data={
                "target_column": "hired",
                "protected_columns": '["gender","race"]',
                "positive_label": "1",
                "prediction_column": "predicted_hired",
                "score_column": "score",
            },
        )
    first_dataset_id = first_upload.json()["data"]["id"]
    first_run = await client.post(
        f"/api/v1/projects/{project_id}/runs",
        json={"dataset_id": first_dataset_id},
    )
    assert first_run.status_code == 200

    second_dataset = fixtures_path / "synthetic_balanced.csv"
    with second_dataset.open("rb") as handle:
        second_upload = await client.post(
            f"/api/v1/projects/{project_id}/datasets",
            files={"file": ("synthetic_balanced.csv", handle.read(), "text/csv")},
            data={
                "target_column": "approved",
                "protected_columns": '["gender","race"]',
                "positive_label": "1",
                "prediction_column": "predicted_approved",
                "score_column": "score",
            },
        )
    second_dataset_id = second_upload.json()["data"]["id"]
    second_run = await client.post(
        f"/api/v1/projects/{project_id}/runs",
        json={"dataset_id": second_dataset_id},
    )
    assert second_run.status_code == 200
    second_run_id = second_run.json()["data"]["id"]

    results_response = await client.get(f"/api/v1/runs/{second_run_id}/results")
    assert results_response.status_code == 200
    payload = results_response.json()["data"]

    assert payload["counterfactual"]
    assert payload["drift"]["risk_history"]
    assert len(payload["drift"]["risk_history"]) >= 2
