## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.81 |
| cited recall (gold calls cited in the answer) | 0.96 |
| evidence cited (gold evidence turns cited) | 0.35 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 2, wrong_call 1, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 8/3/0 |
| core fact recall (LLM judge) | 0.82 |
| atomic fact recall: cores + details, k of n for lists | 0.64 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.54 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 2/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 23,182 |
| mean latency (s) | 72.91 |
| latency p50 / p95 (s), 1 questions in parallel | 61.3 / 175.5 |
| answer step: mean output tokens (what latency follows) | 9,008 |
| first failed step | attribution 3, retrieval 2, answer 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.50 | 1.00 | 0.32 | 0.97 | 0.83 | 0.65 |  | ✓ | medium | attribution (1 failed citation) |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 0.80 | 0.40 |  | ✓ | medium |  |
| q03 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.34 | 1.00 | 0.83 | 0.81 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.72 | 1.00 | 0.55 | 0.95 | 1.00 | 0.94 |  | ✓ | high | attribution (2 failed citations) |
| q05 | aggregate | yes | 1.00 | 0.58 | 0.83 | 0.04 | 0.96 | 0.83 | 0.70 |  | ✓ | medium | attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 0.67 |  | ✓ | medium |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 0.75 | 0.20 | 1.00 | 0.80 | 0.64 |  | ✓ | medium | retrieval (3 evidence turns not in context) |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.22 | 1.00 | 0.67 | 0.56 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.64 | 1.00 | 0.29 | 1.00 | 0.20 | 0.18 |  | ✓ | high | retrieval (5 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.80 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
