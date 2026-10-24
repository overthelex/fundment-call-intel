## Mode: auto  (11/11 questions ran; headline over 11, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.82 |
| cited recall (gold calls cited in the answer) | 0.95 |
| evidence cited (gold evidence turns cited) | 0.41 |
| citation validity (quote found verbatim) | 0.98 |
| failed citations by kind | not_found 2, wrong_call 1, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 6/4/1 |
| core fact recall (LLM judge) | 0.77 |
| atomic fact recall: cores + details, k of n for lists | 0.69 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.56 |
| core facts contradicted | 1 |
| penalties hit | 1 |
| bonus facts stated | 3/9 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/11 |
| mean prompt tokens / question | 55,770 |
| of which from the provider's prompt cache | 21% |
| mean latency (s) | 15.09 |
| latency p50 / p95 (s), 1 questions in parallel | 14.8 / 22.4 |
| answer step: mean output tokens (what latency follows) | 2,411 |
| first failed step | retrieval 4, attribution 2, answer: wrong statement 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | partly | 1.00 | 0.59 | 1.00 | 0.32 | 1.00 | 0.67 | 0.59 |  | ✓ | medium | retrieval (9 evidence turns not in context) |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.83 | 1.00 | 1.00 | 0.70 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.86 | 1.00 | 0.21 | 0.98 | 0.83 | 0.56 |  | ✓ | high | attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.66 | 1.00 | 0.45 | 0.97 | 1.00 | 0.94 |  | ✓ | high | attribution (1 failed citation) |
| q05 | aggregate | partly | 1.00 | 0.42 | 1.00 | 0.12 | 1.00 | 0.67 | 0.60 |  | ✓ | high | retrieval (14 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.91 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q07 | aggregate | no | 1.00 | 0.85 | 1.00 | 0.50 | 1.00 | 0.40 | 0.45 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.22 | 1.00 | 0.83 | 0.69 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.93 | 0.75 | 0.29 | 0.87 | 0.60 | 0.55 | 1 | ✓ | high | retrieval (1 evidence turn not in context); attribution (2 failed citations) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.71 |  | ✓ | high |  |
| q11 | conflict | partly | 1.00 | 0.85 | 0.67 | 0.20 | 1.00 | 0.50 | 0.75 |  | ✓ | medium | retrieval (3 evidence turns not in context) |
