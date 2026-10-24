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

The current code, 29 headline questions (q30 excluded), `gpt-5.4-mini` answering, Claude Opus judging,
24.10. Both pipeline runs used the index committed to the repo (`.cache/`). Files: `results/README.md`.

| | pipeline, run 1 | pipeline, run 2 | whole dataset in prompt (`full`) |
|---|---|---|---|
| context recall | 1.00 | 1.00 | 1.00 (by construction) |
| evidence recall | 0.90 | 0.91 | 1.00 (by construction) |
| cited recall | 0.97 | 1.00 | 0.93 |
| citation validity | **0.99** | **0.99** | 0.97 |
| failed citations: not found · wrong call · wrong speaker | 1 · 2 · 1 | 1 · 2 · 0 | 4 · 10 · 3 |
| answer correct: yes / partly / no | **20 / 9 / 0** | **15 / 13 / 1** | 13 / 14 / 2 |
| core fact recall | 0.82 | 0.75 | 0.73 |
| atomic fact recall | 0.70 | 0.68 | 0.61 |
| compound fact recall (strictest) | 0.62 | 0.61 | 0.55 |
| core facts contradicted · penalties hit | 0 · 0 | 1 · 2 | 1 · 3 |
| correct abstention on unanswerable | 5 / 5 | 4 / 5 | 5 / 5 |
| false abstention on answerable | 0 / 24 | 0 / 24 | 0 / 24 |
| prompt tokens / question | **32K** | 33K | 123K |
| latency mean / p95, 4 in parallel | 10.5 / 21.3 s | 11.2 / 21.6 s | 11.3 / 38.5 s |

`results/comparison.md` has the verdicts per question. The two pipeline runs disagree on 8 of 30, all
on the yes/partly line but one: 20 against 15 "yes" from the same code and index. The baseline
differs from both on 4: worse on q03, q11 and q24, better on q30.

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
- **The pipeline is at least as good as the baseline at about 1/4 of the input tokens.** The gap in
  "yes" (17–19 vs 13) is within the judge noise, so the claim is "no worse"; q24 and q11 are clear
  per-question differences (examples 1 and 2).
- **Quotes are more reliable with less context**: 5–6 failed citations for the pipeline vs 17 for
  the baseline, mostly *wrong call*: real quotes attached to the wrong customer (example 3). Wrong
  call and not found are reported separately because they are different failures (attribution vs
  invention); both count as errors.
- **Unanswerable and near-miss questions work**: "Which ERP does Kestrel use?" (they decline to
  say), ISO 27001 (only SOC 2 is mentioned), an Enterprise price (always "custom"). The miss
  in run 2 (q29) does say Enterprise is "custom priced" but was judged as not declining.
- **Completeness depends on how you count**: about 0.6 compound, 0.7 atomic, 0.8 core. The answers
  usually get the points and drop supporting detail.

### Where it fails

- **Single-call details (q13, q14, q15, q18)**: whole transcript in context, the answer gives the main
  point and leaves out a required detail; first failed step "answer".
- **q09 ("how do renewals differ from new business?")**: evidence recall was about a third. The
  planner chose one note field ("how the team ran the call") while the uplift and the pricing sit
  under pricing and decision process, and the renewal calls were seen only as notes. Now the planner
  takes every field an answer can sit in, and a comparison sends the small kinds of call whole (3
  renewals and 5 cold calls, ~11.5K words; prospects stay as notes): evidence recall 0.93, core
  recall 0.2 → 0.4–0.6. Still "partly": the answer stays general and leaves out the 7% uplift and the
  jointly written pilot criteria. Per-call verdicts made it worse (core 0.0 and 0.27,
  `results/…-assess-incl-comparisons`), so comparisons do not get them.
- **q05 ("which capabilities matter most to prospects?")**: 7 of the 14 missed evidence turns had no
  note at all: customer questions such as "Can we export audit logs to our own SIEM?" or "Version
  history?" were not recorded as needs. The notes prompt now records a question about a capability as
  a need (10 of the 14 are noted now) and the planner takes integrations and objections too: evidence
  recall 0.42 → 0.56, but still "partly" in the saved runs (core recall 0.5–0.67): the answer now
  misses team-owned exception queues or the change-management test instead.
- **q10 ("which cold calls produced a follow-up?")**: five whole calls in context, and the answer
  sometimes said all five did, although Trafford's Yvonne said "I won't read it" (3 of 5 replays of
  the same context with low reasoning; 0 of 3 with medium). Fixed after the fresh-clone run: for a
  question across a few whole calls, each call is first read on its own for the question and gives a
  verdict with verified quotes (`callqa/mapper.py`, in parallel), and the answer is built call by call
  from them. q10 "yes" in 4 of 4 runs and in both current runs; q08, q19 and q20, which take the same path, judged as before
  (`results/…-per-call-check`).
- **q11 (vendor contradictions)** was "partly" before the per-topic check; "yes" in both current runs
  (example 2).
- **Judgement: q07 ("which prospects seem most likely to purchase?")** left Acme out, dropped the
  caveats on the top prospects or put BrightPath on top without its BAA gate ("partly" or "no" in
  every run). Fixed in part: the planner marks questions that rank or classify calls, each candidate
  call (at most 25) gets its own verdict before the answer, and the answer must place every call in
  a tier with its condition or blocker. q07 "yes" in about half the runs since (5 of 9); q02 ("which customers
  mentioned Salesforce?"), which once listed BrightPath and Greenline, "yes" in all 5; q28 too
  (`results/…-assess-each-call`, `…-before-notes-v2`, `…-final`). It costs 100–150K prompt tokens on those questions
  (32K mean per question, was 21K). Comparisons between groups (q09) got worse with it, core recall
  0.27, and are left out (`results/…-assess-incl-comparisons`).
- **q21 ("how much was Verity paying?")** once took Sarah's rhetorical "costs a hundred thousand a
  year" over the £80K account value, the trap in `GOLD_NOTES.md`; "yes" in the other run.
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

### 2. Found in one run, missed in the next, then fixed: q11

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
no-code. The baseline also found only SSO.

Both no-code claims were in the context it saw, so this was the answer step. Re-running only the
answer step on that saved context 5 times found no-code 3 times with low reasoning and 5 times with
medium (at 31–47 s). One pass comparing ~600 statements under 12 topics stops after the clearest
contradictions. Checking one topic per call did not fix it by itself: the first version of that
prompt excluded "statements about different customers or conditions", and "completely no-code" was
said about one customer's use case. With that clause replaced by "a blanket claim made to one
customer contradicts a general statement made to another", the 12 parallel topic checks found
no-code in 5 of 5 runs, in ~5 s (`callqa/conflicts.py`). The answer step now gets their findings
first and must weigh each one. Three judged runs (`results/…-q11-topic-check`), verdict **yes** each:

> Yes. The clearest inconsistency is about identity/security: one OrbitFlow rep said "SSO's included
> on all our plans," while several others said "SAML SSO and SCIM on Enterprise." There is also a
> connector claim conflict [...]. A third conflict is around no-code: one rep said a workflow is
> "completely no-code," while others said "We don't claim every workflow is no-code" [...].

The question takes ~16–23 s instead of ~8 s.

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

Each of these came from a question that failed: the vendor-claims table and the per-topic
contradiction check (q11); a verdict per call for questions across a few whole calls (q10) and for
questions that rank or classify calls (q07, q02); giving product
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
