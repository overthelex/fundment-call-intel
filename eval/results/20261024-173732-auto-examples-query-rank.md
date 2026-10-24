## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.86 |
| cited recall (gold calls cited in the answer) | 0.98 |
| evidence cited (gold evidence turns cited) | 0.45 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_call 3 |
| answer correct (LLM judge): yes / partly / no | 8/3/0 |
| core fact recall (LLM judge) | 0.87 |
| atomic fact recall: cores + details, k of n for lists | 0.74 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.67 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 6/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 57,017 |
| mean latency (s) | 15.38 |
| latency p50 / p95 (s), 1 questions in parallel | 14.4 / 21.9 |
| answer step: mean output tokens (what latency follows) | 2,510 |
| first failed step | retrieval 2, attribution 1, answer 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.64 | 1.00 | 0.36 | 1.00 | 1.00 | 0.76 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.92 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.34 | 0.95 | 0.83 | 0.62 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.69 | 1.00 | 0.52 | 1.00 | 1.00 | 0.94 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.50 | 1.00 | 0.12 | 0.96 | 0.50 | 0.60 |  | ✓ | high | retrieval (12 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.55 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.95 | 1.00 | 0.55 | 1.00 | 0.80 | 0.64 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.34 | 1.00 | 0.83 | 0.69 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 1.00 | 0.75 | 0.29 | 1.00 | 0.60 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.58 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.40 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
