"""Items counted across calls, built once from the stored notes, one note field at a time.

"What matters most to prospects?" is a count over calls. Notes ranked by similarity to an abstract
question cannot count: "Can the queue be owned by a team?" is raised in 5 of 10 calls but ranked
389th-479th of 509 noted turns, below the budget. Here, after ingestion, one call per field groups
that field's notes into specific items (the way a product manager would log them) and lists the
notes behind each; which calls raise an item, and how many, is then counted in code at question time,
for whatever calls the question is about. A note number the model returns that is not in the input
is dropped, so every item points at verified turns.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from .llm import INGEST_HEDGE_AFTER, INGEST_TIMEOUT, LLM, Usage
from .notes import StoredNote

PROMPT_VERSION = "themes-v1"

THEMES_SYSTEM = """You get the notes taken from many sales calls under one heading, one per line as
"N CALL-ID: point". Group them into items: one item per distinct, specific ask, capability, concern or
reason, the way a product manager would log it ("exception queue owned by a team, not a named
person"; "export audit logs to our own SIEM"; "change-management scenario in the evaluation"), never
a category ("security and governance", "exception handling"). If a group would hold two different
asks, split it. Each note goes under at most one item; leave out notes that say nothing specific.
Keep items raised in only one call, too. For each item: a short label, and the numbers N of its notes."""


class ThemeItem(BaseModel):
    item: str
    notes: list[int]


class Themes(BaseModel):
    items: list[ThemeItem]


@dataclass(frozen=True)
class Theme:
    field: str
    item: str
    refs: tuple[tuple[str, int], ...]  # (call_id, turn_idx) of the notes behind it


def build(field: str, notes: list[StoredNote], llm: LLM, usage: Usage | None = None) -> list[Theme]:
    if not notes:
        return []
    lines = [f"{i} {n.call_id}: {n.point}" for i, n in enumerate(notes)]
    out = llm.structured(THEMES_SYSTEM, f"HEADING\n{field}\n\nNOTES\n" + "\n".join(lines), Themes,
                         reasoning_effort="low", usage=usage, timeout=INGEST_TIMEOUT,
                         hedge_after=INGEST_HEDGE_AFTER)
    themes = []
    for it in out.items:
        refs = tuple(sorted({(notes[i].call_id, notes[i].turn_idx) for i in it.notes if 0 <= i < len(notes)}))
        if refs:
            themes.append(Theme(field, it.item, refs))
    return themes


def counted(themes: list[Theme], call_ids: list[str], min_calls: int = 2) -> list[tuple[Theme, list[str]]]:
    """Items with the calls among `call_ids` that raise them, most calls first; the count is of calls."""
    wanted = set(call_ids)
    out = []
    for t in themes:
        ids = sorted({cid for cid, _ in t.refs if cid in wanted})
        if len(ids) >= min_calls:
            out.append((t, ids))
    return sorted(out, key=lambda x: -len(x[1]))
