## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.90 |
| cited recall (gold calls cited in the answer) | 0.94 |
| evidence cited (gold evidence turns cited) | 0.38 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 4, wrong_call 1 |
| answer correct (LLM judge): yes / partly / no | 17/12/0 |
| core fact recall (LLM judge) | 0.78 |
| atomic fact recall: cores + details, k of n for lists | 0.65 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.61 |
| core facts contradicted | 1 |
| penalties hit | 1 |
| bonus facts stated | 5/14 |
| correct abstention on unanswerable | 5/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 38,942 |
| of which from the provider's prompt cache | 40% |
| mean latency (s) | 11.44 |
| latency p50 / p95 (s), 4 questions in parallel | 10.0 / 25.9 |
| answer step: mean output tokens (what latency follows) | 1,304 |
| first failed step | answer 6, retrieval 4, attribution 2, answer: wrong statement 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.73 | 0.38 | 0.18 | 1.00 | 0.83 | 0.35 |  | ✓ | medium |  |
| q02 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.92 | 1.00 | 1.00 | 0.90 |  | ✓ | high |  |
| q03 | aggregate | partly | 1.00 | 0.83 | 1.00 | 0.21 | 0.96 | 0.67 | 0.50 |  | ✓ | high | retrieval (5 evidence turns not in context); attribution (1 failed citation) |
| q04 | aggregate | yes | 1.00 | 0.62 | 1.00 | 0.66 | 1.00 | 1.00 | 0.94 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.46 | 1.00 | 0.04 | 1.00 | 0.67 | 0.50 |  | ✓ | high | retrieval (13 evidence turns not in context) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 0.85 | 1.00 | 0.45 | 1.00 | 0.60 | 0.55 |  | ✓ | medium | answer: wrong statement |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.16 | 1.00 | 0.83 | 0.56 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.86 | 0.75 | 0.36 | 1.00 | 0.60 | 0.36 | 1 | ✓ | high | retrieval (2 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.40 | 0.96 | 1.00 | 0.50 |  | ✓ | high | attribution (1 failed citation) |
| q12 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | high |  |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 0.88 |  | ✓ | high |  |
| q17 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 0.70 | 0.80 | 0.70 |  | ✓ | medium | attribution (3 failed citations) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 0.75 | 0.83 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | 0.73 |  | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | partly | 1.00 | 1.00 | 0.50 | 0.64 | 1.00 | 0.75 | 0.80 |  | ✓ | medium | answer (evidence was in context) |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
