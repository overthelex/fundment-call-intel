# Sales Call QA

Ask questions across the 20 OrbitFlow sales-call transcripts and get an answer you can check.
Every claim comes with a verbatim quote, the call, timestamp, speaker, and a `file:line` link.
Each quote is then matched against the transcript in code, not taken on trust.

```
$ uv run callqa ask "What did Acme Corp say about their current workflow?"

Answer  (confidence: high)
Taking "Acme Corp" to mean Acme Logistics, they said their current workflow is spread across systems:
sales, onboarding and customer success handoffs are managed through spreadsheets and Slack reminders ...

Notes on names
  - "Acme Corp" appears to refer to Acme Logistics in CALL-001.

Evidence
  1. Their current workflow is spread across systems, and handoffs are managed through spreadsheets ...
    ✓ CALL-001 [01:51] Rachel Morgan (VP Revenue Operations, Acme Logistics): "All of that is managed through spreadsheets and Slack reminders."
       data/calls/call-001_acme_logistics.txt:31
  ...

[full: 1 calls, 4,999 words in context · 2 API calls · 9,266 in / 1,156 out tokens · 7.3s]
```

## Setup and run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env        # then set LLM_API_KEY (an OpenAI key works as is)
uv run callqa index         # once: ingests the calls (embeddings, vendor claims, per-call notes; ~5 min,
                            # stored in .cache/callqa.db; re-running reads only new or changed calls)
uv run callqa ask "Which competitors were mentioned, and in what context?"
uv run callqa ask "..." --mode full     # baseline: whole dataset in the prompt
uv run callqa ask "..." --json          # raw result, including the plan and every citation check
uv run callqa                           # interactive prompt
uv run pytest                           # offline unit tests (parser, chunking, citation checker)
```

The client speaks the OpenAI API. With a plain OpenAI key, set only `LLM_API_KEY`. For Azure AI Foundry
(what I ran on), also set `LLM_BASE_URL=https://<resource>.openai.azure.com/openai/v1/`; model names
are then deployment names. Defaults: `CHAT_MODEL=gpt-5.4-mini`, `EMBED_MODEL=text-embedding-3-small`.

## Approach

```
question
  │
  ├─ 1. plan (LLM, structured)      which calls? (named companies, call kinds) · specific vs across · search queries
  │                                 · name mismatches ("Acme Corp" → Acme Logistics, flagged)
  │                                 · ambiguous first names, checked in code ("Priya": who speaks, who is only mentioned)
  │                                 · does it ask whether the vendor contradicts itself?
  │                                 · is it about a product fact? which of 12 topics?
  │                                 · across calls? which note fields hold the answer?
  ├─ 2. context                     vendor-consistency question? → every vendor claim, grouped by topic
  │                                 candidate calls fit in 12K words? → send whole transcripts
  │                                 question across calls? → the turns behind the notes written at ingestion
  │                                   in those fields (+ retrieved excerpts), and the calls with none
  │                                 otherwise → hybrid retrieval (BM25 + embeddings, RRF) with a per-call quota
  │                                 product fact? → plus every vendor statement on that topic, from all calls
  ├─ 3. answer (LLM, structured)    first an inventory of every relevant turn, then the answer from it:
  │                                 summary · claims[] each with verbatim quotes · conflicts[] · not_found[]
  │                                 · each conflict weighed: better-supported side + why, or "cannot tell"
  │                                 · confidence (high / medium / low / insufficient) + reason
  └─ 4. verify (code)               each quote looked up in the parsed transcript → exact / shifted / fuzzy
                                    / wrong speaker / wrong call / not found
                                    unverifiable claims flagged; if none verify, confidence is lowered
```

- **Parsing** (`callqa/parse.py`): header + `[MM:SS] Speaker: text` turns; each turn keeps its file
  line number and its side (vendor / customer, taken from the participant list). The call kind
  (prospect / renewal / churn / cold call) is derived from `STAGE`, because the manifest's `call_type`
  only separates prospects from existing customers.
- **Chunks** (`callqa/index.py`): windows of consecutive turns (~180 words, 2-turn overlap) within one
  call, each with a header naming the call, company, and kind. People talk in fragments, so a window keeps a
  question with its answer.
- **Retrieval**: BM25 catches exact names (Salesforce, Workato, SOC 2); embeddings catch paraphrase
  ("we're nervous about the price" ≈ pricing concern). The two are merged with reciprocal-rank fusion
  over the original question plus the planner's rewrites. For questions about the whole dataset, every
  candidate call also gets its best 2 chunks. Without that quota, long calls crowd short ones out of the
  top-k.
- **Ingestion** (`callqa/store.py`): each call is read once when it is ingested, and the results go
  into one SQLite file. The handler is idempotent by call id and a digest of content, model and prompt
  versions, so an unchanged call costs nothing and a changed one is replaced in one transaction. Two
  passes per call, every quote checked by the citation checker:
  - **vendor claims** (`callqa/claims.py`): what OrbitFlow staff assert about the product under 12
    topics, kept only if said by vendor staff (628 claims). Used whole for consistency questions, by
    topic for product-fact questions ("Is SSO on Growth?");
  - **notes** (`callqa/notes.py`): the call's points under 10 fields (needs, pains, objections,
    competitors, integrations, pricing, decision process, buying signals, outcome, how the team ran
    the call), each tied to a turn and embedded (1,083 notes). Questions across calls select notes by
    field and similarity instead of reading the calls.
- **Answering** (`callqa/prompts.py`): the model sees whose side each speaker is on. It is told that a
  vendor's product statement is a claim, not a fact. It is told to report contradictions instead of
  picking one side silently, and then to weigh them on fixed criteria: how many people say each side,
  how specific each is, whether its speaker later hedged or corrected it, who said it, and recency. When it only saw excerpts, it must say "not found in the retrieved excerpts", not
  "never said".

## Key decisions

1. **Whole calls when they fit, retrieval when they don't.** One call is at most ~5K words, and all 20
   are ~51K words. If the question names a company or a call kind (cold calls are ~4K words in total;
   renewals ~7.5K), chunking only loses context. So those questions get whole transcripts. Retrieval is
   used when the candidate set is large (all prospects, the whole dataset). The 12K-word budget is one
   constant (`FULL_TEXT_WORD_BUDGET`).
2. **Structured output and a verifier in code, not "please cite your sources".** Citations are data
   (call, timestamp, speaker, quote), so they can be checked. The checker allows small timestamp
   slips (`shifted`) and punctuation and casing differences, but rejects invented quotes, words said
   by someone else (`wrong_speaker`) and quotes from another call (`wrong_call`, with a pointer to the
   real one). That gives an objective grounding metric for the eval and a live warning for the user.
3. **The planner sees a catalogue, not the data.** 20 lines of call metadata are enough to resolve
   "Acme Corp", "customers who left" (= churn) or "renewals vs new business" to the right calls. A
   question about something absent from the catalogue (an unknown company) is flagged up front.
   The catalogue lists only participants, so first names are also checked in code against every
   transcript (`callqa/names.py`): "Priya" is Priya Shah, the only Priya who speaks on a call, but a
   Priya Menon (Beacon) and a Priya at Juniper are mentioned. Both kinds of note are printed right
   under the answer, and the answer is told to open with the reading it chose.
4. **Confidence is part of the answer contract.** `insufficient` is an expected output, not a failure.
   The verifier can lower confidence but never raise it.
5. **The baseline is in the code (`--mode full`).** At this dataset size, the whole corpus fits in one
   prompt. The eval compares the pipeline with that brute-force option, so retrieval has to earn its
   place in quality, cost and latency. It is not assumed to help.
6. **Contradictions get their own context, not better retrieval.** "Has the vendor given inconsistent
   answers?" is about a relationship between two turns in different calls, and neither turn looks like
   the question, so similarity search cannot find it (the first version failed it in every run). Putting
   every vendor statement on a topic side by side makes a contradiction visible: "SSO is on all plans"
   (one AE) next to statements in nine other calls that SAML SSO is Enterprise. The planner switches to this
   context only for questions about the vendor's consistency.
   The same table answers product-fact questions: retrieval gives the passages most similar to the
   question, so a fact stated in nine calls and contradicted in one can reach the model as one statement
   against one, and it cannot weigh what it does not see. For a question on one to three product topics
   the answer step also gets every vendor statement on them. A conflict is then reported with both
   sides cited *and* with the better-supported side and the reason, or "cannot tell"; confidence stays
   at most medium.
7. **Read calls when they arrive, not when a question is asked.** Questions across calls need turns
   from every call, and retrieval reached about half of them. Reading every candidate call per
   question (a map step, still available as `--across map`) fixed that but cost ~139K tokens per such
   question at 20 calls and grows with every call. Notes written at ingestion keep most of the gain
   for ~26K tokens, and the cost per question does not grow with the corpus.
8. **One OpenAI-compatible client.** It runs on OpenAI or Azure by changing env vars; no framework.

## Assumptions

- Transcripts are the source of truth; the manifest/header is metadata and can be wrong. Speaker
  attribution is correct (stated in the dataset README), so the speaker's side comes from the participant list.
- Users are sales managers. They want a short answer plus the quotes to check it, more than a long essay.
- English only, a few dozen calls, questions one at a time (no chat history).

## Evaluation

Details, the full results table and three worked examples: [`eval/EVALUATION.md`](eval/EVALUATION.md).

### Run it

```bash
uv run python eval/run_eval.py                    # pipeline, all 30 questions
uv run python eval/run_eval.py --mode full        # baseline: whole dataset in the prompt
uv run python eval/run_eval.py --only q11,q24     # a subset
uv run python eval/run_eval.py --regrade eval/results/<run>.json   # re-check and re-judge saved answers, no generation
uv run python eval/run_eval.py --no-judge         # deterministic metrics only, no Claude Code needed
uv run python eval/run_eval.py --replay eval/results/<run>.json --only q05   # new answer on the saved context
uv run python eval/compare.py --auto A1.json A2.json A3.json --full F.json   # per-question comparison
```

Each run writes `eval/results/<timestamp>-<mode>.json` (every answer, plan, the exact context the
answer step saw, citation checks and verdicts) and a `.md` summary that names the judge and labels
each failed question with the step that failed.

The judge is Claude Opus, a different vendor from the answering model, so it does not grade its own
blind spots. It runs through a local, logged-in [Claude Code](https://claude.com/claude-code)
(`claude -p`, tools disabled, structured output), so it needs `claude` on the PATH and no extra key.
Without it, `run_eval.py` stops before generating any answers; `--no-judge` still runs everything and
reports the metrics computed by code (context and cited recall, citation validity, tokens, latency),
marking the judged ones "not judged". The pipeline itself (`callqa ask`) needs only the OpenAI key.

### What it measures and why

30 annotated questions (`eval/questions.yaml`) covering the cases the task warns about: single-call
lookups, cross-call themes, call-kind filters, name mismatches, ambiguous, unanswerable and near-miss
questions, and vendor contradictions. Each has its gold calls, required facts (core + details), bonus
facts, penalties, and whether the system should abstain.

The metrics are chosen to say *which step* failed, deterministic ones first:

- **context recall**: did routing put the gold calls in front of the model? (code)
- **evidence recall**: did retrieval put the gold *turns* in front of the model? (code, from the
  timestamps in the gold evidence). Call-level recall alone is misleading: every candidate call gets
  at least one excerpt, so the call is "in context" even when the turn that answers is not.
- **citation validity**: is each quote really in that call, said by that speaker? (code)
- **correct** yes / partly / no, **fact recall**, **penalties**: is the answer right and complete? (LLM judge)
- **abstention**: does it say "not in the data" exactly when it should? (LLM judge)
- **tokens and latency**, against a baseline that puts all 20 transcripts in the prompt
- **first failed step** per question (code, from the above): retrieval, answer, attribution or abstention

### Results

29 headline questions, `gpt-5.4-mini` answering, pipeline run 3 times, baseline once. These runs
(17.10) predate the vendor-claims context, conflict weighing and name checks; the runs of the
current code are the paragraphs after the table.
Which file in `eval/results/` is which: [`eval/results/README.md`](eval/results/README.md).

| | pipeline (`auto`) | whole dataset in prompt (`full`) |
|---|---|---|
| context recall | 1.00 in every run | 1.00 (by construction) |
| citation validity | 1.00 / 1.00 / 0.96 | 0.94 (6 quotes attached to the wrong call) |
| correct: yes / partly / no | 14 / 14 / 1 in every run | 8 / 20 / 1 |
| core fact recall | 0.62–0.65 | 0.58 |
| abstention: right on unanswerable / false on answerable | 5/5 · 0–1 of 24 | 5/5 · 0 of 24 |
| prompt tokens per question | ~13K | 122K |

A fourth run from a fresh clone of this repo on 23.10, following this README
(`eval/results/20261023-120606-auto-fresh-clone.md`, 3 min): yes / partly / no 12 / 16 / 1, context
recall 1.00, one citation attached to the wrong call (caught by the checker), abstention 5/5 with no
false abstentions, ~13K prompt tokens, and the same failures (q11, q30).

**After adding the vendor-claims context (23.10)**, q11 is answered correctly: both contradictions
(SSO on all plans vs Enterprise-only, "completely no-code" vs "we don't claim every workflow is
no-code"), in 4 of 4 manual runs and in the eval run (`eval/results/20261023-122047-auto-vendor-claims.md`:
13 / 15 / 1 overall, citation validity 1.00, abstention 5/5). Only q11 is routed to the new context;
the one "no" in that run is q05, a long list that stopped early, which was "partly" before.

**After weighing conflicts (23.10)**, q24 ("Is SSO on Growth?") is answered correctly for the first
time: it reports the conflict, then says Enterprise-only is better supported because nine calls and
three reps say so, while the single "all plans" came from one AE who later said he was only "fairly
sure". Run `eval/results/20261023-204145-auto-weighing.md`: yes / partly / no **15 / 14 / 0**, citation
validity 1.00 with no failed citations, abstention 5/5 with no false abstentions, ~14.5K prompt tokens.
Within the judge noise band, but q11 and q24 are now both "yes".

**After the name checks (23.10)**, q06 ("Acme Corp") is "yes" for the first time: the answer opens
with "Taking Acme Corp to mean Acme Logistics", and the note sits under the answer, where the judge
now sees it too. For q16 ("Priya") the required mention of the other Priyas is now met by the note,
from code; the answer still leaves out that her figures were from memory, so it stays "partly". Run
`eval/results/20261023-210435-auto-names.md`: 14 / 14 / 1. The changes do not touch q05, q11 and
q29, which moved anyway: q05 is the long list that stops early, q11 found only the SSO contradiction
this time (both in the previous runs), and q29 was judged as not declining although it says
"no Enterprise list price, custom priced". That is the noise this eval measures: compare per question,
not the totals.

**With turn-level evidence recall (23.10)**, run `eval/results/20261023-214420-auto-diagnostics.md`:
14 / 15 / 0, abstention 5/5, citation validity 1.00. Context recall is 1.00 but evidence recall is
**0.82**, and it splits by context mode: **0.96** when whole calls are sent (15 questions) and **0.54**
when excerpts are retrieved (8 cross-call questions; q05 0.08, q01 0.32, q09 0.36, q04 0.41). First
failed step: answer 7, retrieval 6, attribution 1.

**Three ways to answer questions across calls (23.10)**, same code otherwise (all with the turn
inventory except the first):

| | retrieval only | map step at question time | notes at ingestion (default) |
|---|---|---|---|
| run | `…-214420-auto-diagnostics` | `…-224354-auto-map` | `…-231007-auto-notes` |
| yes / partly / no (29) | 14 / 15 / 0 | 20 / 9 / 0 | 16 / 13 / 0 |
| the 7 cross-call questions that use it: "yes" | 3 | 4 | 5 |
| evidence recall: all / the 7 | 0.82 / 0.48 | 0.94 / 0.89 | 0.86 / 0.65 |
| core fact recall: all / the 7 | 0.70 / 0.66 | 0.81 / 0.84 | 0.78 / 0.75 |
| atomic fact recall, all | 0.57 | 0.66 | 0.68 |
| prompt tokens per question: mean / the 7 | 14.5K / 18K | 47K / 139K | 17K / 26K |
| failed citations (all flagged) | 1 | 6 | 4 |

On the cross-call questions the notes default sits between the other two on evidence and core recall
(notes are written without knowing the question), at about a fifth of the map step's tokens; its 5
"yes" against the map step's 4 is within the judge noise. One cost the table hides: indexing takes
~5 min instead of ~4, once. The full-run totals differ within the judge noise
(±6 on yes/partly). These three runs used medium reasoning in the answer step; latency is in *Speed*.

**With the map step and the turn inventory (23.10)**, run `eval/results/20261023-224354-auto-map.md`:
**20 / 9 / 0**, the first result clearly outside the judge noise band (14–15 "yes" before). Evidence
recall 0.94 (cross-call questions 0.89, was 0.54), core fact recall 0.81 (was 0.70), abstention 5/5.
The costs are real: mean prompt tokens 47K per question (was 14.5K; a mapped question reads every
candidate call, ~139K tokens, about the same as the whole-dataset baseline at 20 calls), mean latency
42 s under the eval's 4 parallel questions (mapped ones ~90 s), and 6 failed citations instead of 1
(three quotes from Ember's Noah Williams attached to other calls in mapped answers, three in whole-call
answers), all caught and marked ✗ by the checker. The inventory alone, replayed on the 7 questions that
failed in the answer step, raised core recall 0.64 → 0.69 and atomic 0.48 → 0.56 (two replays each),
without changing verdicts: the facts it still misses are context around a correct direct answer.
The map step is capped at 25 candidate calls; why it does not scale and what replaces it is in
*Scaling to thousands of calls*.

What I take from it:

- **Two different bottlenecks.** Questions about one or a few calls get whole transcripts, so
  everything reaches the model and the misses are in the answer step (details left out). Questions
  across all calls get retrieved excerpts, and there retrieval is the bottleneck: about half the
  supporting turns never reach the model. Earlier versions of this README said "retrieval is not the
  bottleneck", based on call-level recall only; turn-level recall showed that was wrong for
  cross-call questions. The map step closes most of that gap (0.54 → 0.89), at query-time cost.
- **The pipeline is no worse than the brute-force baseline at ~1/9 of the tokens, and its quotes are
  more reliable.** Not "better": re-judging the same answers with the same judge moved 6 of 30
  verdicts between yes and partly. The deterministic metrics and the yes-vs-no line are stable; the yes/partly split is not.
- **Unanswerable and near-miss questions work** in all runs (Kestrel's ERP, ISO 27001, Enterprise price).
- **Known failures**: q11 ("has the vendor given inconsistent answers?") was wrong in every run of the
  first version: the two sides of each contradiction sit in different calls and similarity search
  does not find disagreement. It is fixed by the vendor-claims context (above). q24 found both sides
  of the SSO question but would not weigh them; fixed by weighing (above). q30 (bonus) needs a second
  retrieval hop.

The gold set was drafted by an LLM, every citation checked against the source, and the 19 disputed
points decided by a human (`eval/review/`).

## Speed

Targets for a sales manager waiting on an answer with evidence: something on screen in under 2 s,
a question about one call in ≤ 8 s, a question across calls in ≤ 20 s, p95 ≤ 30 s.

Latency follows the tokens the model *generates* in the answer step, at roughly 180 tokens/s;
context size, retrieval, note selection and citation checks are each under a second. The breakdown
is printed under every answer (`[plan 1.3s · context 0.5s · answer 8.4s (1,298 out) · check 0.0s]`),
is in `--json` → `steps`, and the eval reports p50/p95 and the answer step's output tokens.

| one question at a time | before (medium reasoning) | now (low reasoning) |
|---|---|---|
| one call, whole transcript ("What was Verity paying?") | 7.7 s | 5.5 s |
| product fact, excerpts + vendor statements ("SSO on Growth?") | 30 s | 10.2 s |
| across calls, ingestion notes ("Why do prospects hesitate?") | 85 s | 18.9 s |

| full eval, 4 questions in parallel | medium | low (`…-235835-auto-effort-low`) |
|---|---|---|
| mean / p50 / p95 latency | 36 / 33 / 129 s | 9.9 / 8.1 / 21.7 s |
| answer step output tokens, mean | 6.3K | 1.3K |
| yes / partly / no · core · atomic | 16 / 13 / 0 · 0.79 · 0.67 | 18 / 10 / 1 · 0.80 · 0.67 |

The 11 example questions from the task, run one at a time (`--only q01,…,q11 --workers 1`):

| | medium (`…-002657-auto-examples-medium`) | low (`…-001127-auto-examples-low`) |
|---|---|---|
| mean / median / slowest | 72.9 / 61.3 / 175.5 s | **17.1 / 18.2 / 26.3 s** (4.3× faster) |
| all 11 in a row | 13.4 min | 3.2 min |
| yes / partly / no · core recall | 8 / 3 / 0 · 0.82 | 6 / 4 / 1 · 0.84 |

On these 11, completeness is the same but three verdicts moved down (q02 and q05 to "partly", q10 to
"no", the recurring "all five cold calls got a follow-up") and one up (q08); on the full 29 the
direction was the opposite (18 vs 16 "yes"). Both are within the judge noise, so the honest summary
is: 3–4× faster, same completeness, verdicts within noise and slightly lower on the task's examples.
If that matters more than speed, medium reasoning can be used for cross-call questions only.

What was tried, measured on the full eval:

- **Shorter inventory** (call and timestamp only, no description per turn): no gain. Most output
  tokens were reasoning, not the inventory (q04: 18.5K tokens out, an inventory of ~50 entries is
  under 1K), and the model listed more turns once each entry was cheap (32 vs 19 on average). Kept,
  since quality was the same (`…-235550-auto-compact`).
- **Low reasoning in the answer step** (`ANSWER_EFFORT`, default now `low`): 4–5× less output and
  3–4× lower latency with no loss in quality. The inventory written before the answer does the work
  the extra reasoning was doing. The one "no" (q10, "all five cold calls got a follow-up", Trafford
  did not) was the same error as in the medium run, there judged "partly".
- **Progress on screen**: the CLI prints each step as it starts (`planning` → `plan: across question
  over all calls; note fields: …` → `context: notes, 10 calls …; writing the answer`), so the first
  output arrives in well under 2 s even when the answer takes 15 s.

Not done yet, in order of expected gain: stream the answer text and check each citation as it
arrives; run the planner on a smaller model and embed the question while it plans (~1–2 s); keep the
static prompt and the transcripts ahead of the question so the provider's prefix cache applies to
repeated questions on the same calls; cache answers by normalised question and data version; and
provisioned throughput, since the spread under load (8 s alone vs up to 22 s p95 with 4 in parallel)
is the provider's.

## Diagnosing a bad answer

Each step leaves a record, so a wrong answer can be traced to the step that failed:

1. **Plan**: `callqa ask "..." --json` → `plan`. Wrong `call_ids`, a call-kind filter the question did
   not ask for, a missed name (`entity_notes`), or product topics on a question about customers.
2. **Context**: `--json` → `context` holds the mode, the calls, and every turn and line of text the
   answer step saw. Is the turn that answers the question there? In the eval this is
   `evidence recall`, and `failure` says `retrieval (n evidence turns not in context)`.
3. **Answer**: if the evidence was in context but the answer misses it (`failure: answer`), re-run only
   the answer step on the same context: `run_eval.py --replay <run>.json --only q05`. If a prompt
   change fixes it on replay, it was the answer step; retrieval noise is out of the picture.
4. **Citations**: every quote shows ✓ / ✗ with the reason (`wrong_speaker`, `wrong_call` with where
   the words really are, `not found`); `failure: attribution`.
5. **Judge**: if the answer looks right, read `correct_reason` and the per-fact verdicts in the results
   JSON, and re-judge with `--regrade`. The judge moves about 6 of 30 verdicts between yes and partly.

## Known limitations

- **Questions about relationships between calls** are the weak spot. Vendor contradictions are
  handled by the claims table, but only for statements by OrbitFlow staff and only as well as the
  extraction pass caught them; "who else said X" and two-step questions like q30 still rely on
  retrieval, which finds passages similar to the question, not passages that relate to each other.
- **Exhaustive lists**: "which customers mentioned X" can miss a call that mentions X once in passing
  if that excerpt ranks low, or if the answer stops early. The answer cannot say "this list is complete".
- **Judgement questions** ("most likely to buy") are only as good as one model's read of excerpts; the
  answer cites signals but there is no scoring rubric behind it.
- **The checker verifies that the quote exists and that the cited person said it, not that it supports
  the claim.** A real, correctly attributed quote attached to an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** are only surfaced when the question touches them.
- **Ingestion is not deterministic.** Four fresh indexes of the same 20 calls gave 522–628 vendor
  claims and 973–1,185 notes, and one gave three calls no claims at all (now retried, with a
  warning). Answers that depend on a single statement (q11 needs Alastair's "all plans" in CALL-006)
  can differ between two people's indexes; the claims and notes are inspectable in `.cache/callqa.db`.
- **The gold set is small (30) and LLM-drafted** (see `eval/EVALUATION.md`). The judge is
  from a different vendor than the answering model, but it is still an LLM and it is noisy on the
  yes/partly boundary.
- Single-turn, English, no auth. The transcripts are sent to an external LLM API.

## With more time

With another day:

1. **A product-fact table at ingestion**: vendor claims clustered by topic and subject with counts
   (people, calls, last date, hedged), and conflicts recorded when a call arrives. q11 and q24 then
   read a table instead of putting every claim on a topic into the prompt (see the scaling table).
2. **A full-context control for the map step**: the same 8 cross-call questions with all transcripts in
   the prompt (same token cost at 20 calls), to show whether reading call by call beats one big prompt
   on completeness and misattribution, not only on evidence recall.
3. **A second retrieval hop**: let the answer step request more context ("need: the call where an
   engineer reviewed an exported definition") before answering; this fixes q30-type questions.
4. **Entailment check on citations**: a small model checks that each quote supports its claim, not just
   that it exists.
5. **Better eval**: a majority of 3 judge passes per answer (the judge alone moves ~6 of 30 verdicts),
   3–5 repeats of the baseline too, and a blind human-graded subset (about 10 answers, stratified by
   verdict and question type) to measure how often the judge agrees with a person.

### Scaling to thousands of calls

The rule: reading calls is paid for once, at ingestion, not on every question; a question should
cost the same at 20 calls as at 20,000. Measured on the current 20 calls, per question:

| part | now | at thousands of calls | what to do instead |
|---|---|---|---|
| map step (read each candidate call) | ~139K tokens per cross-call question | ~6K tokens × every call: millions of tokens, minutes | **done**: notes at ingestion (default, ~26K tokens per cross-call question, most of the map step's gain); map kept as `--across map`, capped at 25 calls |
| notes at ingestion | 1,083 notes, top 250 by field and similarity | grows with calls; the answer still gets ≤250 | add metadata filters and a shortlist of calls before ranking notes |
| all vendor claims in one prompt (q11) | 628 claims | tens of thousands, does not fit | a product-fact table: claims clustered by topic and subject with counts (people, calls, last date, hedged); conflicts recorded when a new call is ingested |
| every vendor statement on a topic (q24) | 9 calls on SSO | hundreds per topic | the same table: "SAML SSO: Enterprise, 9 calls / 3 reps; all plans, 1 call, later hedged"; weighing becomes counting |
| catalogue in the planner prompt | 20 lines | does not fit | metadata filters plus fuzzy search over companies and people |
| per-call excerpt quota | 20 calls | thousands of excerpts | quota after filtering, on the top-N calls |
| name check over all transcripts | ms | slow | a name index built at ingestion |
| claim extraction, embeddings | once per call | once per call, incremental | fine as is: cached by content hash |
| citation check, inventory, eval | per answer | per answer | fine as is |

### Production

- **Ingestion**: new calls arrive as events; parse → chunk → embed → extract notes per call,
  idempotent by call id + content hash (the embedding cache already works this way). A proper store
  (Postgres + pgvector or a vector DB) replaces in-memory numpy/BM25, with metadata filters (date,
  segment, rep, stage) in the query.
- **Security and privacy**: transcripts hold customer PII and commercial terms. That means
  tenant/role-based access applied as a retrieval filter (a rep sees their own accounts, a manager
  their team's), a region-pinned LLM endpoint with no training on data and zero/limited retention,
  PII redaction where the use case allows, audit logs of questions and the turns they surfaced, and
  prompt-injection hygiene (transcripts are untrusted input: a customer can say "ignore previous
  instructions" on a call).
- **Operations**: run the eval in CI on prompt/model changes, log every question with its plan,
  context and citation checks, collect user feedback (thumbs down + "wrong citation"), and watch
  citation validity and abstention rate as live quality signals.
- **Cost/latency**: see *Speed*; in production also per-tenant rate limits and a latency budget per
  step, alerting on p95.
