"""Parse transcript files into Call / Turn records.

The transcript files are the source of truth. The manifest is only used to
cross-check the headers: every turn keeps its file line number so evidence can
be traced back to `data/calls/<file>:<line>`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

VENDOR = "OrbitFlow"
TURN_RE = re.compile(r"^\[(\d{1,3}):(\d{2})\] ([^:]+): (.*)$")
PARTICIPANT_NOTE_RE = re.compile(r"\s*\(([^)]*)\)\s*$")


@dataclass(frozen=True)
class Participant:
    name: str
    role: str
    company: str
    note: str = ""

    @property
    def side(self) -> str:
        return "vendor" if self.company == VENDOR else "customer"


@dataclass(frozen=True)
class Turn:
    call_id: str
    idx: int  # 0-based position within the call
    ts: str  # "MM:SS" as written in the transcript
    seconds: int
    speaker: str
    side: str  # vendor | customer | unknown
    text: str
    line: int  # 1-based line number in the source file


@dataclass
class Call:
    call_id: str
    path: Path
    date: str
    company: str
    industry: str
    company_size: str
    stage: str
    duration_minutes: int
    call_type: str = ""  # from manifest: Prospect | Renewal | Churn | Cold call ...
    participants: list[Participant] = field(default_factory=list)
    turns: list[Turn] = field(default_factory=list)
    # header lines as pseudo-turns (ts="header"), so header metadata can be cited and checked too
    header: list[Turn] = field(default_factory=list)

    @property
    def category(self) -> str:
        """prospect | renewal | churn | cold_call, derived from the stage.

        The manifest's call_type only distinguishes Prospect / Existing customer.
        """
        stage = self.stage.lower()
        if "cold call" in stage:
            return "cold_call"
        if "churn" in stage:
            return "churn"
        if "renewal" in stage:
            return "renewal"
        return "prospect"

    def speaker(self, name: str) -> Participant | None:
        return next((p for p in self.participants if p.name == name), None)

    def label(self) -> str:
        return f"{self.call_id} | {self.company} | {self.category} | {self.stage} | {self.date}"


def _parse_participant(line: str) -> Participant:
    body = line.lstrip("- ").strip()
    note = ""
    m = PARTICIPANT_NOTE_RE.search(body)
    if m:
        note, body = m.group(1), body[: m.start()]
    parts = [p.strip() for p in body.split(",")]
    name, company = parts[0], parts[-1]
    role = ", ".join(parts[1:-1])
    return Participant(name=name, role=role, company=company, note=note)


def parse_call(path: Path) -> Call:
    lines = path.read_text(encoding="utf-8").splitlines()
    header: dict[str, str] = {}
    participants: list[Participant] = []
    header_lines: list[tuple[int, str]] = []
    i = 0
    while i < len(lines) and lines[i].strip() != "TRANSCRIPT":
        line = lines[i]
        if line.strip():
            header_lines.append((i + 1, line.strip()))
        if line.startswith("- "):
            participants.append(_parse_participant(line))
        elif ":" in line:
            key, _, value = line.partition(":")
            header[key.strip().upper()] = value.strip()
        i += 1
    if i == len(lines):
        raise ValueError(f"{path}: no TRANSCRIPT marker")

    call_id = header["CALL ID"]
    by_name = {p.name: p for p in participants}
    turns: list[Turn] = []
    for lineno in range(i + 1, len(lines)):
        m = TURN_RE.match(lines[lineno])
        if not m:
            continue  # disclaimer line and blanks
        mm, ss, speaker, text = m.groups()
        p = by_name.get(speaker)
        turns.append(
            Turn(
                call_id=call_id,
                idx=len(turns),
                ts=f"{mm}:{ss}",
                seconds=int(mm) * 60 + int(ss),
                speaker=speaker,
                side=p.side if p else "unknown",
                text=text.strip(),
                line=lineno + 1,
            )
        )

    duration = re.match(r"\d+", header.get("DURATION", "0"))
    return Call(
        call_id=call_id,
        path=path,
        date=header.get("DATE", ""),
        # existing customers are labelled CUSTOMER:, prospects PROSPECT:
        company=header.get("PROSPECT") or header.get("CUSTOMER", ""),
        industry=header.get("INDUSTRY", ""),
        company_size=header.get("COMPANY SIZE", ""),
        stage=header.get("STAGE", ""),
        duration_minutes=int(duration.group()) if duration else 0,
        participants=participants,
        turns=turns,
        header=[
            Turn(call_id, -1, "header", 0, "header", "metadata", text, lineno) for lineno, text in header_lines
        ],
    )


def load_calls(data_dir: Path) -> list[Call]:
    manifest = {m["call_id"]: m for m in json.loads((data_dir / "manifest.json").read_text())}
    calls = []
    for path in sorted((data_dir / "calls").glob("call-*.txt")):
        call = parse_call(path)
        meta = manifest.get(call.call_id)
        if meta:
            call.call_type = meta.get("call_type", "")
        calls.append(call)
    return calls
