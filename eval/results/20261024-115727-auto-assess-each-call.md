## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.70 |
| cited recall (gold calls cited in the answer) | 0.92 |
| evidence cited (gold evidence turns cited) | 0.48 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | none |
| answer correct (LLM judge): yes / partly / no | 3/1/0 |
| core fact recall (LLM judge) | 0.80 |
| atomic fact recall: cores + details, k of n for lists | 0.63 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.67 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 2/3 |
| correct abstention on unanswerable | 1/1 |
| false abstention on answerable | 0/3 |
| mean prompt tokens / question | 96,872 |
| mean latency (s) | 13.80 |
| latency p50 / p95 (s), 4 questions in parallel | 16.5 / 22.1 |
| answer step: mean output tokens (what latency follows) | 1,382 |
| first failed step | retrieval 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.55 | 1.00 | 1.00 | 0.73 |  | ✓ | medium |  |
| q09 | multi_call | partly | 1.00 | 0.21 | 0.75 | 0.07 | 1.00 | 0.40 | 0.27 |  | ✓ | high | retrieval (11 evidence turns not in context) |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
