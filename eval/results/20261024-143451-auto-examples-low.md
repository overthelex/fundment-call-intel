## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.83 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.45 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 1, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 8/3/0 |
| core fact recall (LLM judge) | 0.95 |
| atomic fact recall: cores + details, k of n for lists | 0.80 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.70 |
| core facts contradicted | 1 |
| penalties hit | 1 |
| bonus facts stated | 2/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 51,504 |
| mean latency (s) | 16.72 |
| latency p50 / p95 (s), 1 questions in parallel | 15.6 / 22.4 |
| answer step: mean output tokens (what latency follows) | 2,841 |
| first failed step | attribution 2, answer: wrong statement 1, answer 1, retrieval 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.41 | 1.00 | 0.32 | 1.00 | 1.00 | 0.82 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.75 | 1.00 | 1.00 | 0.80 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.45 | 0.99 | 1.00 | 0.94 |  | ✓ | high | attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.69 | 1.00 | 0.59 | 0.98 | 1.00 | 0.94 |  | ✓ | high | attribution (1 failed citation) |
| q05 | aggregate | yes | 1.00 | 0.58 | 1.00 | 0.21 | 1.00 | 0.83 | 0.90 |  | ✓ | high |  |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.82 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.90 | 1.00 | 0.45 | 1.00 | 0.80 | 0.64 |  | ✓ | high | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.22 | 1.00 | 0.83 | 0.75 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.86 | 1.00 | 0.36 | 0.97 | 1.00 | 0.55 | 1 | ✓ | high | retrieval (2 evidence turns not in context); attribution (1 failed citation) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.53 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.30 | 1.00 | 1.00 | 0.75 |  | ✓ | medium |  |
