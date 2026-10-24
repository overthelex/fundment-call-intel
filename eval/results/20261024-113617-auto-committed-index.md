## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.88 |
| cited recall (gold calls cited in the answer) | 0.96 |
| evidence cited (gold evidence turns cited) | 0.39 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | wrong_call 4 |
| answer correct (LLM judge): yes / partly / no | 17/11/1 |
| core fact recall (LLM judge) | 0.74 |
| atomic fact recall: cores + details, k of n for lists | 0.65 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.56 |
| core facts contradicted | 0 |
| penalties hit | 2 |
| bonus facts stated | 5/14 |
| correct abstention on unanswerable | 4/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 21,055 |
| mean latency (s) | 10.12 |
| latency p50 / p95 (s), 4 questions in parallel | 5.8 / 22.1 |
| answer step: mean output tokens (what latency follows) | 1,368 |
| first failed step | answer 8, retrieval 4, attribution 2, abstention: answered 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.45 | 1.00 | 0.27 | 0.97 | 0.83 | 0.71 |  | ✓ | high | attribution (1 failed citation) |
| q02 | aggregate | no | 1.00 | 1.00 | 0.60 | 0.42 | 1.00 | 0.60 | 0.30 | 1 | ✓ | medium | answer (evidence was in context) |
| q03 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.48 | 0.98 | 1.00 | 0.88 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.69 | 1.00 | 0.55 | 1.00 | 1.00 | 0.72 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.42 | 1.00 | 0.00 | 1.00 | 0.50 | 0.40 |  | ✓ | high | retrieval (14 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.55 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 1.00 | 0.75 | 0.40 | 0.97 | 0.60 | 0.64 |  | ✓ | medium | answer (evidence was in context); attribution (1 failed citation) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.83 | 0.81 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.64 | 0.75 | 0.14 | 1.00 | 0.40 | 0.27 |  | ✓ | high | retrieval (5 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.75 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | high | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.18 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | partly | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 0.75 | 0.75 |  | ✓ | high | retrieval (3 evidence turns not in context) |
| q17 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.62 | 1.00 | 1.00 | 0.80 |  | ✓ | medium |  |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 0.25 | 0.50 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.75 | 0.73 | 1 | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 0.80 | 0.67 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 0.93 | 1.00 | 0.36 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | yes | - | 1.00 | - | 0.33 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 1.00 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
