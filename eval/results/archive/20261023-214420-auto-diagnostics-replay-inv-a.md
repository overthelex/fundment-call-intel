## Mode: auto  (7/7 questions ran; headline over 7, bonus questions listed separately)

Judge: `claude-cli:opus`

| metric | value |
|---|---|
| context recall (gold calls reached the model) | 1.00 |
| evidence recall (gold evidence turns reached the model) | 1.00 |
| cited recall (gold calls cited in the answer) | 1.00 |
| evidence cited (gold evidence turns cited) | 0.32 |
| citation validity (quote found verbatim) | 0.99 |
| failed citations by kind | wrong_speaker 1 |
| answer correct (LLM judge): yes / partly / no | 2/5/0 |
| core fact recall (LLM judge) | 0.68 |
| atomic fact recall: cores + details, k of n for lists | 0.54 |
| compound fact recall: old scoring, 1 / 0.5 / 0 | 0.53 |
| core facts contradicted | 0 |
| penalties hit | 0 |
| bonus facts stated | 1/1 |
| correct abstention on unanswerable | 0/0 |
| false abstention on answerable | 0/7 |
| mean prompt tokens / question | 9,817 |
| mean latency (s) | 26.16 |
| first failed step | answer 5, attribution 1 |

| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q06 | entity_resolution | yes | 1.00 | 1.00 | 1.00 | 0.45 | 1.00 | 0.83 | 0.67 |  | ✓ | high |  |
| q08 | multi_call | partly | 1.00 | 1.00 | 1.00 | 0.19 | 1.00 | 0.67 | 0.50 |  | ✓ | medium | answer (evidence was in context) |
| q12 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | 0.50 | 0.29 |  | ✓ | medium | answer (evidence was in context) |
| q13 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.18 | 1.00 | 0.50 | 0.36 |  | ✓ | high | answer (evidence was in context) |
| q14 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.50 | 0.33 |  | ✓ | high | answer (evidence was in context) |
| q18 | single_call | partly | 1.00 | 1.00 | 1.00 | 0.29 | 1.00 | 0.75 | 0.83 |  | ✓ | high | answer (evidence was in context) |
| q20 | multi_call | yes | 1.00 | 1.00 | 1.00 | 0.35 | 0.92 | 1.00 | 0.78 |  | ✓ | high | attribution (1 failed citation) |
