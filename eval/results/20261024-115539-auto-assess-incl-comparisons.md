## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.86 |
| cited recall (gold calls cited in the answer) | 0.98 |
| evidence cited (gold evidence turns cited) | 0.43 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 2, wrong_call 2 |
| answer correct (LLM judge): yes / partly / no | 17/12/0 |
| core fact recall (LLM judge) | 0.76 |
| atomic fact recall: cores + details, k of n for lists | 0.66 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.61 |
| core facts contradicted | 0 |
| penalties hit | 1 |
| bonus facts stated | 5/14 |
| correct abstention on unanswerable | 4/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 35,684 |
| mean latency (s) | 9.88 |
| latency p50 / p95 (s), 4 questions in parallel | 7.4 / 20.3 |
| answer step: mean output tokens (what latency follows) | 1,190 |
| first failed step | answer 7, retrieval 4, attribution 2, abstention: answered 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.36 | 1.00 | 0.18 | 0.96 | 0.83 | 0.71 |  | ✓ | high | attribution (1 failed citation) |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.75 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.86 | 0.83 | 0.34 | 1.00 | 0.83 | 0.56 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.72 | 0.88 | 0.41 | 0.91 | 1.00 | 0.89 |  | ✓ | high | attribution (2 failed citations) |
| q05 | aggregate | partly | 1.00 | 0.42 | 1.00 | 0.08 | 1.00 | 0.50 | 0.60 |  | ✓ | high | retrieval (14 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.82 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.70 | 1.00 | 0.60 | 0.97 | 0.60 | 0.64 |  | ✓ | high | retrieval (6 evidence turns not in context); attribution (1 failed citation) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.25 | 1.00 | 0.83 | 0.69 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.43 | 0.75 | 0.29 | 1.00 | 0.40 | 0.27 |  | ✓ | high | retrieval (8 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.75 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.50 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 0.25 | 0.50 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.56 | 1.00 | 0.75 | 0.73 | 1 | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.35 | 1.00 | 1.00 | 0.67 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.06 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 0.93 | 1.00 | 0.71 | 1.00 | 1.00 | 0.80 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.17 | 1.00 | 0.50 | 0.40 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 1.00 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
