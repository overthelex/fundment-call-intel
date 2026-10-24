## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.86 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.52 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | none |
| answer correct (LLM judge): yes / partly / no | 2/2/0 |
| core fact recall (LLM judge) | 0.73 |
| atomic fact recall: cores + details, k of n for lists | 0.63 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.60 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 2/3 |
| correct abstention on unanswerable | 1/1 |
| false abstention on answerable | 0/3 |
| mean prompt tokens / question | 98,858 |
| mean latency (s) | 17.57 |
| latency p50 / p95 (s), 4 questions in parallel | 20.8 / 23.5 |
| answer step: mean output tokens (what latency follows) | 1,501 |
| first failed step | retrieval 2 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.92 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.95 | 1.00 | 0.50 | 1.00 | 0.80 | 0.73 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q09 | multi_call | partly | 1.00 | 0.64 | 1.00 | 0.14 | 1.00 | 0.40 | 0.27 |  | ✓ | high | retrieval (5 evidence turns not in context) |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
