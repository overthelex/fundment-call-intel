# Evaluation

The README has the short version. This file has the rubric, the full results, how far the judge can be
trusted, three worked examples, and where the gold set comes from.

## What is measured and why

The question behind the design: when an answer is wrong, which step failed? Each metric isolates one
step, and the cheap deterministic ones come first so the noisy LLM-judged ones are not the only signal.

| metric | what it tells you | how |
|---|---|---|
| context recall | did routing put the right calls in front of the model? | gold calls ∩ context calls |
| evidence recall | did retrieval put the right *turns* in front of the model? | gold evidence turns ∩ context turns |
| cited recall | did the answer actually use them? | gold calls ∩ calls with a verified citation |
| evidence cited | which supporting turns did it cite? (reading aid: gold lists all, answers cite a few) | gold evidence turns ∩ cited turns |
| citation validity | are the quotes real and correctly attributed? | code check against the transcript |
| correct (yes / partly / no) | is the main point right? | LLM judge against the rubric |
| core / atomic fact recall | how complete is it? | LLM judge, per core and per detail |
| penalties | did it make a statement the gold set rules out? | LLM judge |
| abstention | does it say "not in the data" when, and only when, it should? | LLM judge (`declines`) |
| tokens, latency | what does it cost? | API usage per question |
| first failed step | where to look first | rules over the metrics above, in pipeline order |

Evidence turns come from the timestamps in each question's gold `evidence` ("CALL-001 [01:51] … /
[02:12] …", ranges like "[07:09]-[07:17]"); all 382 resolve to a turn, 381 exactly. The `failure`
label is: abstention (declined or answered when it should not), else, for answers not judged "yes",
"answer: wrong statement" if a core fact is contradicted, "retrieval" if some evidence turn never
reached the context, otherwise "answer (evidence was in context)"; failed citations add "attribution".

Reading them together: low context recall means routing failed; good context recall with low evidence
recall means retrieval found the call but not the turn. High context recall with
low cited recall means the answer step ignored evidence. Low citation validity means invented or
misattributed quotes. Low fact recall with good citations means the answer is incomplete despite good
sources. Every run is compared with a brute-force baseline (`--mode full`, all 20 transcripts in the
prompt), because the question for a RAG system is whether it beats the obvious alternative, not only
its absolute score.

## The gold set

`questions.yaml` has 30 questions covering what the task warns about: single-call lookups, cross-call
themes, call-kind filters ("in renewal calls…"), name mismatches ("Acme Corp" is Acme Logistics),
ambiguous questions, unanswerable and near-miss questions (ISO 27001 when only SOC 2 is mentioned),
and vendor contradictions. Each question has:

- `expected_calls` (must be found) and `acceptable_calls` (may be cited without penalty);
- `should_abstain` for questions the data cannot answer;
- **required facts**, each split into a *core* claim and supporting *details*; for enumerations
  ("which companies…") covering k of n details counts as full coverage (`min_details`);
- **bonus facts**, credited when present but never required;
- **penalties**, statements a correct answer must not make (attributing a customer's figure to the
  vendor, naming SAP as Kestrel's ERP).

q30, a two-step inference, is marked `bonus_question` and kept out of the headline numbers.
`GOLD_NOTES.md` lists the dataset's traps found while annotating.

The judge (Claude Opus, a different vendor from the answering model) sees the question, the answer and
the rubric, and returns per fact: core `supported` / `missing` / `contradicted`, which details are
covered, which bonus facts and penalties are hit, an overall `correct` verdict and `declines`. Only an
answer that asserts the opposite counts as `contradicted`; one that declines to conclude counts as
`missing`. An answer that reports both sides of a conflict is not a decline.

Completeness is reported three ways from the same verdicts, because the number depends heavily on how
you count:

- **core recall**: share of required core claims stated (did it get the points);
- **atomic recall**: cores and details as separate atoms, enumerations capped at k;
- **compound recall** (the original scoring): 1 if the core and every detail, 0.5 if the core only.

## Results

The current code, 29 headline questions (q30 excluded), `gpt-5.4-mini` answering, Claude Opus judging.
The pipeline and the baseline ran on 24.10 from a fresh clone, following the README; the second
pipeline run is the same code on another index. Files: `results/README.md`.

| | pipeline (`auto`), fresh clone | pipeline, 2nd run | whole dataset in prompt (`full`) |
|---|---|---|---|
| context recall | 1.00 | 1.00 | 1.00 (by construction) |
| evidence recall | 0.87 | 0.87 | 1.00 (by construction) |
| cited recall | 0.97 | 0.98 | 0.93 |
| citation validity | **0.99** | **0.99** | 0.97 |
| failed citations: not found · wrong call · wrong speaker | 1 · 3 · 1 | 2 · 2 · 0 | 4 · 10 · 3 |
| answer correct: yes / partly / no | **19 / 9 / 1** | 18 / 10 / 1 | 13 / 14 / 2 |
| core fact recall | 0.79 | 0.80 | 0.73 |
| atomic fact recall | 0.67 | 0.67 | 0.61 |
| compound fact recall (strictest) | 0.63 | 0.65 | 0.55 |
| core facts contradicted · penalties hit | 0 · 2 | 2 · 1 | 1 · 3 |
| correct abstention on unanswerable | 5 / 5 | 4 / 5 | 5 / 5 |
| false abstention on answerable | 0 / 24 | 0 / 24 | 0 / 24 |
| prompt tokens / question | **17K** | 17K | 123K |
| latency mean / p95, 4 in parallel | 8.6 / 21.0 s | 9.9 / 21.7 s | 11.3 / 38.5 s |

`results/comparison.md` has the verdicts per question. The two pipeline runs disagree on 6 of 30
(q05, q07, q10, q11, q12, q15). The baseline differs from both pipeline runs on 5 questions where the
two agree: worse on q03, q08, q16 and q24, better on q30.

### How far the judge can be trusted

Re-judging the *same* answers with the same Claude judge moved 6 of 30 verdicts, all between yes and
partly (`results/archive/20261017-155023-auto-judge-repeat-opus`). A second judge model (`gpt-5.4`)
agreed with Claude on 22 of 30 and was stricter on the yes/partly line
(`results/archive/20261017-155023-auto-judge-gpt54`). Both checks were made on answers of an earlier
version of the code; what they measure is the judge, not the pipeline. So the yes/partly boundary is
noise of about ±6 questions. The yes-vs-no line, the abstentions and the deterministic metrics
(context and evidence recall, citation validity, tokens) are stable. A majority of three judge passes
would cut the noise.

### Reading the numbers

- **Routing is not the bottleneck; for cross-call questions retrieval is.** Every gold call reaches
  the model, but the turn that answers does not always: evidence recall is ~1.0 when whole calls are
  sent and lower for questions across calls, which use the notes written at ingestion (q09 about a
  third, q05 about a half). The answer cannot list what it never saw.
- **The pipeline is at least as good as the baseline at about 1/7 of the input tokens.** The gap in
  "yes" (18–19 vs 13) is within the judge noise, so the claim is "no worse"; the per-question
  differences are not on unstable questions, and q24 is a clear one (example 1).
- **Quotes are more reliable with less context**: 4–5 failed citations for the pipeline vs 17 for
  the baseline, mostly *wrong call*: real quotes attached to the wrong customer (example 3). Wrong
  call and not found are reported separately because they are different failures (attribution vs
  invention); both count as errors.
- **Unanswerable and near-miss questions work**: "Which ERP does Kestrel use?" (they decline to
  say), ISO 27001 (only SOC 2 is mentioned), an Enterprise price (always "custom"). The one miss
  (q29, second run) gave the price as custom but was judged as not declining.
- **Completeness depends on how you count**: about 0.63 compound, 0.67 atomic, 0.8 core. The answers
  usually get the points and drop supporting detail.

### Where it fails

- **Single-call details (q13, q14, q15, q18)**: whole transcript in context, the answer gives the main
  point and leaves out a required detail; first failed step "answer".
- **Cross-call patterns (q09 "how do renewals differ from new business?")**: a pattern that shows
  only across calls is in no single call's notes; evidence recall about a third. `--across map`
  reaches more turns (README, *Options for questions across calls*) and still misses it.
- **Unstable: q11 (vendor contradictions)** found both contradictions in one run and only the SSO one
  in the other (example 2).
- **Judgement: q07 ("who is most likely to buy?")** was "no" in one run for putting BrightPath in the
  top tier without its security blocker, "partly" in the other.
- **q30 (bonus, two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the
  question and the Juniper call to answer it. The planner routes to Verity only, so the pipeline
  declines; the baseline, which sees every call, answers it.

## Three worked examples

From the fresh-clone runs (`results/20261024-094317-auto-fresh-clone`, `…-094601-full-fresh-clone`)
unless stated otherwise, abridged.

### 1. Right, and the baseline gets it wrong: q24

> Is SSO available on OrbitFlow's Growth plan?

In the data one AE says "SSO's included on all our plans" (CALL-006 [07:23]) and later that he is
only "fairly sure"; in nine other calls three reps say SAML SSO is Enterprise. Retrieval alone
returns the few passages most similar to the question, so the answer step also gets every vendor
statement on the topic from the claims table and must weigh a conflict on fixed criteria (how many
people, how specific, later hedged or corrected, who said it, recency).

Pipeline, verdict **yes**:

> OrbitFlow staff mostly said SSO is an Enterprise feature, which means it is not available on
> Growth; one rep said the opposite, that SSO is on all plans. The better-supported answer is
> Enterprise-only, because that version appears in many calls from multiple reps, while the
> all-plans claim appears once and was later hedged.
> ✓ CALL-006 [07:23] Alastair McCrae (AE): "Yeah, so SSO's included on all our plans, that's standard."
> ✓ CALL-006 [14:50] Alastair McCrae (AE): "I'm fairly sure it's all plans. But yeah, I'll confirm."
> ✓ CALL-002 [01:59] Jon Bell (SE): "SAML SSO and SCIM provisioning, both on Enterprise."
> ✓ CALL-012 [08:09] Leo Grant (AE): "SAML SSO is Enterprise."  (+ 8 more)

Baseline, all 20 transcripts in the prompt, verdict **no**:

> Yes—OrbitFlow staff said SSO is included on all plans, which would include Growth. The clearest
> statement is Alastair's in CALL-006, and it's echoed by Jon/Nina in other calls when they say SSO
> is on Enterprise, which does not contradict all-plans availability.

Every statement was in its prompt; it picked the one that answered the question most directly.

### 2. Unstable: q11

> Has anyone from the vendor given inconsistent answers about the product?

There are two: SSO on all plans vs Enterprise-only, and "completely no-code" (CALL-006 [11:30]) vs
"we don't claim every workflow is no-code" (CALL-001 [12:12]). Each side sits in a single turn of a
different call, so similarity search cannot find them; for this question the answer step sees every
vendor claim, grouped by topic.

Second run (`results/20261023-235835-auto-effort-low`), verdict **yes**:

> Yes. There are a couple of clear inconsistencies: on SSO, one rep said it is "included on all our
> plans" while other reps said SAML SSO is on Enterprise; and on coding, one rep said the use case is
> "completely no-code" while another said "We don't claim every workflow is no-code."

Fresh clone, verdict **partly**: SSO, plus a weaker one (Alastair's "all of those are native
connectors" vs other reps' "a mix of native connectors and API-based options"), and no word on
no-code. Both no-code claims were in the context it saw; the answer step stopped at two. The
baseline also found only SSO. This is the variance the per-question comparison is for; a product-fact
table with conflicts recorded at ingestion (README, *With more time*) would make it a lookup.

### 3. The checker catches a real misattribution: q08

> Why did customers who left decide to leave?

Baseline, citation check `wrong_call` ×2:

> ✗ CALL-014 [04:08] Hazel Wren: "it would scale with us."  → said in CALL-015 [04:08]
> ✗ CALL-014 [05:27] Hazel Wren: "We paid for eleven workflows' worth of value and a plan for forty."
>   → said in CALL-015 [05:27]

Hazel Wren is Oakhill's; CALL-014 is Verity's. With all 20 transcripts in the prompt the model mixed
up the two churned accounts, and the checker shows it because the words are not in CALL-014, with a
pointer to where they are. The pipeline routed "customers who left" to the two churn calls, sent them whole, and
attributed every quote correctly (verdict yes vs partly).

## What the eval led to

Each of these came from a question that failed: the vendor-claims table (q11); giving product
questions every vendor statement on the topic and weighing conflicts (q24); checking first names in
code and showing the notes on names under the answer (q06 "Acme Corp", q16 "Priya"); checking the
speaker and the call, not only the words (a run credited Sarah's words to Maya); notes written at
ingestion for cross-call questions (turn-level evidence recall, 0.54 on retrieved excerpts); an
inventory of relevant turns written before the answer (the answer-step failures, tested with
`--replay` so retrieval was held fixed); and low reasoning in the answer step (per-step timings showed
latency follows generated tokens).

## Where the gold set comes from

The questions and facts were drafted by an LLM agent that read all 20 transcripts. Every cited line was
then checked against the source and every "not in the data" was checked with grep. The disputed
interpretations (19 points) were reviewed by a second model (Claude) and a human decided each one; the
decisions are in `review/reviews_2026-10-19.json`. They changed the rubric, not the system: three
apparent conflicts (Verity's "hundred thousand", "you weren't there in February", Greenline's "two and
a half thousand") turned out to be readings of normal speech and became bonus facts or penalties; q11
now requires the two product contradictions and treats commercial concessions as optional; q07 is
graded by tiers, not order; facts were split into core and details.

The choice of what counts as the main point in the undisputed questions has not been reviewed by a
human.
