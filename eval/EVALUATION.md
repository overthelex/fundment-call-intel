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

`gpt-5.4-mini` answering. The pipeline was run three times with identical code and the full-context
baseline once. All four sets of answers were then re-checked and re-judged against the reviewed gold
set without regenerating them (`--regrade`). Files in `results/`: `*-auto.*` / `*-full.*` are the
original runs, `*-regraded.*` the numbers below, `comparison.md` the per-question comparison,
`*-judge-repeat-opus.*` and `*-judge-gpt54.*` the judge-reliability checks. `results/README.md` lists every file with its judge.

Over 29 questions (q30 excluded):

| | pipeline (`auto`), 3 runs | whole dataset in prompt (`full`), 1 run |
|---|---|---|
| context recall | 1.00 / 1.00 / 1.00 | 1.00 (by construction) |
| cited recall | 0.91 / 0.91 / 0.89 | 0.90 |
| citation validity | **1.00 / 1.00 / 0.96** | 0.94 |
| failed citations: not found · wrong call · wrong speaker | 1·0·0 / 0·0·0 / 1·2·3 | 3·6·1 |
| answer correct: yes / partly / no | 14/14/1 in each run | 8 / 20 / 1 |
| core fact recall | 0.62 / 0.65 / 0.62 | 0.58 |
| atomic fact recall | 0.51 / 0.51 / 0.48 | 0.48 |
| compound fact recall (old scoring) | 0.42 / 0.46 / 0.44 | 0.42 |
| penalties hit | 0 / 0 / 0 | 0 |
| correct abstention on unanswerable | 5/5 in every run | 5 / 5 |
| false abstention on answerable | 1 / 0 / 1 (of 24) | 0 / 24 |
| prompt tokens / question | **~13K** | 122K |
| latency / question | 13–14 s | 13 s |

### How far the judge can be trusted

Re-judging the *same* answers of one run with the same Claude judge moved 6 of 30 verdicts, all
between yes and partly (14/14/1 became 8/20/1). So the yes/partly boundary is noise of about ±6 questions, and the identical 14/14/1 in the
three runs is partly luck. The yes-vs-no line, the abstentions and the deterministic metrics (context
recall, citation validity, tokens) are stable. Taking the majority of three judge passes would cut the
noise.

A one-off cross-check with `gpt-5.4` as the judge (`results/*-judge-gpt54.*`) agreed with Claude on
22 of 30 and was stricter on the yes/partly line. It is kept as evidence of how much the choice of
judge moves the numbers; the evaluation uses Claude only, from a different vendor than the answering
model. A fourth pipeline run from a fresh clone on 23.10 (`results/20261023-120606-auto-fresh-clone.md`,
Claude judge) gave 12 / 16 / 1, inside that noise band, with context recall 1.00, one wrong-call
citation caught by the checker, abstention 5/5 and ~13K tokens per question.

### Reading the numbers

- **Routing is not the bottleneck; retrieval is, for cross-call questions.** Every gold call reaches
  the model in every run, which is what the first version of this file reported. Turn-level evidence
  recall, added on 23.10 (`results/20261023-214420-auto-diagnostics`), shows the call was often there
  without the turn: 0.96 when whole calls are sent, 0.54 when excerpts are retrieved (q05 0.08, q01
  0.32, q09 0.36, q04 0.41). The "long lists stop early" failures (q02, q05) are mostly retrieval:
  the answer cannot list what it never saw.
- **The pipeline is at least as good as the baseline at ~1/9 of the input tokens.** The gap in "yes"
  (14 vs 8) is within the judge noise and the baseline's own run-to-run noise is not measured, so the
  honest claim is "no worse", not "better". Per question the baseline is ahead on the two hardest
  cross-call questions, q11 and q30, where it sees everything, and behind on q21 (example 1 below).
- **Quotes are more reliable with less context**: 0.96–1.00 citation validity for the pipeline vs 0.94
  for the baseline, whose failures are mostly *wrong call* (6): real quotes attached to the wrong
  customer. Wrong call and not found are reported separately because they are different failures
  (attribution vs invention); both count as errors.
- **The checker catches real errors, not only typos**: an invented quote, vendor words credited to the
  customer, one speaker's words credited to a colleague, the right quote in the wrong call. The CLI
  shows each as ✗, with a pointer to where the words actually are when they exist elsewhere.
- **Unanswerable and near-miss questions work** in all runs: "Which ERP does Kestrel use?" (they
  decline to say), ISO 27001 (only SOC 2 is mentioned), an Enterprise price (always "custom").
- **Completeness depends on how you count**: 0.42–0.46 compound, about 0.5 atomic, about 0.62 core.
  The answers usually get the points and drop supporting detail.

### Where it fails

- **q11 "Has anyone from the vendor given inconsistent answers?"**: wrong in every run of the first
  version; fixed on 23.10 by the vendor-claims context (example 3).
- **q24 "Is SSO on Growth?"**: found both sides but would not conclude; fixed on 23.10 by weighing
  conflicts over every vendor statement on the topic (example 2).
- **q30 (bonus, two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the
  question and the Juniper call to answer it. The planner routes to Verity only, so the pipeline
  declines; the baseline answers it.
- **Long cross-call lists (q01, q05, q09)**: the right calls were in context but most supporting turns
  were not (evidence recall 0.08–0.36); first failed step "retrieval". The map step (each candidate
  call read in full by a cheap pass, `callqa/mapper.py`) raised cross-call evidence recall to 0.89 and
  q01 and q04 to "yes" (`results/20261023-224354-auto-map`). q09 ("how do renewals differ from new
  business?") stays at 0.50: a reader of one call cannot see a pattern that only shows across calls.
  Because the map step pays for a full read on every question, the default became notes written at
  ingestion (`callqa/notes.py`, `callqa/store.py`). On the 7 cross-call questions that use it: 5
  "yes" (map 4, retrieval 3), core recall 0.75 (map 0.84, retrieval 0.66), evidence recall 0.65 (map
  0.89, retrieval 0.48), for ~26K tokens each instead of ~139K (`results/20261023-231007-auto-notes`).
- **Name mismatches (q06 "Acme Corp", q16 "Priya")**: the mapping was made but sat in a note at the
  bottom that the judge never saw, and the planner could not know about people only mentioned in
  passing. Fixed on 23.10: first names are checked against every transcript in code
  (`callqa/names.py`), the notes are printed under the answer and passed to the judge, and the answer
  is told to open with the reading it chose. q06 became "yes"; for "Priya" the model still often does not
  repeat the note, so the note itself, from code, is what the user reads.

## Three worked examples

From run `20261017-155023-auto-regraded`, abridged; examples 2 and 3 also show the answer after the fix.

### 1. Correct, and the baseline gets it wrong: q21

> How much was Verity Payments paying OrbitFlow per year?

Pipeline (confidence medium), verdict **yes**:

> About £80,000 per year; OrbitFlow described Verity as an "eighty-thousand-pound account."
> ✓ CALL-014 [11:40] Ruth Adeyemi (CSM, OrbitFlow): "You were an eighty-thousand-pound account"

Baseline, verdict **no**, citation check `wrong_call` ×3:

> Verity Payments was paying about £21.5k per year …
> ✗ CALL-014 [01:28] Ruth Adeyemi: "So you were paying twenty-one and a half thousand a year for what — two builders?"

That quote is from the Oakhill call (CALL-015 [01:28]), not Verity's. With all 20 transcripts in the prompt the model
mixed up two churned accounts; the checker flags it because the words are not in CALL-014.
The gold set also rewards (bonus) noting that Verity's engineering manager said the platform "costs a hundred thousand a year", and
penalises presenting 100K as the price without a caveat; this answer gets neither.

### 2. Partly: false balance, then fixed, q24

> Is SSO available on OrbitFlow's Growth plan?

Pipeline (confidence low), verdict **partly**:

> The transcripts conflict, so I can't verify a clean yes/no. One OrbitFlow rep said SSO is included
> on all plans, but several other reps said SAML SSO is on Enterprise.
> ✓ CALL-006 [07:23] Alastair McCrae (AE): "Yeah, so SSO's included on all our plans, that's standard."
> ✓ CALL-002 [01:59] Jon Bell (SE): "SAML SSO and SCIM provisioning, both on Enterprise."
> ✓ CALL-004 [02:09] Jon Bell (SE): "SAML SSO and SCIM provisioning — both supported, both on Enterprise."

Judge, per required fact: Alastair's claim *supported*; Leo Grant telling Pinewood that SSO would be
lost on Growth *missing*; engineers saying Enterprise-only *supported*; weighing the evidence to
conclude Enterprise-only *missing*. The answer finds the conflict but treats one hesitant rep (who
said he was "fairly sure" and would confirm) as equal to every engineer. Reporting a conflict is right;
refusing to weigh it is not.

Two things were missing, and a prompt alone would fix only one. The model saw two or three of the
statements, because retrieval returns the passages most similar to the question; in the data, SAML SSO
is called Enterprise in nine calls by three reps. And it had no rule for weighing.

**The fix.** The planner names the product topics of a question (one to three of the 12 claim topics),
and the answer step also gets every vendor statement on them from the claims table. Each conflict now
carries `better_supported` and `why`, decided on fixed criteria (how many people, how specific, later
hedged or corrected, who said it, recency) or "cannot tell"; both sides are still cited and confidence
stays at most medium. Run `results/20261023-204145-auto-weighing`, verdict **yes**:

> Best-supported answer: no, OrbitFlow's SSO is described as an Enterprise-only feature, not a
> Growth-plan feature, although one AE once said it was on all plans.
> ✓ CALL-006 [07:23] Alastair McCrae (AE): "SSO's included on all our plans, that's standard."
> ✓ CALL-002 [01:59] Jon Bell (SE), CALL-004 [02:09] Jon Bell, CALL-008 [10:56] Nina Patel (SE),
> CALL-012 [08:09] Leo Grant (AE): SAML SSO on Enterprise
> → better supported: Enterprise-only. Five statements across multiple calls and two different reps;
> only one AE said all plans, and he later hedged: "I'm fairly sure it's all plans. But yeah, I'll confirm."

The first full run with this change routed a broad question (q05, "what capabilities matter to
prospects?") to all 12 topics, and the vendor statements crowded out the prospects' words. Only
"specific" questions with at most three topics now get the table (`MAX_PRODUCT_TOPICS`); "which
customers asked about SSO?" is about customers. The same run showed a
judge glitch: it returned a verdict for one of q24's four facts, and missing verdicts counted as "not
stated"; the evaluator now asks again when verdicts are missing.

### 3. Wrong, then fixed: a cross-call question retrieval cannot see, q11

> Has anyone from the vendor given inconsistent answers about the product?

Pipeline (confidence insufficient), verdict **no**:

> I did not find a direct product contradiction in the retrieved excerpts. The vendor reps mostly
> qualified their answers or deferred exact product details to writing …

There are two: SSO on all plans (CALL-006) vs Enterprise-only (CALL-012 and the engineers), and
"completely no-code" (CALL-006) vs "we don't claim every workflow is no-code" (CALL-001). Each side
sits in a single turn of a different call, and retrieval by similarity to the question finds turns
that sound like "inconsistent answers", not turns that disagree with each other. The citations it did
give are real, so citation validity stays at 1.0 while the answer is wrong, which is why validity
alone is not a quality metric. The fix had to be structural, not a prompt change.

**The fix.** At index time one extraction pass per call lists every product statement by OrbitFlow
staff under 12 fixed topics, each with a verbatim quote that must pass the citation checker
(`callqa/claims.py`, 587 claims). The planner flags questions about the vendor's consistency, and
for those the answer step sees all claims grouped by topic. The same question now gets (run
`results/20261023-122047-auto-vendor-claims`, verdict **yes**):

> Yes. I found two clear inconsistencies in OrbitFlow staff answers: one about whether SSO is on all
> plans or only Enterprise, and one about whether the product is completely no-code.
> ✓ CALL-006 [07:23] Alastair McCrae (AE): "SSO's included on all our plans, that's standard."
> ✓ CALL-002 [01:59] Jon Bell (SE): "SAML SSO and SCIM provisioning, both on Enterprise."
> ✓ CALL-006 [11:30] Alastair McCrae (AE): "That's fine, it's completely no-code."
> ✓ CALL-002 [19:37] Jon Bell (SE): "We don't claim every workflow is no-code."

It found both contradictions in 4 of 4 manual runs. The first version of the extraction prompt missed
short replies like "it's completely no-code"; telling it that short answers to a customer's question
count, and that a hedge about SSO is an SSO claim, fixed that (448 → 587 claims).

## What changed because of the eval

In order: the judge got partial credit and a separate `correct` verdict; the planner stopped narrowing
product questions to "prospect" calls (that cut out the renewal call holding the SSO answer); calls not
named in the question each get one excerpt even for narrow questions; figures that differ across
statements must go into `conflicts`; header metadata became citable; abstention scoring moved from a
heuristic to the judge; and after an audit of the results the checker started verifying the speaker and
the call, because one run credited Sarah's words to Maya; q11 led to the vendor-claims table, and q24
to giving product questions every vendor statement on the topic and weighing conflicts; q06 and q16 to
checking first names in code and showing the notes on names under the answer; turn-level evidence
recall to the map step for cross-call questions, and the 7 answer-step failures to an inventory of
relevant turns written before the answer (tested with `--replay`, so retrieval was held fixed).

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
