## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.90 |
| cited recall (gold calls cited in the answer) | 0.98 |
| evidence cited (gold evidence turns cited) | 0.42 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 5 |
| answer correct (LLM judge): yes / partly / no | 16/13/0 |
| core fact recall (LLM judge) | 0.77 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.59 |
| core facts contradicted | 1 |
| penalties hit | 0 |
| bonus facts stated | 6/14 |
| correct abstention on unanswerable | 4/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 34,067 |
| mean latency (s) | 10.79 |
| latency p50 / p95 (s), 4 questions in parallel | 8.8 / 23.2 |
| answer step: mean output tokens (what latency follows) | 1,390 |
| first failed step | answer 8, retrieval 4, attribution 1, answer: wrong statement 1, abstention: answered 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.64 | 1.00 | 0.36 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.75 | 1.00 | 1.00 | 0.70 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.34 | 0.95 | 1.00 | 0.94 |  | ✓ | high | attribution (3 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.62 | 0.88 | 0.48 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.50 | 1.00 | 0.08 | 1.00 | 0.17 | 0.20 |  | ✓ | medium | retrieval (12 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.45 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 1.00 | 0.55 | 1.00 | 0.80 | 0.73 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.12 | 1.00 | 0.50 | 0.38 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.93 | 1.00 | 0.43 | 0.93 | 0.80 | 0.45 |  | ✓ | high | retrieval (1 evidence turn not in context); attribution (2 failed citations) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.58 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 0.67 | 0.25 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.75 | 1.00 | 0.75 | 0.57 |  | ✓ | high | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.18 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | partly | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 0.75 | 0.75 |  | ✓ | medium | retrieval (3 evidence turns not in context) |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.60 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.14 | 1.00 | 0.25 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 0.86 | 0.75 | 0.64 |  | ✓ | high | answer (evidence was in context); attribution (1 failed citation) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.59 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.06 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 1.00 | 1.00 | 0.71 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | yes | - | 1.00 | - | 0.33 | 1.00 | 1.00 | 0.80 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 0.50 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
