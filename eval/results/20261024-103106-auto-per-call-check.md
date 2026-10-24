## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 1.00 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.38 |
| citation validity (quote found verbatim) | 0.98 |
| failed citations by kind | not_found 1 |
| answer correct (LLM judge): yes / partly / no | 2/2/0 |
| core fact recall (LLM judge) | 0.78 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.61 |
| core facts contradicted | 0 |
| penalties hit | 1 |
| bonus facts stated | 1/3 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/4 |
| mean prompt tokens / question | 31,272 |
| mean latency (s) | 16.45 |
| latency p50 / p95 (s), 4 questions in parallel | 17.5 / 22.7 |
| answer step: mean output tokens (what latency follows) | 1,530 |
| first failed step | answer 2 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.09 | 1.00 | 0.50 | 0.50 |  | ✓ | high | answer (evidence was in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 0.86 | 0.71 |  | ✓ | high |  |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.44 | 0.93 | 0.75 | 0.64 | 1 | ✓ | high | answer (evidence was in context); attribution (1 failed citation) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
