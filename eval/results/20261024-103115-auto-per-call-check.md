## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 1.00 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.39 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | none |
| answer correct (LLM judge): yes / partly / no | 3/1/0 |
| core fact recall (LLM judge) | 0.85 |
| atomic fact recall: cores + details, k of n for lists | 0.70 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.59 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 0/3 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/4 |
| mean prompt tokens / question | 31,310 |
| mean latency (s) | 17.20 |
| latency p50 / p95 (s), 4 questions in parallel | 15.6 / 23.9 |
| answer step: mean output tokens (what latency follows) | 1,327 |
| first failed step | answer 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.28 | 1.00 | 0.83 | 0.62 |  | ✓ | high |  |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | 0.73 |  | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.41 | 1.00 | 0.80 | 0.67 |  | ✓ | high |  |
