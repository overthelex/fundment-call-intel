## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.90 |
| cited recall (gold calls cited in the answer) | 0.99 |
| evidence cited (gold evidence turns cited) | 0.42 |
| citation validity (quote found verbatim) | 0.98 |
| failed citations by kind | not_found 2, wrong_call 5, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 17/12/0 |
| core fact recall (LLM judge) | 0.79 |
| atomic fact recall: cores + details, k of n for lists | 0.68 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.60 |
| core facts contradicted | 0 |
| penalties hit | 2 |
| bonus facts stated | 4/14 |
| correct abstention on unanswerable | 4/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 35,310 |
| of which from the provider's prompt cache | 22% |
| mean latency (s) | 11.69 |
| latency p50 / p95 (s), 4 questions in parallel | 9.4 / 29.8 |
| answer step: mean output tokens (what latency follows) | 1,496 |
| first failed step | answer 8, attribution 3, retrieval 3, abstention: answered 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.55 | 1.00 | 0.23 | 0.95 | 1.00 | 0.71 |  | ✓ | high | attribution (1 failed citation) |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.67 | 1.00 | 1.00 | 0.60 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.90 | 1.00 | 0.41 | 0.98 | 0.83 | 0.75 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.62 | 1.00 | 0.48 | 1.00 | 1.00 | 0.83 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.46 | 1.00 | 0.17 | 0.97 | 0.50 | 0.70 |  | ✓ | high | retrieval (13 evidence turns not in context); attribution (1 failed citation) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.90 | 0.75 | 0.40 | 0.96 | 1.00 | 0.64 |  | ✓ | medium | attribution (1 failed citation) |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.67 | 0.62 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.86 | 1.00 | 0.29 | 0.92 | 0.60 | 0.36 | 1 | ✓ | high | retrieval (2 evidence turns not in context); attribution (2 failed citations) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 0.86 | 0.71 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.35 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 0.80 | 0.50 | 0.45 |  | ✓ | high | answer (evidence was in context); attribution (1 failed citation) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.40 |  | ✓ | high | answer (evidence was in context) |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.60 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.67 |  | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | 0.64 | 1 | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.59 | 1.00 | 1.00 | 0.67 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.33 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.12 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.25 | 1.00 | 1.00 | 1.00 |  | ✗ | high | abstention: answered |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
