# Saved runs

Every run writes `<timestamp>-<mode>[-suffix].json` (answers, plans, citation checks, verdicts) and a
`.md` summary. Answering model throughout: `gpt-5.4-mini`. Summaries written since 23.10 name the judge
in a `Judge:` line; the older ones predate that line, so their judge is listed here.

| files | what it is | judge | gold set | use it for |
|---|---|---|---|---|
| `20261017-155023-auto`, `-155813-auto`, `-160049-auto` | pipeline, 3 runs | `gpt-5.4` (the first version's judge) | before review | raw history only |
| `20261017-155512-full` | baseline, whole dataset in the prompt | `gpt-5.4` | before review | raw history only |
| `*-regraded` (all four of the above) | the same answers, citations re-checked and re-judged with `--regrade` | Claude Opus | reviewed | **the headline numbers in the README** |
| `20261017-155023-auto-judge-repeat-opus` | run 1 re-judged a second time | Claude Opus | reviewed | judge noise (6 of 30 verdicts moved) |
| `20261017-155023-auto-judge-gpt54` | run 1 re-judged by another model | `gpt-5.4` | reviewed | how much the choice of judge moves the numbers |
| `comparison.md` | per-question comparison of the regraded runs (`compare.py`) | - | reviewed | which questions are unstable |
| `20261023-120606-auto-fresh-clone` | pipeline run from a fresh clone, following the README | Claude Opus | reviewed | reproduction check |
| `20261023-122047-auto-vendor-claims` | current code, with the vendor-claims context | Claude Opus | reviewed | **the current numbers** (q11 fixed) |

The raw 17.10 summaries (7/21/2, 5/24/1, 8/20/2) differ from the headline 14/14/1 because both the
judge and the rubric changed afterwards: the gold set was reviewed (`../review/`), facts were split
into core and details, and the answers were re-judged without being regenerated. Their deterministic
columns differ slightly too: the gold calls were revised (context recall 0.98 → 1.00) and the citation
checker gained speaker and call checks in between.
