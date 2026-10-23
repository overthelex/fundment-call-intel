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
| `20261023-122047-auto-vendor-claims` | with the vendor-claims context | Claude Opus | reviewed | q11 fixed |
| `20261023-204145-auto-weighing` | product questions get every vendor statement on the topic, conflicts weighed | Claude Opus | reviewed | q24 fixed (15/14/0) |
| `20261023-210435-auto-names` | plus first-name checks in code, notes on names under the answer and shown to the judge | Claude Opus | reviewed | q06 fixed (14/14/1) |
| `20261023-214420-auto-diagnostics` | saves the exact context; adds evidence recall and the failed step per question | Claude Opus | reviewed | 14/15/0; evidence recall 0.82, excerpts 0.54 |
| `…-diagnostics-replay-base`, `-base2` | the 7 answer-step failures re-answered on the saved contexts, code unchanged | Claude Opus | reviewed | variance of the answer step alone |
| `…-diagnostics-replay-inv-a`, `-inv-b` | the same, with the turn inventory | Claude Opus | reviewed | effect of the inventory (core 0.64 → 0.69) |
| `20261023-223336-auto-map-subset` | the 8 cross-call questions with the map step | Claude Opus | reviewed | evidence recall 0.54 → 0.87 on them |
| `20261023-224354-auto-map` | map step (≤25 calls) and turn inventory | Claude Opus | reviewed | 20/9/0; evidence recall 0.94; 47K tokens/question (`--across map`) |
| `20261023-231007-auto-notes` | cross-call questions use notes written at ingestion | Claude Opus | reviewed | 16/13/0; evidence recall 0.86; 17K tokens/question |
| `20261023-235550-auto-compact` | inventory as call + timestamp only; adds per-step timings | Claude Opus | reviewed | 16/13/0; latency 36 s mean, 129 s p95 |
| `20261023-235835-auto-effort-low` | current code: low reasoning in the answer step | Claude Opus | reviewed | **the current numbers** (18/10/1; core 0.80; latency 9.9 s mean, 21.7 s p95) |
| `20261024-001127-auto-examples-low`, `20261024-002657-auto-examples-medium` | the task's 11 example questions, one at a time, low vs medium reasoning | Claude Opus | reviewed | latency 17.1 s vs 72.9 s mean; 6/4/1 vs 8/3/0 |

The raw 17.10 summaries (7/21/2, 5/24/1, 8/20/2) differ from the headline 14/14/1 because both the
judge and the rubric changed afterwards: the gold set was reviewed (`../review/`), facts were split
into core and details, and the answers were re-judged without being regenerated. Their deterministic
columns differ slightly too: the gold calls were revised (context recall 0.98 → 1.00) and the citation
checker gained speaker and call checks in between.
