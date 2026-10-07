"""Append-only audit trail for agent iterations."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"


def record(event: str, tool_name: str, arguments: object = None, result: object = None, stop_reason: str | None = None) -> None:
    """Append one compact JSON object; this file is never truncated or cleared."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "tool": tool_name,
        "arguments": str(arguments)[:500] if arguments is not None else None,
        "result": str(result)[:500] if result is not None else None,
        "stop_reason": stop_reason,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
