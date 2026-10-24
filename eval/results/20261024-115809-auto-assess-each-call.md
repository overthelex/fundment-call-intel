## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.83 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.56 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_call 1 |
| answer correct (LLM judge): yes / partly / no | 3/1/0 |
| core fact recall (LLM judge) | 0.80 |
| atomic fact recall: cores + details, k of n for lists | 0.69 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.70 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 1/3 |
| correct abstention on unanswerable | 1/1 |
| false abstention on answerable | 0/3 |
| mean prompt tokens / question | 99,007 |
| mean latency (s) | 15.85 |
| latency p50 / p95 (s), 4 questions in parallel | 14.1 / 27.6 |
| answer step: mean output tokens (what latency follows) | 1,341 |
| first failed step | retrieval 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.85 | 1.00 | 0.50 | 1.00 | 1.00 | 0.91 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.64 | 1.00 | 0.36 | 0.96 | 0.40 | 0.36 |  | ✓ | high | retrieval (5 evidence turns not in context); attribution (1 failed citation) |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
