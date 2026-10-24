## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.83 |
| cited recall (gold calls cited in the answer) | 0.91 |
| evidence cited (gold evidence turns cited) | 0.42 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_call 2 |
| answer correct (LLM judge): yes / partly / no | 6/5/0 |
| core fact recall (LLM judge) | 0.84 |
| atomic fact recall: cores + details, k of n for lists | 0.74 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.66 |
| core facts contradicted | 1 |
| penalties hit | 0 |
| bonus facts stated | 4/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 66,690 |
| of which from the provider's prompt cache | 14% |
| mean latency (s) | 19.79 |
| latency p50 / p95 (s), 1 questions in parallel | 14.5 / 63.5 |
| answer step: mean output tokens (what latency follows) | 2,234 |
| first failed step | retrieval 2, answer 2, answer: wrong statement 1, attribution 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.64 | 0.75 | 0.18 | 1.00 | 0.83 | 0.59 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q03 | aggregate | partly | 1.00 | 0.86 | 1.00 | 0.21 | 1.00 | 0.67 | 0.75 |  | ✓ | high | retrieval (4 evidence turns not in context) |
| q04 | aggregate | yes | 1.00 | 0.59 | 1.00 | 0.76 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.46 | 1.00 | 0.12 | 0.96 | 0.67 | 0.70 |  | ✓ | high | retrieval (13 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.45 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 1.00 | 0.45 | 1.00 | 0.60 | 0.55 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.25 | 1.00 | 0.67 | 0.62 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | yes | 1.00 | 0.93 | 0.75 | 0.64 | 0.97 | 1.00 | 0.73 |  | ✓ | high | attribution (1 failed citation) |
| q10 | aggregate | partly | 1.00 | 1.00 | 0.80 | 0.37 | 1.00 | 0.86 | 0.71 |  | ✓ | high | answer (evidence was in context) |
| q11 | conflict | yes | 1.00 | 0.85 | 0.67 | 0.15 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
