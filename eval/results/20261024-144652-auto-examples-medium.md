## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.84 |
| cited recall (gold calls cited in the answer) | 0.95 |
| evidence cited (gold evidence turns cited) | 0.39 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_speaker 2 |
| answer correct (LLM judge): yes / partly / no | 7/4/0 |
| core fact recall (LLM judge) | 0.82 |
| atomic fact recall: cores + details, k of n for lists | 0.65 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.62 |
| core facts contradicted | 1 |
| penalties hit | 1 |
| bonus facts stated | 3/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 51,838 |
| mean latency (s) | 63.77 |
| latency p50 / p95 (s), 1 questions in parallel | 59.1 / 197.4 |
| answer step: mean output tokens (what latency follows) | 9,200 |
| first failed step | retrieval 2, attribution 1, answer: wrong statement 1, answer 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.55 | 1.00 | 0.36 | 1.00 | 1.00 | 0.71 |  | ✓ | medium |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.75 | 1.00 | 1.00 | 0.80 |  | ✓ | medium |  |
| q03 | aggregate | partly | 1.00 | 0.79 | 0.83 | 0.17 | 0.95 | 0.67 | 0.31 |  | ✓ | high | retrieval (6 evidence turns not in context); attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.76 | 1.00 | 0.52 | 1.00 | 1.00 | 0.67 |  | ✓ | medium |  |
| q05 | aggregate | yes | 1.00 | 0.58 | 0.67 | 0.08 | 0.93 | 0.83 | 0.70 |  | ✓ | medium | attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.90 | 1.00 | 0.45 | 1.00 | 0.80 | 0.64 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.16 | 1.00 | 0.33 | 0.44 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.93 | 1.00 | 0.36 | 1.00 | 0.40 | 0.18 | 1 | ✓ | high | retrieval (1 evidence turn not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.79 |  | ✓ | medium |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.30 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
