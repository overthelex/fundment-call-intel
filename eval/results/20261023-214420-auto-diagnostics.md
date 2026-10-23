## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 0.82 |
| cited recall (gold calls cited in the answer) | 0.96 |
| evidence cited (gold evidence turns cited) | 0.26 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 14/15/0 |
| core fact recall (LLM judge) | 0.70 |
| atomic fact recall: cores + details, k of n for lists | 0.57 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.52 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 3/14 |
| correct abstention on unanswerable | 5/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 14,523 |
| mean latency (s) | 16.16 |
| first failed step | answer 7, retrieval 6, attribution 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | partly | 1.00 | 0.32 | 0.88 | 0.18 | 1.00 | 0.67 | 0.35 |  | ✓ | medium | retrieval (15 evidence turns not in context) |
| q02 | aggregate | yes | 1.00 | 0.92 | 1.00 | 0.67 | 1.00 | 1.00 | 0.70 |  | ✓ | high |  |
| q03 | aggregate | yes | 1.00 | 0.66 | 1.00 | 0.14 | 1.00 | 0.83 | 0.62 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.41 | 0.88 | 0.24 | 1.00 | 1.00 | 0.56 |  | ✓ | medium |  |
| q05 | aggregate | partly | 1.00 | 0.08 | 0.83 | 0.00 | 1.00 | 0.33 | 0.20 |  | ✓ | medium | retrieval (22 evidence turns not in context) |
| q06 | entity_resolution | partly | 1.00 | 1.00 | 1.00 | 0.36 | 1.00 | 0.67 | 0.44 |  | ✓ | high | answer (evidence was in context) |
| q07 | aggregate | partly | 1.00 | 0.60 | 0.75 | 0.25 | 1.00 | 0.60 | 0.55 |  | ✓ | medium | retrieval (8 evidence turns not in context) |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.09 | 1.00 | 0.50 | 0.31 |  | ✓ | high | answer (evidence was in context) |
| q09 | multi_call | partly | 1.00 | 0.36 | 0.75 | 0.07 | 1.00 | 0.20 | 0.18 |  | ✓ | high | retrieval (9 evidence turns not in context) |
| q10 | aggregate | yes | 1.00 | 1.00 | 1.00 | 0.32 | 0.90 | 0.86 | 0.71 |  | ✓ | medium | attribution (1 failed citation) |
| q11 | conflict | yes | 1.00 | 0.80 | 1.00 | 0.25 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.43 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.27 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q15 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.40 |  | ✓ | high |  |
| q16 | entity_resolution | partly | 1.00 | 0.50 | 1.00 | 0.33 | 1.00 | 0.75 | 0.75 |  | ✓ | high | retrieval (3 evidence turns not in context) |
| q17 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.80 | 0.60 |  | ✓ | medium |  |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.21 | 1.00 | 0.50 | 0.33 |  | ✓ | medium | answer (evidence was in context) |
| q19 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | 0.73 |  | ✓ | high |  |
| q20 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.24 | 1.00 | 0.80 | 0.56 |  | ✓ | high | answer (evidence was in context) |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.17 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 0.94 | 1.00 | 0.06 | 1.00 | 0.50 | 0.50 |  | ✓ | high | retrieval (1 evidence turn not in context) |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | yes | 1.00 | 1.00 | 1.00 | 0.36 | 1.00 | 1.00 | 1.00 |  | ✓ | medium |  |
| q25 | unanswerable | yes | - | 1.00 | - | 0.00 | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | partly | - | 1.00 | - | 0.33 | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | 1.00 | - | 0.50 | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | partly | - | 1.00 | - | 0.00 | 1.00 | 0.50 | 0.25 |  | ✓ | insufficient |  |
| q30 (bonus) | multi_call | no | 0.50 | 0.44 | 0.50 | 0.22 | 1.00 | 0.67 | 0.40 |  | ✗ | insufficient | abstention: declined |
