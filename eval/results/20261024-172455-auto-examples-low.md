## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.84 |
| cited recall (gold calls cited in the answer) | 0.96 |
| evidence cited (gold evidence turns cited) | 0.44 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 4 |
| answer correct (LLM judge): yes / partly / no | 9/2/0 |
| core fact recall (LLM judge) | 0.92 |
| atomic fact recall: cores + details, k of n for lists | 0.75 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.69 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 6/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 55,233 |
| mean latency (s) | 15.04 |
| latency p50 / p95 (s), 1 questions in parallel | 15.2 / 21.1 |
| answer step: mean output tokens (what latency follows) | 2,410 |
| first failed step | retrieval 2 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.68 | 1.00 | 0.50 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.83 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.83 | 0.83 | 0.31 | 1.00 | 1.00 | 0.56 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.66 | 1.00 | 0.38 | 1.00 | 1.00 | 0.61 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.46 | 1.00 | 0.17 | 0.97 | 0.67 | 0.80 |  | ✓ | high | retrieval (13 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.55 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.55 | 1.00 | 0.80 | 0.73 |  | ✓ | medium |  |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.28 | 1.00 | 0.83 | 0.69 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.93 | 0.75 | 0.50 | 0.87 | 0.80 | 0.45 |  | ✓ | high | retrieval (1 evidence turn not in context); attribution (4 failed citations) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.35 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
