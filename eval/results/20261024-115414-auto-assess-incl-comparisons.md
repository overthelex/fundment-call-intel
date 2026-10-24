## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.87 |
| cited recall (gold calls cited in the answer) | 0.98 |
| evidence cited (gold evidence turns cited) | 0.43 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | wrong_call 4, wrong_speaker 2 |
| answer correct (LLM judge): yes / partly / no | 17/12/0 |
| core fact recall (LLM judge) | 0.73 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.60 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 3/14 |
| correct abstention on unanswerable | 3/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 35,571 |
| mean latency (s) | 10.23 |
| latency p50 / p95 (s), 4 questions in parallel | 9.8 / 19.3 |
| answer step: mean output tokens (what latency follows) | 1,258 |
| first failed step | answer 6, retrieval 5, abstention: answered 2, attribution 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.50 | 1.00 | 0.18 | 1.00 | 0.83 | 0.76 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q03 | aggregate | partly | 1.00 | 0.83 | 0.83 | 0.24 | 0.97 | 0.67 | 0.25 |  | ✓ | high | retrieval (5 evidence turns not in context); attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.69 | 1.00 | 0.55 | 0.93 | 1.00 | 1.00 |  | ✓ | high | attribution (4 failed citations) |
| q05 | aggregate | partly | 1.00 | 0.42 | 1.00 | 0.08 | 0.97 | 0.33 | 0.50 |  | ✓ | medium | retrieval (14 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.91 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.95 | 1.00 | 0.40 | 1.00 | 0.60 | 0.64 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.28 | 1.00 | 0.83 | 0.69 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.50 | 1.00 | 0.07 | 1.00 | 0.00 | 0.00 |  | ✓ | high | retrieval (7 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.75 | 0.67 | 0.25 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.75 | 1.00 | 0.75 | 0.71 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 1.00 | 0.50 | 0.45 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.60 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 0.25 | 0.50 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.75 | 0.82 |  | ✓ | high |  |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.35 | 1.00 | 0.80 | 0.67 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 0.93 | 1.00 | 0.71 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✗ | high | abstention: answered |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
