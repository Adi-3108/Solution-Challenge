from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Iterable

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _iter_response_text(payload: dict[str, object]) -> Iterable[str]:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    texts: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        parts = content.get("parts", [])
        if not isinstance(parts, list):
            continue
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return texts


def _extract_json(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
        stripped = stripped.strip()

    try:
        payload = json.loads(stripped)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            payload = json.loads(stripped[start : end + 1])
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None


def _compact_metrics(metrics: object) -> list[dict[str, object]]:
    if not isinstance(metrics, list):
        return []
    compact: list[dict[str, object]] = []
    for metric in metrics:
        if not isinstance(metric, dict):
            continue
        compact.append(
            {
                "id": metric.get("id"),
                "metric_name": metric.get("metric_name"),
                "display_name": metric.get("display_name"),
                "group_name": metric.get("group_name"),
                "value": metric.get("value"),
                "severity": metric.get("severity"),
                "threshold_used": metric.get("threshold_used"),
                "explanation": metric.get("explanation"),
                "details": metric.get("details"),
            }
        )
    return compact


def _compact_recommendations(recommendations: object) -> list[dict[str, object]]:
    if not isinstance(recommendations, list):
        return []
    compact: list[dict[str, object]] = []
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        compact.append(
            {
                "title": recommendation.get("title"),
                "metric_name": recommendation.get("metric_name"),
                "affected_group": recommendation.get("affected_group"),
                "strategy": recommendation.get("strategy"),
                "summary": recommendation.get("summary"),
            }
        )
    return compact


async def enrich_audit_payload(payload: dict[str, object]) -> dict[str, object] | None:
    if not settings.gemini_api_key:
        return None

    compact_input = {
        "run": payload.get("run"),
        "summary": payload.get("summary"),
        "metrics": _compact_metrics(payload.get("metrics")),
        "recommendations": _compact_recommendations(payload.get("recommendations")),
        "drift": payload.get("drift"),
    }
    prompt = (
        "You are improving audit explanations for fairness results.\n"
        "Given this JSON, return ONLY JSON with this exact shape:\n"
        "{"
        '"metrics":[{"id":"<metric-id-or-null>","metric_name":"...","group_name":"...","explanation":"..."}],'
        '"recommendations":[{"metric_name":"...","affected_group":"...","summary":"..."}],'
        '"summary":{"narrative":"...", "key_takeaways":["..."]}'
        "}\n"
        "Rules:\n"
        "- Keep reasoning factual and tied to metric values/severity/thresholds.\n"
        "- Do not invent numbers or groups.\n"
        "- explanation should be 2-4 sentences each.\n"
        "- recommendation summary should be actionable and specific.\n"
        "- Use plain language.\n\n"
        f"INPUT JSON:\n{json.dumps(compact_input, ensure_ascii=True)}"
    )

    params = {"key": settings.gemini_api_key}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    # gemini-2.5-flash is a preview model with limited capacity — 503s are common.
    # Build a fallback chain: try the configured model first, then the stable fallback.
    _FALLBACK_MODEL = "gemini-1.5-flash"
    model_chain: list[str] = [settings.gemini_model]
    if settings.gemini_model != _FALLBACK_MODEL:
        model_chain.append(_FALLBACK_MODEL)

    # gemini-2.5-flash has a "thinking" phase that can take 60-90 s.
    # Use a structured timeout: short connect, long read.
    gemini_timeout = httpx.Timeout(
        connect=10.0,
        read=max(float(settings.gemini_timeout_seconds), 90.0),
        write=10.0,
        pool=5.0,
    )

    response_json: dict[str, object] | None = None

    for model in model_chain:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        max_retries = 2  # 2 tries per model before switching to fallback
        retry_delay = 5.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=gemini_timeout) as client:
                    response = await client.post(url, params=params, json=body)
                    response.raise_for_status()
                    response_json = response.json()
                    break  # success — exit retry loop
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    jitter = random.uniform(0.5, 1.5)
                    logger.warning(
                        "gemini_request_failed_retrying",
                        model=model,
                        status=status,
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(retry_delay * jitter)
                    retry_delay *= 2
                    continue
                # Capacity errors (503/502/504) on last attempt → try next model
                if status in (502, 503, 504):
                    logger.warning(
                        "gemini_model_unavailable_trying_fallback",
                        model=model,
                        status=status,
                    )
                    break  # exit retry loop, outer loop picks next model
                logger.warning("gemini_enrichment_failed", model=model, error=repr(exc))
                return None
            except httpx.RequestError as exc:
                if attempt < max_retries - 1:
                    jitter = random.uniform(0.5, 1.5)
                    logger.warning(
                        "gemini_request_exception_retrying",
                        model=model,
                        error=repr(exc),
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(retry_delay * jitter)
                    retry_delay *= 2
                    continue
                logger.warning("gemini_enrichment_failed", model=model, error=repr(exc))
                return None
            except Exception as exc:
                logger.warning("gemini_enrichment_failed", model=model, error=repr(exc))
                return None

        if response_json is not None:
            break  # success — skip remaining models in chain

    if response_json is None:
        logger.warning("gemini_enrichment_failed_all_models", models=model_chain)
        return None

    parsed: dict[str, object] | None = None
    for text in _iter_response_text(response_json if isinstance(response_json, dict) else {}):
        parsed = _extract_json(text)
        if parsed is not None:
            break
    if parsed is None:
        logger.warning("gemini_enrichment_parse_failed")
        return None

    merged = dict(payload)
    metric_updates = parsed.get("metrics", [])
    if isinstance(metric_updates, list) and isinstance(payload.get("metrics"), list):
        keyed = {}
        for item in payload["metrics"]:
            if not isinstance(item, dict):
                continue
            metric_id = item.get("id")
            if metric_id is not None:
                keyed[str(metric_id)] = item
        for update in metric_updates:
            if not isinstance(update, dict):
                continue
            target = None
            metric_id = update.get("id")
            if metric_id is not None:
                target = keyed.get(str(metric_id))
            if target is None:
                for item in payload["metrics"]:
                    if not isinstance(item, dict):
                        continue
                    if (
                        item.get("metric_name") == update.get("metric_name")
                        and item.get("group_name") == update.get("group_name")
                    ):
                        target = item
                        break
            if target is not None and isinstance(update.get("explanation"), str):
                target["explanation"] = update["explanation"].strip()

    recommendation_updates = parsed.get("recommendations", [])
    if isinstance(recommendation_updates, list) and isinstance(payload.get("recommendations"), list):
        for update in recommendation_updates:
            if not isinstance(update, dict):
                continue
            for recommendation in payload["recommendations"]:
                if not isinstance(recommendation, dict):
                    continue
                if (
                    recommendation.get("metric_name") == update.get("metric_name")
                    and recommendation.get("affected_group") == update.get("affected_group")
                    and isinstance(update.get("summary"), str)
                ):
                    recommendation["summary"] = update["summary"].strip()
                    break

    if isinstance(merged.get("summary"), dict):
        summary_update = parsed.get("summary")
        if isinstance(summary_update, dict):
            narrative = summary_update.get("narrative")
            takeaways = summary_update.get("key_takeaways")
            if isinstance(narrative, str):
                merged["summary"]["narrative"] = narrative.strip()
            if isinstance(takeaways, list):
                merged["summary"]["key_takeaways"] = [str(item) for item in takeaways if str(item).strip()]

    return merged

