## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.87 |
| cited recall (gold calls cited in the answer) | 0.99 |
| evidence cited (gold evidence turns cited) | 0.37 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 2, wrong_call 3, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 19/9/1 |
| core fact recall (LLM judge) | 0.76 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.60 |
| core facts contradicted | 1 |
| penalties hit | 0 |
| bonus facts stated | 6/14 |
| correct abstention on unanswerable | 5/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 31,200 |
| mean latency (s) | 9.94 |
| latency p50 / p95 (s), 4 questions in parallel | 10.4 / 20.7 |
| answer step: mean output tokens (what latency follows) | 1,272 |
| first failed step | retrieval 4, answer 4, attribution 3, answer: wrong statement 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.50 | 1.00 | 0.14 | 1.00 | 0.83 | 0.59 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.75 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.21 | 0.95 | 0.83 | 0.62 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.72 | 1.00 | 0.38 | 0.97 | 1.00 | 0.78 |  | ✓ | high | attribution (1 failed citation) |
| q05 | aggregate | partly | 1.00 | 0.42 | 1.00 | 0.21 | 0.96 | 0.67 | 0.70 |  | ✓ | high | retrieval (14 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.73 | 0.98 | 1.00 | 1.00 |  | ✓ | high | attribution (1 failed citation) |
| q07 | aggregate | partly | 1.00 | 0.95 | 1.00 | 0.70 | 1.00 | 0.80 | 0.64 |  | ✓ | medium | retrieval (1 evidence turn not in context) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.25 | 1.00 | 0.83 | 0.62 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.36 | 0.75 | 0.14 | 0.93 | 0.20 | 0.18 |  | ✓ | high | retrieval (9 evidence turns not in context); attribution (1 failed citation) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.75 | 1.00 | 0.35 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 1.00 | 0.50 | 0.45 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high |  |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q17 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.80 | 0.70 |  | ✓ | medium |  |
| q18 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.75 | 0.82 |  | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q21 | single_call | no | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 0.00 | 0.50 |  | ✓ | medium | answer: wrong statement |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 1.00 | 0.80 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | high |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 0.50 |  | ✓ | insufficient |  |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
