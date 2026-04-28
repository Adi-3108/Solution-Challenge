from __future__ import annotations

from fastapi import Request


def envelope(request: Request, data: object, next_cursor: str | None = None) -> dict[str, object]:
    return {
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "next_cursor": next_cursor,
        },
    }


def error_response(code: str, message: str, details: dict[str, object]) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": details}}

