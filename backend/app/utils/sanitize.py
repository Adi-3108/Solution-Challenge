from __future__ import annotations

import html


def sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return html.escape(value.strip())

