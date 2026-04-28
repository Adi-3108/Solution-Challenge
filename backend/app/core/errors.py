from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, object] = field(default_factory=dict)

