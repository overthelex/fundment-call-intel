## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.90 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.41 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | not_found 1, wrong_call 5, wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 20/8/1 |
| core fact recall (LLM judge) | 0.80 |
| atomic fact recall: cores + details, k of n for lists | 0.71 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.63 |
| core facts contradicted | 0 |
| penalties hit | 1 |
| bonus facts stated | 4/14 |
| correct abstention on unanswerable | 5/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 36,818 |
| of which from the provider's prompt cache | 15% |
| mean latency (s) | 11.60 |
| latency p50 / p95 (s), 4 questions in parallel | 9.6 / 25.6 |
| answer step: mean output tokens (what latency follows) | 1,337 |
| first failed step | answer 6, retrieval 2, attribution 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.68 | 1.00 | 0.36 | 1.00 | 1.00 | 0.76 |  | ✓ | high |  |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.75 | 1.00 | 1.00 | 0.70 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.86 | 1.00 | 0.34 | 0.96 | 1.00 | 0.94 |  | ✓ | high | attribution (2 failed citations) |
| q04 | aggregate | yes | 1.00 | 0.69 | 1.00 | 0.38 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q05 | aggregate | partly | 1.00 | 0.46 | 1.00 | 0.17 | 0.94 | 0.50 | 0.60 |  | ✓ | high | retrieval (13 evidence turns not in context); attribution (2 failed citations) |
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.64 | 1.00 | 1.00 | 0.89 |  | ✓ | high |  |
| q07 | aggregate | yes | 1.00 | 0.85 | 1.00 | 0.50 | 1.00 | 1.00 | 0.82 |  | ✓ | high |  |
| q08 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.22 | 1.00 | 0.83 | 0.62 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.86 | 1.00 | 0.36 | 0.94 | 0.60 | 0.45 |  | ✓ | high | retrieval (2 evidence turns not in context); attribution (2 failed citations) |
| q10 | aggregate | partly | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 1.00 | 0.71 |  | ✓ | high | answer (evidence was in context) |
| q11 | conflict | yes | 1.00 | 0.85 | 1.00 | 0.35 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | high | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 0.83 | 0.50 | 0.55 |  | ✓ | high | answer (evidence was in context); attribution (1 failed citation) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.43 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high |  |
| q16 | entity_resolution | yes | 1.00 | 0.50 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q17 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.38 | 1.00 | 0.80 | 0.60 |  | ✓ | medium | answer (evidence was in context) |
| q18 | single_call | no | 1.00 | 1.00 | 1.00 | 0.14 | 1.00 | 0.50 | 0.33 | 1 | ✓ | high | answer (evidence was in context) |
| q19 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | 0.73 |  | ✓ | high |  |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.47 | 1.00 | 0.80 | 0.78 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.17 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | yes | 1.00 | 0.94 | 1.00 | 0.06 | 1.00 | 0.50 | 0.50 |  | ✓ | high |  |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 0.93 | 1.00 | 0.71 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | 0.75 | - | 0.00 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
