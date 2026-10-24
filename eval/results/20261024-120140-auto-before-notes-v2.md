## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.87 |
| cited recall (gold calls cited in the answer) | 0.99 |
| evidence cited (gold evidence turns cited) | 0.44 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 2, wrong_call 2, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 17/12/0 |
| core fact recall (LLM judge) | 0.81 |
| atomic fact recall: cores + details, k of n for lists | 0.69 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.64 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 5/14 |
| correct abstention on unanswerable | 4/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 31,244 |
| mean latency (s) | 11.19 |
| latency p50 / p95 (s), 4 questions in parallel | 8.5 / 31.2 |
| answer step: mean output tokens (what latency follows) | 1,370 |
| first failed step | answer 8, attribution 3, retrieval 3, abstention: answered 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.41 | 1.00 | 0.27 | 1.00 | 1.00 | 0.76 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.92 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.41 | 0.97 | 1.00 | 0.88 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.76 | 0.88 | 0.34 | 0.96 | 1.00 | 0.72 |  | ✓ | high | attribution (1 failed citation) |
| q05 | aggregate | partly | 1.00 | 0.42 | 0.83 | 0.04 | 1.00 | 0.67 | 0.60 |  | ✓ | medium | retrieval (14 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.82 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.95 | 1.00 | 0.55 | 1.00 | 1.00 | 0.64 |  | ✓ | medium |  |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.34 | 1.00 | 0.67 | 0.69 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.29 | 1.00 | 0.14 | 0.94 | 0.20 | 0.18 |  | ✓ | high | retrieval (10 evidence turns not in context); attribution (1 failed citation) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.63 | 0.95 | 1.00 | 0.79 |  | ✓ | high | attribution (1 failed citation) |
| q11 | conflict | yes | 1.00 | 0.75 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | high | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.36 | 1.00 | 0.50 | 0.45 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.60 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.14 | 1.00 | 0.75 | 0.67 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.75 | 0.64 |  | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.41 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 1.00 | 1.00 | 0.79 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.00 | - | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.00 | 1.00 | 1.00 | 1.00 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
