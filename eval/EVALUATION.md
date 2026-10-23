# Evaluation

The README has the short version. This file has the rubric, the full results, how far the judge can be
trusted, three worked examples, and where the gold set comes from.

## What is measured and why

The question behind the design: when an answer is wrong, which step failed? Each metric isolates one
step, and the cheap deterministic ones come first so the noisy LLM-judged ones are not the only signal.

| metric | what it tells you | how |
|---|---|---|
| context recall | did retrieval/routing put the right calls in front of the model? | gold calls ∩ context calls |
| cited recall | did the answer actually use them? | gold calls ∩ calls with a verified citation |
| citation validity | are the quotes real and correctly attributed? | code check against the transcript |
| correct (yes / partly / no) | is the main point right? | LLM judge against the rubric |
| core / atomic fact recall | how complete is it? | LLM judge, per core and per detail |
| penalties | did it make a statement the gold set rules out? | LLM judge |
| abstention | does it say "not in the data" when, and only when, it should? | LLM judge (`declines`) |
| tokens, latency | what does it cost? | API usage per question |

Reading them together: low context recall means retrieval or routing failed. High context recall with
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
`*-judge-repeat-opus.*` and `*-judge-gpt54.*` the judge-reliability checks.

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
between yes and partly (14/14/1 became 8/20/1). Claude and `gpt-5.4` agree on 22 of 30 for the same
answers. So the yes/partly boundary is noise of about ±6 questions, and the identical 14/14/1 in the
three runs is partly luck. The yes-vs-no line, the abstentions and the deterministic metrics (context
recall, citation validity, tokens) are stable. Taking the majority of three judge passes would cut the
noise; the judge has not yet been calibrated against human grades (see the end of this file).

The default judge is `gpt-5.4`, so that is what a rerun uses. It is stricter on the yes/partly line:
a run from a fresh clone on 23.10 (`results/20261023-113918-auto-fresh-clone.md`) gave 8 / 18 / 3,
with context recall 1.00, citation validity 1.00, abstention 5/5 and ~13K tokens per question, the
same as the Claude-judged runs.

### Reading the numbers

- **Routing and retrieval are not the bottleneck.** Every gold call reaches the model in every run.
  Where cited recall drops (q02 Salesforce, q05 capabilities), the calls were in context but the
  answer stopped after a few examples.
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

- **q11 "Has anyone from the vendor given inconsistent answers?"**: wrong in every pipeline run
  (example 3).
- **q24 "Is SSO on Growth?"**: finds both sides but will not conclude (example 2).
- **q30 (bonus, two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the
  question and the Juniper call to answer it. The planner routes to Verity only, so the pipeline
  declines; the baseline answers it.
- **Long cross-call lists (q02, q05)**: the right calls are in context, but the answer stops early.

## Three worked examples

From run `20261017-155023-auto-regraded`, abridged.

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

### 2. Partly: false balance, q24

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

### 3. Wrong: a cross-call question retrieval cannot see, q11

> Has anyone from the vendor given inconsistent answers about the product?

Pipeline (confidence insufficient), verdict **no**:

> I did not find a direct product contradiction in the retrieved excerpts. The vendor reps mostly
> qualified their answers or deferred exact product details to writing …

There are two: SSO on all plans (CALL-006) vs Enterprise-only (CALL-012 and the engineers), and
"completely no-code" (CALL-006) vs "we don't claim every workflow is no-code" (CALL-001). Each side
sits in a single turn of a different call, and retrieval by similarity to the question finds turns
that sound like "inconsistent answers", not turns that disagree with each other. The citations it did
give are real, so citation validity stays at 1.0 while the answer is wrong, which is why validity
alone is not a quality metric. The fix is structural (per-call vendor-claim notes grouped by topic, see
"With more time" in the README), not a prompt change.

## What changed because of the eval

In order: the judge got partial credit and a separate `correct` verdict; the planner stopped narrowing
product questions to "prospect" calls (that cut out the renewal call holding the SSO answer); calls not
named in the question each get one excerpt even for narrow questions; figures that differ across
statements must go into `conflicts`; header metadata became citable; abstention scoring moved from a
heuristic to the judge; and after an audit of the results the checker started verifying the speaker and
the call, because one run credited Sarah's words to Maya.

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
human, and that review is not a calibration of the judge. The planned calibration: 10 answers,
stratified by verdict and question type, graded blind by a human, reporting the raw agreement rate and
explaining every disagreement.
