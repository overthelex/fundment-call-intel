# Gold notes: dataset traps

Found during a full read of all 20 transcripts. Timestamps are `[MM:SS]` inside each call.

## Vendor contradictions (OrbitFlow staff)
- **SSO tier.** Alastair McCrae says "SSO's included on all our plans" (CALL-006 [07:23]) and is then only "fairly sure" ([14:50]). Every SE says SAML SSO/SCIM are Enterprise (CALL-001 [20:05], CALL-002 [01:59], CALL-004 [02:09]). Leo Grant says "SAML SSO is Enterprise" (CALL-012 [08:09]).
- **Billing term.** Alastair says monthly is "usually fine" (CALL-006 [08:25]). Everyone else presents Growth as an annual agreement (CALL-001 [04:50], CALL-003 [06:41]).
- **No-code.** Alastair says "completely no-code" (CALL-006 [11:30]). Jon Bell: "We don't claim every workflow is no-code" (CALL-001 [12:12]).
- **Uplift policy.** Maya says the 7% uplift "applies to everyone" (CALL-011 [08:24]). Leo offers Pinewood a six-month term with "no uplift" (CALL-012 [09:50]).
- **Enablement.** Maya says sitting-with-team enablement is paid PS (CALL-014 [05:23]). Leo includes it for free (CALL-012 [16:21]).
- **Pricing flexibility.** Alastair floats re-pricing for Oakhill (CALL-015 [03:25]) after originally saying "the entry point is Growth" ([06:47]). This matches his "the price is the price" stance at Fable (CALL-006 [08:41]).
- **Overstated claims.** Alastair says "all native connectors, no problem" (CALL-006 [03:19]), "up and running in a couple of weeks" ([11:58]), and "integrate with anything that's got an API" (CALL-019 [01:50]). He gets Trafford's practice count wrong: 14 vs 11 (CALL-019 [00:34]-[00:44]).

## Header / manifest vs body, and within-call contradictions
- **Greenline size.** Header says 2,300 employees. Carlos says his six-person team is "supporting two and a half thousand" (CALL-007 [06:49]): the load on his team, rounded, not the headcount. Not a conflict after review.
- **Verity's spend.** Ruth and Kwame say it is an £80K account ([11:40], [13:46], [18:52]). Sarah's "costs a hundred thousand a year" ([06:56]) has no currency, is rhetorical, and Maya immediately relates it to Workato ([07:13]); after review it is not treated as a conflict (flagging it is a bonus).
- **Ruth's Verity takeover.** Ruth says January ([00:41]) and Kwame confirms it ([04:24]). His later "You weren't there in February" ([20:34]) reads, on review, as taking the February failure off Ruth, with her "I was there in April" pointing to the April episode ([13:06]-[13:23]); it is not a contradiction. "Month twenty" ([04:48]) does not reconcile with a two-year contract ending 31 October and is not used.
- **Pinewood reschedules.** Ruth says "rescheduled twice", Graham says "Three times" (CALL-012 [00:00]-[00:08]). Graham says he has avoided the meeting for four months, Nadia says five ([21:47]-[21:51]).
- **Oakhill tenure.** Hazel has wanted the compliance workflow "for three years" (CALL-015 [05:11]) but has been a customer for two years ([03:44], [08:19]).
- **Silverline call length.** Chloe offers "five minutes", Martine says "three" (CALL-017 [02:34], [03:50]). The header also gives Martine a join time (03:41) that manifest.json does not carry.

## Customer self-corrections ("inconsistent customer descriptions")
Each prospect call contains one; RAG must not freeze the pre-correction version.
- 001 [05:57] onboarding is "standardised" per the deck, but EMEA and NA milestones differ.
- 002 [10:04] policy says no PHI in HubSpot, but names do appear in free text.
- 003 [04:11] Zendesk angle overstated: only ~1/4 of the Zaps touch it.
- 004 [12:14] "cloud-first" policy, but two German plants can't expose databases.
- 005 [17:19] "all approvals in Jira" softened for low-risk approvals.
- 006 [02:28] onboarding isn't one process; pods customise it.
- 007 [07:32] not fully centralised: North and South West have their own Power Automate specialists.
- 008 [22:42] "no new interface" softened.
- 009 [02:18] health scores are unreliable per Darren, and that claim is itself an impression ([27:04]).
- 010 [03:38] ops own business logic, not connector code or secrets.

## Near-duplicates and entity collisions
- **"Sixty Zaps".** Cedar & Finch: "more than sixty Zapier automations" (CALL-003 [02:39]). Lumen's former estate: "Sixty-odd Zaps, half of them orphaned" (CALL-011 [14:43]).
- **Names.** Maya Chen (vendor) / Marcus Chen (Juniper) / Marcus Lee (Cedar & Finch). Leo Grant (vendor) / Olivia Grant (Inkwell). Priya Shah (BrightPath) / Priya Menon (Beacon) / "Priya" at Juniper / Priyanka (Lumen). Tom Alvarez (Acme) / "Tom" at Juniper (CALL-010 [24:46]).
- **"Acme Corp"** does not exist. The only Acme is Acme Logistics (CALL-001).
- **Boilerplate.** Near-identical prospect lines recur across calls ("the happy path is not the hard part", "fifteen times last month", "team rather than a named individual", "don't find out in month four that every approver needs a full seat"). Retrieval by phrase alone returns many calls.
- **Boilerplate (vendor).** The security pitch is near-verbatim in 001/002/004/005/008/009/010, so chunks from different calls look interchangeable.

## Numbers that collide or shift
- **"Eleven".** BrightPath backlog of 11 weeks (CALL-002 [08:32]), Harbor's 11-day record (CALL-008 [01:54]), Juniper's 11 days to ship (CALL-010 [10:17]), Lumen ticket sat 11 days (CALL-011 [12:38]), Pinewood 11 tickets ([14:25]), Halberd 11 to 4 days (CALL-013 [16:34]), Oakhill 11 workflows, Trafford 11 practices, Kestrel 11 orders.
- **Contract dates.** Lumen expires 18 Oct. Verity ends 31 Oct. Oakhill leaves 11 Nov. Pinewood renews 29 Nov with notice due 30 Sep. Halberd renews in November.
- **Lumen tiers.** Contracted 250K, actual ~280K, options 350K/400K. Percentages: 7% uplift, ~9% total, 14% with nine seats, 22% June overage.
- **Annual Growth cost.** "Twenty-one, six" (CALL-003 [11:50]), "twenty-one and a half thousand" (CALL-006 [09:01], CALL-015 [01:28]). Growth's currency is never stated; pounds appear only for other figures (006, 014, 015, 020).
- **Approval thresholds.** Cedar & Finch 15K, Fable 20K, Acme finance above 25K.

## Facts that are deliberately absent (abstention bait)
- No ISO 27001 (only SOC 2 Type II). No Enterprise price ("custom"). No prepay or multi-year discount %.
- Kestrel's ERP is withheld (CALL-020 [03:34]). The Hannover Messe vendor is never identified (CALL-004 [29:11]).
- No UiPath, Boomi or n8n. "HIPAA" is never said, though BrightPath's BAA/PHI discussion implies it (CALL-002 [01:01]).
- OrbitFlow has no German region and UK residency is unconfirmed (CALL-004 [02:39], CALL-007 [16:22], CALL-008 [11:26]).
- Maya credits the "visibility vs coordination" line to "a customer ... in July" (CALL-018 [02:42]). That plausibly means Greenline (CALL-007 [01:17]), but the transcript doesn't say so.
