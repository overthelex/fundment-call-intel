## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus x3 votes, median`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.79 |
| cited recall (gold calls cited in the answer) | 0.99 |
| evidence cited (gold evidence turns cited) | 0.36 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 3 |
| answer correct: yes / partly / no (from the judge's fact verdicts, in code) | 15/12/2 |
| judge's own overall verdict agrees with it | 25/29 |
| judge: votes per answer; answers where every vote agreed on its overall verdict | 3;22/29 |
| core fact recall (LLM judge) | 0.77 |
| atomic fact recall: cores + details, k of n for lists | 0.67 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.61 |
| core facts contradicted | 2 |
| penalties hit | 3 |
| bonus facts stated | 1/14 |
| correct abstention on unanswerable | 3/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 33,654 |
| of which from the provider's prompt cache | 0% |
| mean latency (s) | 18.44 |
| latency p50 / p95 (s), 4 questions in parallel | 14.4 / 39.0 |
| answer step: mean output tokens (what latency follows) | - |
| first failed step | retrieval 6, answer 5, attribution 3, answer: wrong statement 2, abstention: answered 2 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.41 | 1.00 | 0.27 | 0.97 | 1.00 | 0.82 |  | ✓ | high | attribution (1 failed citation) |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.75 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes (yes/partly/yes) | 1.00 | 0.66 | 1.00 | 0.28 | 1.00 | 0.83 | 0.62 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.72 | 1.00 | 0.52 | 1.00 | 1.00 | 0.94 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.62 | 0.67 | 0.00 | 1.00 | 0.67 | 0.70 |  | ✓ | medium | retrieval (9 evidence turns not in context) |
| q06 | entity_resolution | partly (yes/partly/yes) | 1.00 | 0.45 | 1.00 | 0.45 | 1.00 | 0.83 | 0.67 |  | ✓ | high | retrieval (6 evidence turns not in context) |
| q07 | aggregate | no (partly/partly/no) | 1.00 | 0.55 | 1.00 | 0.30 | 1.00 | 0.40 | 0.45 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.12 | 1.00 | 0.50 | 0.38 | 1 | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly (partly/yes/yes) | 1.00 | 0.57 | 1.00 | 0.07 | 0.93 | 0.80 | 0.55 |  | ✓ | high | retrieval (6 evidence turns not in context); attribution (1 failed citation) |
| q10 | aggregate | yes | 1.00 | 0.58 | 1.00 | 0.37 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.25 | 0.96 | 1.00 | 0.75 |  | ✓ | medium | attribution (1 failed citation) |
| q12 | single_call | partly (partly/partly/yes) | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | high | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.18 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 0.86 | 1.00 | 1.00 |  | ✓ | high | attribution (1 failed citation) |
| q17 | single_call | no (no/no/partly) | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.60 | 0.60 |  | ✓ | medium | answer: wrong statement |
| q18 | single_call | partly | 1.00 | 0.93 | 1.00 | 0.21 | 1.00 | 0.75 | 0.67 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q19 | multi_call | partly (no/partly/partly) | 1.00 | 0.56 | 1.00 | 0.44 | 1.00 | 0.50 | 0.55 | 2 | ✓ | high | retrieval (7 evidence turns not in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.41 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 0.81 | 1.00 | 0.06 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (3 evidence turns not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 0.86 | 1.00 | 0.64 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | high |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✗ | insufficient | abstention: answered |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 0.50 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | partly | 1.00 | 0.89 | 1.00 | 0.22 | 1.00 | 0.67 | 0.80 |  | ✓ | high | retrieval (1 evidence turn not in context) |
