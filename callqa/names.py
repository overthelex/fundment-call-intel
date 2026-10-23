"""First names in a question that could mean more than one person.

The planner sees only the catalogue of participants, so it cannot know that "Priya" is also someone
mentioned in passing on another call. This check is plain code over the parsed transcripts: for each
participant first name used in the question without a surname, list everyone who speaks under that
name, and every call where the name is mentioned although nobody on the call has it. OrbitFlow staff
are one team across calls, so a mention of "Maya" elsewhere is taken to be the same Maya Chen.
"""

from __future__ import annotations

import re

from .parse import VENDOR, Call

WORD_RE = re.compile(r"\b[A-Z][a-z]+\b")


def ambiguous_names(question: str, calls: list[Call]) -> list[str]:
    # first name -> {(full name, company): [call ids]}
    speakers: dict[str, dict[tuple[str, str], list[str]]] = {}
    roles: dict[tuple[str, str], str] = {}
    for call in calls:
        for p in call.participants:
            speakers.setdefault(p.name.split()[0], {}).setdefault((p.name, p.company), []).append(call.call_id)
            roles[(p.name, p.company)] = p.role

    notes = []
    for first in dict.fromkeys(WORD_RE.findall(question)):
        named = speakers.get(first)
        if not named:
            continue
        surname = re.search(rf"\b{first} ([A-Z][a-z]+)", question)
        if surname and any(n.split()[-1] == surname.group(1) for n, _ in named):
            continue  # full name given
        only_staff = all(company == VENDOR for _, company in named)

        mention_re = re.compile(rf"\b{first}\b(?: ([A-Z][a-z]+))?")
        mentions = []
        for call in [] if only_staff else calls:
            if any(p.name.split()[0] == first for p in call.participants):
                continue  # on this call the name means the participant
            for t in call.turns:
                m = mention_re.search(t.text)
                if m:
                    who = f"{first} {m.group(1)}" if m.group(1) else f"a {first}"
                    mentions.append(f"{who} at {call.company} ({call.call_id} [{t.ts}])")
                    break

        if len(named) + len(mentions) < 2:
            continue
        people = "; ".join(
            f"{name} ({roles[(name, company)]}, {company}, {', '.join(ids)})" for (name, company), ids in named.items()
        )
        speaks = "is the only one who speaks on a call" if len(named) == 1 else "all speak on calls"
        note = f'"{first}" is ambiguous: {people} {speaks}.'
        if mentions:
            note += " Also mentioned, not on those calls: " + "; ".join(mentions) + "."
        notes.append(note)
    return notes
