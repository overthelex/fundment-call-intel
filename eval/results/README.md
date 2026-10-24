# Saved runs

Every run writes `<timestamp>-<mode>[-suffix].json` (answers, plans, the exact context each answer
saw, citation checks and verdicts) and a `.md` summary. Answering model `gpt-5.4-mini`, judge Claude
Opus (named in each summary's `Judge:` line), reviewed gold set.

Runs of the current code (the README's results table):

| files | what it is | result |
|---|---|---|
| `20261024-154829-auto-parts`, `20261024-154956-auto-parts` | pipeline, twice, on the index committed in `.cache/` (calls read in parts) | 16 / 13 / 0 and 17 / 12 / 0; 34K tokens |
| `20261024-094601-full-fresh-clone` | baseline: whole dataset in the prompt (`--mode full`) | 13 / 14 / 2; 123K tokens; 17 failed citations |
| `comparison.md` | per-question verdicts of these three runs (`compare.py`) | which questions are unstable |

The same code before calls were read in parts, on the previous index (whole calls at medium):
`20261024-123718-auto-final` 20 / 9 / 0 and `20261024-123853-auto-final` 15 / 13 / 1 (32–33K tokens).
The ingestion benchmark behind the switch is `eval/bench_ingest.py` (README, *Speed*).

Tried and not kept (README, q05): notes ranked by the question and the planner's search queries,
budget 350 turns: `20261024-173307/173429-auto-query-rank` 16 / 12 / 1 and 14 / 14 / 1, and the 11
example questions `20261024-173732-auto-examples-query-rank` 8 / 3 / 0.

Before the notes recorded capability questions and comparisons got the small kinds of call whole
(previous index): `20261024-120000/120140-auto-before-notes-v2` 19 / 9 / 1 and 17 / 12 / 0. With those
changes, q05, q07 and q09 alone: `20261024-123424/123502/123529-auto-q05-q07-q09`.

Before per-call verdicts for questions that rank or classify calls, on the index before that:
`20261024-113617-auto-committed-index` 17 / 11 / 1 and `20261024-113750-auto-committed-index`
17 / 12 / 0 (21K tokens). With them: `20261024-115650/115727/115809-auto-assess-each-call` (q02, q07, q09,
q28, three times: q07 yes 2 of 3, q02 and q28 yes 3 of 3) and, with comparisons also getting
verdicts, `20261024-115414/115539-auto-assess-incl-comparisons` (q09 core recall 0.0 and 0.27).

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
| `20261024-172455-auto-examples-low` | the task's 11 example questions, one at a time, current index | 9 / 2 / 0; 15.0 s mean |
| `20261024-143451-auto-examples-low` | the same on the previous index | 8 / 3 / 0; 16.7 s mean |
| `20261024-144652-auto-examples-medium` | the same with `ANSWER_EFFORT=medium`, previous index | 7 / 4 / 0; 63.8 s mean |

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
