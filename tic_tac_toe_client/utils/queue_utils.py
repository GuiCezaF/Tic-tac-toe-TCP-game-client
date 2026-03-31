"""Operações sobre filas sem bloqueio."""

from __future__ import annotations

import queue
from typing import Any


def drain_queue(
    q: queue.Queue[dict[str, Any]],
    max_items: int = 256,
) -> list[dict[str, Any]]:
    """Esvazia até `max_items` elementos sem bloquear."""
    out: list[dict[str, Any]] = []
    for _ in range(max_items):
        try:
            out.append(q.get_nowait())
        except queue.Empty:
            break
    return out
