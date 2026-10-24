## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.83 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.41 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 1 |
| answer correct (LLM judge): yes / partly / no | 8/3/0 |
| core fact recall (LLM judge) | 0.88 |
| atomic fact recall: cores + details, k of n for lists | 0.73 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.65 |
| core facts contradicted | 1 |
| penalties hit | 0 |
| bonus facts stated | 4/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 56,703 |
| of which from the provider's prompt cache | 31% |
| mean latency (s) | 15.66 |
| latency p50 / p95 (s), 1 questions in parallel | 14.4 / 22.3 |
| answer step: mean output tokens (what latency follows) | 2,362 |
| first failed step | attribution 2, answer: wrong statement 1, answer 1, retrieval 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.50 | 1.00 | 0.36 | 0.96 | 0.83 | 0.65 |  | ✓ | medium | attribution (1 failed citation) |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.92 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.83 | 1.00 | 0.34 | 0.98 | 1.00 | 0.88 |  | ✓ | high | attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.66 | 1.00 | 0.48 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q05 | aggregate | yes | 1.00 | 0.54 | 1.00 | 0.17 | 1.00 | 0.83 | 0.90 |  | ✓ | high |  |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.45 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 1.00 | 0.55 | 1.00 | 0.80 | 0.55 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.22 | 1.00 | 0.67 | 0.62 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.93 | 1.00 | 0.29 | 1.00 | 0.60 | 0.45 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | high |  |
