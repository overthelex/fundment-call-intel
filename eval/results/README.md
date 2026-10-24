# Saved runs

Every run writes `<timestamp>-<mode>[-suffix].json` (answers, plans, the exact context each answer
saw, citation checks and verdicts) and a `.md` summary. Answering model `gpt-5.4-mini`, judge Claude
Opus (named in each summary's `Judge:` line), reviewed gold set.

Runs of the current code (the README's results table):

| files | what it is | result |
|---|---|---|
| `20261024-113617-auto-committed-index`, `20261024-113750-auto-committed-index` | pipeline, twice, on the index committed in `.cache/` (claims from two merged passes) | 17 / 11 / 1 and 17 / 12 / 0; 21K tokens |
| `20261024-094601-full-fresh-clone` | baseline: whole dataset in the prompt (`--mode full`) | 13 / 14 / 2; 123K tokens; 17 failed citations |
| `comparison.md` | per-question verdicts of these three runs (`compare.py`) | which questions are unstable |

The same code with a single claims pass, on four fresh indexes: `20261024-111014-auto-fresh-clone-4`
18 / 10 / 1 and, on that same index again, `20261024-112846-auto-same-index` 13 / 15 / 1 (that index
lacked the "completely no-code" claim, so q11 depended on luck); `20261024-104212-auto-fresh-clone-2`
17 / 11 / 1; `20261024-105919-auto-fresh-clone-3` 16 / 12 / 1.

Runs that show one change, referenced from the README and `EVALUATION.md`:

| files | what it is | result |
|---|---|---|
| `20261024-094317-auto-fresh-clone` | pipeline before the q10 and q11 fixes | 19 / 9 / 1; q10 yes, q11 partly |
| `20261023-235835-auto-effort-low` | the same code on another index | 18 / 10 / 1 |
| `20261024-1022*-auto-q11-topic-check` | q11 three times, after adding the per-topic contradiction check | yes, yes, yes |
| `20261024-1031*-auto-per-call-check` | q08, q10, q19, q20 four times, after adding per-call verdicts | q10 yes ×4, q08 3 yes 1 partly, q19 partly, q20 yes |
| `20261024-001127-auto-examples-low` | the task's 11 example questions, one at a time | 17.1 s mean |
| `20261024-002657-auto-examples-medium` | the same with `ANSWER_EFFORT=medium` | 72.9 s mean |

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
