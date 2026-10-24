## Mode: auto  (4/4 questions ran; headline over 4, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.92 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.59 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | none |
| answer correct (LLM judge): yes / partly / no | 3/1/0 |
| core fact recall (LLM judge) | 0.82 |
| atomic fact recall: cores + details, k of n for lists | 0.65 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.58 |
| core facts contradicted | 1 |
| penalties hit | 0 |
| bonus facts stated | 1/2 |
| correct abstention on unanswerable | 1/1 |
| false abstention on answerable | 0/3 |
| mean prompt tokens / question | 101,885 |
| of which from the provider's prompt cache | 20% |
| mean latency (s) | 16.32 |
| latency p50 / p95 (s), 4 questions in parallel | 17.3 / 24.3 |
| answer step: mean output tokens (what latency follows) | 1,310 |
| first failed step | answer: wrong statement 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.83 | 1.00 | 1.00 | 0.70 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 1.00 | 0.45 | 1.00 | 0.60 | 0.55 |  | ✓ | medium | answer: wrong statement |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 0.86 | 0.71 |  | ✓ | high |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
