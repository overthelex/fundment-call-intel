## Mode: auto  (30/30 questions ran; headline over 29, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| cited recall (gold calls cited in the answer) | 0.92 |
| citation validity (quote found verbatim) | 1.00 |
| failed citations by kind | not_found 1 |
| answer correct (LLM judge): yes / partly / no | 13/15/1 |
| core fact recall (LLM judge) | 0.64 |
| atomic fact recall: cores + details, k of n for lists | 0.50 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.46 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 0/14 |
| correct abstention on unanswerable | 5/5 |
| false abstention on answerable | 0/24 |
| mean prompt tokens / question | 13,801 |
| mean latency (s) | 13.33 |

| id | kind | correct | ctx recall | cited recall | cit. valid | core | atomic | penalties | abstain ok | conf | missed calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| q01 | aggregate | yes | 1.00 | 0.88 | 1.00 | 0.83 | 0.59 |  | ✓ | high | CALL-007 |
| q02 | aggregate | partly | 1.00 | 0.60 | 1.00 | 0.60 | 0.40 |  | ✓ | high | CALL-001, CALL-004 |
| q03 | aggregate | partly | 1.00 | 1.00 | 1.00 | 0.67 | 0.25 |  | ✓ | high |  |
| q04 | aggregate | yes | 1.00 | 0.62 | 1.00 | 1.00 | 0.61 |  | ✓ | high | CALL-003, CALL-010, CALL-014 |
| q05 | aggregate | no | 1.00 | 1.00 | 1.00 | 0.17 | 0.20 |  | ✓ | high |  |
| q06 | entity_resolution | partly | 1.00 | 1.00 | 1.00 | 0.67 | 0.56 |  | ✓ | high |  |
| q07 | aggregate | partly | 1.00 | 1.00 | 1.00 | 0.80 | 0.64 |  | ✓ | medium |  |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.67 | 0.62 |  | ✓ | high |  |
| q09 | multi_call | partly | 1.00 | 0.75 | 1.00 | 0.00 | 0.00 |  | ✓ | high | CALL-013 |
| q10 | aggregate | yes | 1.00 | 1.00 | 0.93 | 1.00 | 0.79 |  | ✓ | high |  |
| q11 | conflict | yes | 1.00 | 0.33 | 1.00 | 1.00 | 0.50 |  | ✓ | high | CALL-001, CALL-012 |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.29 |  | ✓ | medium |  |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.36 |  | ✓ | high |  |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.33 |  | ✓ | high |  |
| q15 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.40 |  | ✓ | high |  |
| q16 | entity_resolution | partly | 1.00 | 1.00 | 1.00 | 0.25 | 0.25 |  | ✓ | high |  |
| q17 | single_call | yes | 1.00 | 1.00 | 1.00 | 0.80 | 0.50 |  | ✓ | medium |  |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.25 | 0.33 |  | ✓ | medium |  |
| q19 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.75 | 0.73 |  | ✓ | high |  |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 0.78 |  | ✓ | high |  |
| q21 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q22 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.50 |  | ✓ | high |  |
| q23 | single_call | yes | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |  | ✓ | high |  |
| q24 | conflict | partly | 1.00 | 1.00 | 1.00 | 0.50 | 0.40 |  | ✓ | low |  |
| q25 | unanswerable | yes | - | - | - | 1.00 | 0.67 |  | ✓ | insufficient |  |
| q26 | unanswerable | yes | - | - | 1.00 | 0.50 | 0.60 |  | ✓ | insufficient |  |
| q27 | unanswerable | yes | - | - | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q28 | unanswerable | yes | - | - | - | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q29 | unanswerable | yes | - | - | 1.00 | 1.00 | 1.00 |  | ✓ | insufficient |  |
| q30 (bonus) | multi_call | no | 0.50 | 0.50 | 1.00 | 0.67 | 0.40 |  | ✓ | medium | CALL-010 |
