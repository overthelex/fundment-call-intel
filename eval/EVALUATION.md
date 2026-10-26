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
26.10. Both pipeline runs used the index committed to the repo (`.cache/`). Files: `results/README.md`.

| | pipeline, run 1 | pipeline, run 2 | whole dataset in prompt (`full`) |
|---|---|---|---|
| context recall | 1.00 | 1.00 | 1.00 (by construction) |
| evidence recall | 0.90 | 0.90 | 1.00 (by construction) |
| cited recall | 0.98 | 0.97 | 0.93 |
| citation validity | **1.00** | **0.99** | 0.97 |
| failed citations: not found · wrong call · wrong speaker | 0 · 4 · 1 | 0 · 5 · 0 | 4 · 10 · 3 |
| answer correct: yes / partly / no | **18 / 11 / 0** | **17 / 11 / 1** | 13 / 14 / 2 |
| core fact recall | 0.80 | 0.80 | 0.73 |
| atomic fact recall | 0.70 | 0.67 | 0.61 |
| compound fact recall (strictest) | 0.61 | 0.65 | 0.55 |
| core facts contradicted · penalties hit | 0 · 0 | 0 · 3 | 1 · 3 |
| correct abstention on unanswerable | 4 / 5 | 2 / 5 | 5 / 5 |
| false abstention on answerable | 0 / 24 | 0 / 24 | 0 / 24 |
| prompt tokens / question (from the prompt cache) | 40K (31%) | **38K** (24%) | 123K |
| latency mean / p95, 4 in parallel | 12.7 / 31.5 s | 12.2 / 29.4 s | 11.3 / 38.5 s |

`results/comparison.md` has the verdicts per question. The two pipeline runs disagree on 6 of 30;
runs of nearly the same code have given 15 to 20 "yes". The baseline is worse than both runs on q03,
q05, q07 and q16 and better on q30. The abstention misses (q29 in run 1; q26, q27, q29 in run 2) are
judged "yes" and do say the data has no answer: the judge's abstention flag and its verdict disagree.
The code before the buying rubric and the counted items scored 19 / 10 / 0 twice (24.10,
`…-211125/211257-auto-final`); what moved and why is in the README, *Results*.

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
  sent and lower for questions across calls, which use the notes written at ingestion (about three
  quarters on the 7 such questions). The answer cannot list what it never saw.
- **The pipeline is at least as good as the baseline at about 1/3 of the input tokens.** The gap in
  "yes" (17–18 vs 13) is about the size of the judge noise, so the claim is "no worse"; q24 and q11 are clear
  per-question differences (examples 1 and 2).
- **Quotes are more reliable with less context**: 5 failed citations for the pipeline vs 17 for
  the baseline, mostly *wrong call*: real quotes attached to the wrong customer (example 3). Wrong
  call and not found are reported separately because they are different failures (attribution vs
  invention); both count as errors.
- **Unanswerable and near-miss questions work**: "Which ERP does Kestrel use?" (they decline to
  say), ISO 27001 (only SOC 2 is mentioned), an Enterprise price (always "custom"). The miss
  in run 2 (q29) does say Enterprise is "custom priced" but was judged as not declining.
- **Completeness depends on how you count**: about 0.6 compound, 0.7 atomic, 0.8 core. The answers
  usually get the points and drop supporting detail.

### Where it fails, question by question

- **Single-call details (q13, q14, q15, q18)**: the whole transcript is in context; the answer gives
  the main point and leaves out a required detail (first failed step "answer").
- **q05 ("which capabilities matter most to prospects?")**: "partly" in most runs until its items
  were counted. It is a count over calls, and notes ranked by similarity to an abstract question miss
  concrete asks: "Can the queue be owned by a team?" is raised in 5 of 10 calls but ranked
  389th–479th of 509 noted turns, below the budget. Now the notes of each field are grouped into
  items once, after ingestion (`themes.py`), the calls behind each item are counted in code, and the
  turns of the 25 items raised in most calls are added to the context: "yes" in 7 of 8 runs, the
  misses now being one of six themes left out (SIEM export, reusable components or the
  change-management scenario, a different one each run). See *Engineering notes*.
- **q07 ("which prospects seem most likely to purchase?")**: "yes" in about half the runs while the
  model chose the tiers (the gold set puts Juniper on top; the model's verdict was "viable, not a sure
  buyer" in some runs). Now each call is read for fixed signals and code computes the tier
  (`mapper.tier_of`) and writes the ranking paragraph: 5 of 6 "yes" run alone (`results/…-q07-rubric`)
  and 2 of 4 in full evals (the answer's prose contradicted the ranking once; a signal was misread
  once), 117–179K
  prompt tokens and 23–44 s. Three designs did not hold up on the way: caps on any blocker the model
  found (every prospect has one, so all ten came out conditional); caps on blockers the model marked as
  "stopping" the purchase (it marked the evaluation's own open questions in some runs and not in
  others); and a broad "the decision waits on something else" (it counted the prospect's own
  evaluation). What caps the tier now is narrow: the prospect must first find out whether the problem
  is there at all, or the decision is whether to expand a vendor they already use. The rubric was
  tuned on q07 alone.
- **q09 ("how do renewals differ from new business?")**: evidence recall 0.93 since the planner takes
  every note field an answer can sit in and comparisons send the small kinds of call whole (3
  renewals, 5 cold calls); "yes" in some runs, and when "partly" the answer stays general (the 7%
  uplift, the jointly written pilot criteria). Per-call verdicts made comparisons worse (core recall
  0.0 and 0.27, `results/…-assess-incl-comparisons`), so comparisons do not get them.
- **q21 ("how much was Verity paying?")** once took Sarah's rhetorical "costs a hundred thousand a
  year" over the £80K account value, the trap in `GOLD_NOTES.md`.
- **q30 (bonus, two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the
  question and the Juniper call to answer it. The planner routes to Verity only, so the pipeline
  declines; the baseline, which sees every call, answers it.

Fixed, and how (details in *Engineering notes*): q10 and q02 (a verdict per call, and a coverage
check), q11 (each claim topic checked twice), q24 (every vendor statement on the topic, weighed),
q06 and q16 (names checked in code).

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
medium (at 31–47 s). One pass comparing ~550 statements under 12 topics stops after the clearest
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

Later, on another index, a run of the 11 example questions missed no-code again: one check of that
topic found it 7 times in 10. Each topic is now checked twice and the pairs merged; q11 "yes" in 6
of 6 runs since (`results/…-q11-two-passes`). The question takes 15–37 s instead of ~8 s.

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

## Engineering notes

What was measured, changed or dropped along the way, with the runs in `results/` (index:
`results/README.md`).

### Small parallel checks instead of one pass

- **q10**: with five whole cold calls in context, the answer said all five produced a follow-up in 3 of
  5 replays, although Trafford's Yvonne said "I won't read it". Each call is now read on its own for
  the question and gives a verdict with verified quotes (`callqa/mapper.py`), for a few whole calls
  always and for questions that rank or classify calls (q02, q07, q28) when the planner says so, at
  most 25 calls. q10 "yes" in 4 of 4 runs after (`…-per-call-check`).
- **Coverage check**: once, with all five verdicts in context, the answer to q10 wrote "three of the
  four cold calls" and dropped Kestrel. Each verdict now says whether the call counts toward the answer;
  code checks that the answer cites or names every call that does, and runs the answer step once more,
  told which calls it left out, if not. Replaying that answer: flagged and re-answered with all four
  follow-ups; in 8 live answers to q02, q07, q10 and q28 it did not need to fire (`…-coverage-check`).
- **q11**: one pass over ~550 vendor statements found the "completely no-code" contradiction in 3 of 5
  replays; one small call per claim topic, in parallel, fixed that, but one check of the "no-code"
  topic still found it only 7 times in 10. Each topic is now checked twice and the pairs merged: q11
  "yes" in 6 of 6 runs, each with the no-code contradiction (`…-q11-two-passes`), 15–37 s instead of
  14–17 s.

### q05: what was tried

| change | evidence recall on q05 | kept? |
|---|---|---|
| notes prompt records customer questions about capabilities as needs | 0.42 → ~0.5 | yes |
| a bonus for points that recur across calls | no better on average (0.72–0.76 vs 0.76 over the 7 cross-call questions) | no |
| rank notes by the question and the planner's search queries, budget 350 turns | 0.43 → 0.72 on saved plans, 0.33–0.50 live: the planner's queries change between runs; q07 fell to "no" twice (`…-query-rank`) | no |
| `--across map`: read each call for the question, group the points into items, count calls in code | 1.0; core recall 0.50–0.83, "yes" in 1 of 3, at ~45 s and ~150K tokens (`…-q05-map-tally`) | as an option |
| items counted once from the stored notes (one call per field after ingestion), their turns put first within the 250-turn budget | 0.67–0.75, "yes" 3 of 3, but q01 fell to "partly" in both full runs: the items took half the budget from what q01 needed | no |
| the same, their turns added on top of the budget | 0.67–0.79, core recall 0.50–1.0, "yes" in 7 of 8, 34–46K tokens; q01 "yes" in 5 of 5 (`…-q05-themes`, `…-q01-q05-themes`, `…-213702/213723-auto-final`) | **yes** |

The counting step still groups too coarsely ("security, compliance and access controls" instead of
"export audit logs to our own SIEM"), which is what q05 loses on when it is "partly".

### Ingestion: reading calls in parts

One request over a whole ~5K-word call generated up to 40K tokens and took 1.5–3 min, and ingestion
waits for its slowest request. Calls are now read in parts of ~1,700 words, overlapping by two turns,
all at once. Measured on the longest call (CALL-004, 4,904 words, 3 parts), 2 repeats, variants
interleaved (`eval/bench_ingest.py`):

| read | reasoning: claims / notes | requests | time for the call | output tokens | claims | notes |
|---|---|---|---|---|---|---|
| whole call | medium / medium | 3 | 98–116 s | 41K | 38–41 | 60–93 |
| parts | low / low | 9 | 21–24 s | 21K | 46–47 | 105–117 |
| **parts (used)** | **low / medium** | 9 | 63–79 s | 48K | 52–54 | 111–121 |

All-low is the fastest, but its notes, though more numerous, rank worse against questions: the 7
cross-call questions got 0.74 of their evidence turns from an all-low index, 0.79 with notes at
medium, 0.77 from the whole-call index (same saved plans). Claims lose nothing at low (14–15 of the 15
vendor statements behind the gold contradictions in every index). The eval on the parts index was
within noise of the whole-call one (`…-parts`). The note budget counts turns, not notes, since a
turn noted under three fields used to take three places.

### Ingestion: the hangs

Fresh ingestions took 92 s to 13 min. A request log and thread dumps (`faulthandler`) over repeated
ingestions showed two causes:

- **TLS handshakes one at a time.** The HTTP client's default SSL context (`truststore` 0.10) holds
  one lock for a whole handshake, network round trips included, so the ~180 connections opened at once
  shook hands in turn: connections queued for ~10 s were closed by the server (30–70 `SSLEOFError` per
  ingestion), and one stalled handshake held every other thread (100+ threads waiting on the lock,
  sockets in CLOSE_WAIT, 0% CPU). Bursts of separate clients, each with its own context, never failed,
  which pointed at the shared lock. A plain `ssl` context with `certifi`: 0 handshake failures since.
- **Requests the provider never answers**: ~4% of them, also reproduced with separate clients and
  tiny prompts (4 of 120 sent at once); no response until the read timeout, and an embedding response
  whose body never arrived. Extractions get a duplicate after 60 s (p90 42 s, p99 86 s) and the first
  answer wins; embeddings, normally under 2 s, time out after 20 s. At question time the same applies
  after 45 s for the planner and the answer, 20 s for verdicts and topic checks.

Four fresh ingestions with both fixes: 80–129 s (24.10). Two more on a fresh clone the next day,
with the same code: 188 s and 260 s.

### Cost and the prompt cache

Prompts put static text first and the question last, so the provider's prefix cache serves the
shared part: per-call readers used to put the question first, so a transcript read for several
questions was never cached. 40% of prompt tokens in a full eval now come from the cache
(`…-prompt-cache`). At list prices a typical question costs ~$0.03 and one with 10–20 per-call checks
$0.11–0.14.

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
