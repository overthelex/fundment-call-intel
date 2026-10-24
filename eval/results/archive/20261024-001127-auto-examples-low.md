## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.82 |
| cited recall (gold calls cited in the answer) | 0.96 |
| evidence cited (gold evidence turns cited) | 0.39 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_call 3 |
| answer correct (LLM judge): yes / partly / no | 6/4/1 |
| core fact recall (LLM judge) | 0.84 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.61 |
| core facts contradicted | 1 |
| penalties hit | 1 |
| bonus facts stated | 1/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 24,441 |
| mean latency (s) | 17.15 |
| latency p50 / p95 (s), 1 questions in parallel | 18.2 / 26.3 |
| answer step: mean output tokens (what latency follows) | 2,293 |
| first failed step | retrieval 3, answer 1, attribution 1, answer: wrong statement 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.45 | 1.00 | 0.18 | 1.00 | 0.83 | 0.47 |  | ✓ | high |  |
| q02 | aggregate | partly | 1.00 | 1.00 | 1.00 | 0.58 | 1.00 | 1.00 | 0.60 | 1 | ✓ | high | answer (evidence was in context) |
| q03 | aggregate | yes | 1.00 | 0.83 | 0.83 | 0.34 | 0.95 | 0.83 | 0.75 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.52 | 1.00 | 1.00 | 0.83 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.54 | 1.00 | 0.17 | 0.97 | 0.67 | 0.60 |  | ✓ | high | retrieval (11 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.55 | 1.00 | 0.83 | 0.78 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.90 | 0.75 | 0.45 | 1.00 | 0.80 | 0.82 |  | ✓ | medium | retrieval (2 evidence turns not in context) |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.64 | 1.00 | 0.29 | 1.00 | 0.60 | 0.36 |  | ✓ | high | retrieval (5 evidence turns not in context) |
| q10 | aggregate | no | 1.00 | 1.00 | 1.00 | 0.58 | 1.00 | 0.71 | 0.64 |  | ✓ | high | answer: wrong statement |
| q11 | conflict | yes | 1.00 | 0.80 | 1.00 | 0.25 | 1.00 | 1.00 | 0.75 |  | ✓ | medium |  |
