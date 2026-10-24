# Saved runs

Every run writes `<timestamp>-<mode>[-suffix].json` (answers, plans, the exact context each answer
saw, citation checks and verdicts) and a `.md` summary. Answering model `gpt-5.4-mini`, judge Claude
Opus (named in each summary's `Judge:` line), reviewed gold set.

Runs of the current code:

| files | what it is | result |
|---|---|---|
| `20261024-094317-auto-fresh-clone` | pipeline, all 30 questions, from a fresh clone following the README | 19 / 9 / 1; 17K tokens; latency 8.6 s mean, 21.0 s p95 |
| `20261024-094601-full-fresh-clone` | baseline: whole dataset in the prompt (`--mode full`), same clone | 13 / 14 / 2; 123K tokens; 17 failed citations |
| `20261023-235835-auto-effort-low` | pipeline, a second run of the same code | 18 / 10 / 1; latency 9.9 s mean, 21.7 s p95 |
| `20261024-001127-auto-examples-low` | the task's 11 example questions, one at a time | 17.1 s mean |
| `20261024-002657-auto-examples-medium` | the same with `ANSWER_EFFORT=medium` | 72.9 s mean |
| `20261024-1022*-auto-q11-topic-check` | q11 three times, with the per-topic contradiction check added after the runs above | yes, yes, yes |
| `comparison.md` | per-question verdicts of the first three runs (`compare.py`) | which questions are unstable |

Options for questions across calls (`--across`), measured with `ANSWER_EFFORT=medium`:

| files | `--across` | result |
|---|---|---|
| `20261023-231007-auto-notes` | `notes` (default) | 16 / 13 / 0; evidence recall 0.86; 17K tokens per question |
| `20261023-224354-auto-map` | `map` | 20 / 9 / 0; evidence recall 0.94; 47K tokens per question |
| `20261023-214420-auto-diagnostics` | `retrieval` (run without the turn inventory) | 14 / 15 / 0; evidence recall 0.82 |

`archive/` holds the runs of earlier versions of the code. Two of them are still the evidence for how
noisy the judge is: `20261017-155023-auto-judge-repeat-opus` (the same answers judged twice: 6 of 30
verdicts moved between yes and partly) and `20261017-155023-auto-judge-gpt54` (another judge model:
22 of 30 agree).
