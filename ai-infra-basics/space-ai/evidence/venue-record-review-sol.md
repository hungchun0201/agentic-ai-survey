# Independent review of the venue-record section / 頂會紀錄章節的獨立審查

Reviewer: `gpt-5.6-sol` at high reasoning effort, run on 2026-10-02 against the section text in both
languages, `program-screen.json` and `paper-corpus.json`. Verdict on the reviewed snapshot: **FAIL**,
with the located list reproduced below.

審查者為 `gpt-5.6-sol`（high effort），於 2026-10-02 針對雙語章節文字、`program-screen.json` 與
`paper-corpus.json` 執行。對受審 snapshot 的結論為 **FAIL**，完整的逐項清單如下。

## What was changed in response / 依審查結果所做的修改

- The table lead said the second column carried the physical assumptions; it is the third. Corrected in both languages.
- The zero-year sourcing sentence now states what the evidence file records: a second official page of the same programme for each zero year.
- The programme screen's own two limits, unequal denominators and title-level classification, are now stated in the section rather than only in the evidence file.
- Connex's 11 ms and 554 ms are no longer presented as one comparison; the section now says they come from different benchmarks. CacheGen's 81% to 8% now carries its experimental condition.
- The unlabelled dispersion in Theseus's 8 ± 5.1 ms and 206 ± 107 ms is removed; the section reports the averages.
- The bisection comparison now reads three and a half to four orders of magnitude, which is what 2.25 and 10 against 28,800 TB/s give, and bisection bandwidth is defined as the capacity across the narrowest equal split.
- Four scope overreaches were narrowed to the reviewed corpus: the assumptions that "can fail" rather than "are false" between spacecraft; the evidence bar; the power claim; and the third opening's occupancy. The closing observation is now stated in three explicitly scoped parts.
- Numbers quoted from papers that have no corpus record are now marked in the source file as reported-number tier, and the section says so where it quotes them.
- Acronyms are expanded at first use, and two long paragraphs were split.
- The Chinese prose was de-calqued against the reviewer's list, and the recurring noun is now 切入點 throughout.

Declined: the proposed unit-and-acronym primer paragraph, because the page's own foundations section
follows immediately and already teaches that material; and the wholesale paragraph rewrites, whose
substance was applied without adopting their wording.

未採納：建議新增的單位與縮寫前導段落——因為頁面緊接著就是基礎章節，該內容已在其中教學；以及整段改寫的
建議稿，其實質已逐項採納，但不沿用其措辭。

---

## Part 1 — English readability

### Release-blocking first-use jargon

The three randomly selected prose paragraphs were lines 2, 21, and 64.

1. [section-en.md:2](/tmp/claude-1000/-home-hclin-PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:2)

> “The corpus behind this page … SIGCOMM … ACM … AI datacenter.”

A zero-background reader could follow the overall contrast, but not the institutional and technical terms. Unexplained on first use: `corpus`, `ACM`, `AI datacenter`; SIGCOMM is only partially expanded.

Replace the paragraph with:

> Networking proposals should be compared with published work. The reviewed collection contains 60 papers, including 35 from SIGCOMM, the annual main conference of the Association for Computing Machinery (ACM) Special Interest Group on Data Communication. Across 2022–2026, those 35 papers form two groups: papers about satellite networks, and papers about networks that connect specialized processors for artificial-intelligence workloads. This section asks where those groups overlap and which questions remain unanswered within the screened record.

2. [section-en.md:21](/tmp/claude-1000/-home-hclin-PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:21)

> “none of them carries traffic whose next step waits on the last byte”

A zero-background reader would not reliably follow it. Unexplained: `mobile-core signaling`, `control-rate data`, `radar waveform`, `downlink`, and the dependency implied by “waits on the last byte.” It also overstates the evidence: mobile-core signaling and CommSAR traffic are bidirectional, and their delay tolerance is not uniform.

Replace the paragraph with:

> The eleven papers do not carry communication whose next computation step must wait for every byte to arrive. Their workloads include broadband and web traffic; control messages that establish handset service; Earth-observation images; small sensor reports; and low-rate control data embedded in radar signals. Their tolerance to delay varies, and some traffic is bidirectional, but none imposes the step-by-step communication dependency of distributed accelerator computation.

3. [section-en.md:64](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:64)

> “LLM inference and serving, collective communication algorithms, in-network aggregation … scale-up fabrics”

A zero-background reader cannot follow the session-name list. Unexplained: `LLM`, `inference`, `serving`, `collective communication`, `in-network aggregation`, and `scale-up fabric`. Calling SIGCOMM “an AI-infrastructure venue” from a 26.6% title share is also overstated.

Replace with:

> First, AI-infrastructure networking has become a substantial SIGCOMM programme category: 29 of the 109 listed titles in 2026, or 26.6%, concern networks for machine-learning workloads, compared with one title in 2022. The programme also shifted toward sessions on large-language-model inference, model serving, coordinated communication among accelerators, processing performed inside the network, high-bandwidth local interconnects, and training-cluster scheduling.

### Subsection openings and tables

No subsection starts cold. Each opening states what it builds on and why it is present.

No table is bare. Each table has a lead-in that states what it enumerates. There is, however, a wrong reading instruction at [section-en.md:28](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:28):

> “the second column is where an orbital setting breaks”

The assumptions are in the third column.

Replace with:

> The table states, for every family, what it already establishes and the physical assumption on which it depends. The third column identifies assumptions that can fail in an orbital setting and therefore locates the remaining design question.

Make the same `第二欄` → `第三欄` correction in [section-zh.md:28](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-zh.md:28).

### Paragraphs that are piles rather than arguments

- [section-en.md:27](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:27) combines the second track’s purpose, counts, growth, scope caveat, next-subsection preview, Cyclops overlap, and arithmetic. Split after “settled literature” and before the Cyclops reconciliation.

- [section-en.md:74](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:74) combines two detailed systems, three bibliographic identities, an unscreened-venues caveat, and the central absence. It needs three paragraphs: verified satellite-ground precedents; neighbouring identities; scoped residual claim.

### Unexplained acronyms, units, and quantities

The section needs a compact primer after line 3. Exact insertion:

> Artificial-intelligence systems train models by adjusting parameters from examples and perform inference by using a trained model to produce an output. They run on accelerators—specialized processors, usually graphics processing units (GPUs)—connected by a datacenter network. A satellite contact is a predicted interval during which two endpoints can communicate; an inter-satellite link connects two spacecraft. Bandwidth is the amount of data a link can carry per second, and latency is the time an operation takes. Units below use ms for milliseconds, s for seconds, Kbps/Gbps/Tbps for thousand/billion/trillion bits per second, GB/TB for billion/trillion bytes, W for watts, m for metres, and km for kilometres.

Other first-use repairs required:

- [Line 11](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:11): replace `5G NTN` with `fifth-generation non-terrestrial networking (5G NTN)`.
- [Line 19](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:19): replace `Planet-Scale IoT` on first descriptive use with `Planet-Scale Internet of Things (IoT)`.
- [Line 27](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:27): replace `NSDI` with `the USENIX Symposium on Networked Systems Design and Implementation (NSDI)`.
- [Line 32](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:32): replace `AllGather` with `AllGather, in which every participant receives every participant’s data`.
- [Line 36](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:36): replace first `NIC` with `network interface card (NIC)`.
- [Line 64](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:64): expand `LLM` as `large language model (LLM)`.
- [Line 74](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:74): define `B` as billion parameters, `LEO` as low Earth orbit, and `IEEE` as the Institute of Electrical and Electronics Engineers.
- [Line 84](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:84): expand `RDMA` as remote direct memory access.
- [Line 100](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:100): expand `CCSDS` as Consultative Committee for Space Data Systems.
- [Line 118](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:118): expand `UDP` and `TCP`.

Several numbers arrive before their significance:

- Line 17: replace `at 17 ms mean inference` with `in a mean 17 ms—2,738 times faster than its solver baseline`.
- Line 19: replace the queue sentence with:

  > Dissecting the StarLink estimates approximately 1,500 packets in the downlink bottleneck queue and 4,000 in the uplink queue, making the estimated uplink queue about 2.7 times deeper.

- Line 19: replace the CommSAR rates with:

  > CommSAR carries data inside an imaging waveform at 105 Kbps down and 112 Kbps up—approximately 13 and 14 kilobytes per second, respectively, which is control-rate rather than datacenter-fabric capacity.

- Line 34 uses `±` without saying what statistic it denotes. The corpus also does not label it. Until checked in the primary paper, replace with:

  > Theseus reports average delta-migration setup of 8 ms, compared with 206 ms for a fresh setup.

### Register

No banned literal tokens, arrow chains, bold one-word sentences, or second-person address occur. The broader register nevertheless fails: it reads as an insider’s submission-positioning memo.

Examples and replacements:

- [Line 7](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:7):

  > “consequences for anyone planning a submission … a reviewer’s recent reading”

  Replace with:

  > This distribution identifies the relevant comparison set. Because almost all satellite papers appeared in 2025 and 2026, current work should be compared primarily with that cohort rather than only with the 2022 paper.

- [Line 65](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:65):

  > “A submission that joins the two therefore faces an audience…”

  Replace with:

  > Work that joins the two tracks must explain the orbital constraints explicitly and compare its mechanism with current AI-fabric baselines.

- [Line 90](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:90):

  > “That is where a position argument belongs”

  Replace with:

  > These workshop papers show that orbital computing is already an agenda-setting topic, but they do not by themselves establish main-track novelty.

- [Line 105](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:105):

  > “worth a paper … how interesting the question sounds”

  Replace with:

  > Each row identifies the established mechanism, the remaining mechanism, and an experiment that could determine whether the remaining mechanism produces a measurable benefit. The order reflects the availability of the required experimental apparatus.

Overall judgment: insider’s memo, not a zero-background teaching narrative.

## Part 2 — Factual integrity

### Counts

All requested counts reconcile:

- Corpus: 60 records.
- SIGCOMM records: 35.
- Central satellite papers: 11, distributed `1/0/0/6/4`.
- Comparator set: 24, comprising 22 SIGCOMM papers plus TACCL and TopoOpt at NSDI.
- AI-infrastructure programme counts: `1/3/7/15/29`.
- Listed-title denominators: `57/73/62/88/109`.

The Cyclops arithmetic is numerically correct but badly explained. Cyclops is discussed in two analytical roles but counted only once, among the 22 comparators. The unique-record partition is:

`11 central satellite + 2 aerial adjacencies (Loon and UAV 5G) + 22 comparators including Cyclops = 35`.

Replace the final sentence of [line 27](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:27) with:

> Cyclops is discussed twice—as an optical-terminal adjacency and as a transferable comparator—but is counted only once, in the comparator category. The 35 distinct SIGCOMM records therefore partition into eleven central satellite papers, two aerial adjacencies, and twenty-two comparators.

### Unsupported programme-screen claims and omitted caveats

[program-screen.json:12](/home/hclin/PhD_Research/agentic-ai-survey/ai-infra-basics/space-ai/evidence/program-screen.json:12) says the denominators are not identically constructed and title-level classification can miss hidden workloads. The section omits both limitations.

Add to [section-en.md:49](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:49):

> The 2022 and 2023 denominators come from programme pages, whereas the 2024–2026 denominators come from accepted-paper pages, so the denominators are not identically constructed. Classification from titles can miss workloads not named in a title; satellite candidates were additionally checked against abstracts or session placement.

[Line 6](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:6) claims:

> “including two independent official sources for each of the two zero years”

`program-screen.json` records one official URL for each year, not two independent sources. Replace with:

> The programme screen records an official listing for every year and additionally checks satellite classifications against abstracts or session placement, so the two zero years are audited rather than inferred from the reviewed corpus.

### Per-paper numbers

The following match the corpus records:

- SpaceCore: 122.2×.
- SaTE: 17 ms and 2,738×.
- CoOrbit: 108.6× and 41.6×.
- Theseus: 8 ± 5.1 ms and 206 ± 107 ms.
- Connex: approximately 11 ms and 554 ms.
- CacheGen: 81% to 8%.
- Cyclops: 9.4 and 23.5 Gbps.
- In-orbit instability: near 9 W and up to 10% throttling loss.
- Bisection estimates: 2.25, 10, and 28,800 TB/s.

I also checked the queue estimates, CommSAR rates, StarCDN percentage, Loon recovery result, TE-CCL synthesis time, MixNet and Opus switching times, Flare credit waste, GeoOrchestra path, OrbitalBrain result, optical-bench rates, TinyLEO link assumptions, contact durations, radiator mass, and Hypatia simulation times. Those reconcile.

Two presentations are misleading despite containing the right numerals:

- [Line 40](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:40) presents Connex’s 11 ms and 554 ms as one direct comparison. The corpus says they come from different microbenchmarks.

  Replace with:

  > Connex reports approximately 11 ms for pair-local blocking cutover in a cross-pod microbenchmark; a separate same-node, two-rank benchmark reports approximately 554 ms for destroy and reinitialize.

- The same line omits the condition on CacheGen’s 81%→8% result.

  Replace with:

  > In a random-bandwidth experiment with a one-second time-to-first-token objective, CacheGen reduces objective violations from 81% to 8%.

### Quantitative claims absent from `paper-corpus.json`

These violate the stated traceability rule:

- [Line 74](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:74): `2 B`, `7 B`, `110.67 Mbps`, `4.33%`, `6.3 s`, and `7.9 s`.
- [Line 94](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:94): SkyMemory’s `21–24%` and `1.1 B`; ImpactHO’s `93.7%`, `500 ms`, `391 ms`, and `847 ms`.
- [Line 110](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:110): the closest preprint’s `20 Gbps`.

Either add structured primary-source records to `paper-corpus.json`, or remove the numbers. A publishable interim replacement for line 74 is:

> Outside the screened networking venues, two programme-verified main-track papers report large-model service over real satellite-to-ground links: one at ACM Multimedia 2025 and one at SenSys 2026. Both exclude inter-satellite links by construction. Their quantitative results are omitted here because these papers do not yet have reviewed records in the structured paper corpus.

For the preprint row, remove the unsupported numbers and retain only the qualitative descriptions until records are added.

### Incorrect standards claim

[Line 100](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:100) says:

> “each contact begins no later than the previous one ends”

The recorded definition says that contact `i+1` ends no earlier than contact `i` begins. The current wording reverses which endpoints are compared.

Replace with:

> The standard defines a route as a sequence of contacts in which contact i+1 ends no earlier than contact i begins; it defines the volume of a contact as its duration multiplied by its data rate.

The Chinese sentence at [section-zh.md:100](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-zh.md:100) repeats the error. Replace with:

> 該標準把 route 定義為一串 contact，其中 contact i+1 的結束時間不早於 contact i 的開始時間；contact volume 則定義為持續時間與資料速率的乘積。

### Scope overreach

These are release blockers:

- [Line 46](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:46):

  > “Each of them is false between two spacecraft”

  Replace with:

  > Each assumption can fail between spacecraft: an optical link has a predicted line-of-sight deadline, and an alternate control or data path may not be available.

- [Line 77](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:77):

  > “A first result in this area”

  This generalizes beyond the corpus. Replace with:

  > Any new result evaluated against this corpus should separate direct measurements from extrapolations.

- [Line 116](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:116):

  > “The only in-orbit energy measurement available … every accelerator-scale power claim in this area is currently a model.”

  Replace with:

  > The reviewed corpus contains one in-orbit energy measurement, which reports instability near 9 W; the accelerator-scale power studies in this corpus are models rather than in-orbit measurements.

- [Line 121](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:121):

  > “The third opening is the least occupied”

  Replace with:

  > Within the reviewed corpus, the third opening has the fewest direct precedents.

- [Line 122](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:122):

  > “the inter-satellite case is occupied only at preprint and workshop tier”

  The page admits that several relevant venue families were not screened. Replace the whole central observation with:

  > Within the reviewed corpus and the five-year SIGCOMM title screen, no SIGCOMM main-track paper joins the two tracks. Two verified main-track papers at other venues serve large models over satellite-to-ground links. Among the records reviewed here, inter-satellite work appears only as preprints and workshop papers; no claim is made about the unscreened venue families.

Also change [line 75](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:75):

> “The orbital figures sit four orders of magnitude below…”

For 10 versus 28,800 TB/s, the difference is about 3.46 orders; for 2.25 it is about 4.11. Replace with:

> The two orbital estimates are approximately three and a half to four orders of magnitude below the terrestrial estimate.

And replace:

> “it is the quantity a collective consumes”

with:

> Bisection bandwidth is the aggregate capacity across the narrowest equal partition of a network; communication-heavy collective operations can be constrained by it.

### Scope-note attribution

[Line 76](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-en.md:76) does state that the notes were written by the survey, so the provenance is technically disclosed. The subsequent possessives—“CommSAR’s note,” “DeepSpace’s note”—nevertheless sound like author quotations.

Replace each with `The survey’s note on CommSAR`, `The survey’s note on DeepSpace`, and so forth.

## Part 3 — Chinese version

### Meaning differences

- [Line 23](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-zh.md:23): `radio-on time` becomes `開機時間`, which can mean whole-device uptime.

  Replace `值得花費開機時間` with `值得耗用無線電開啟時間`.

- [Line 34](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-zh.md:34): English `deterministically` becomes `可預期`, which is weaker.

  Replace `能以低成本、可預期的方式` with `能以低成本且具決定性的方式`.

- [Line 114](/tmp/claude-1000/-home-hclin/PhD-Research-MAS-attention-selection/ec35ce44-aea8-4a78-8476-5ae7401f356d/scratchpad/spaceai/review/section-zh.md:114): Chinese specifies `標準差`, while English only says `deviation`. Align the English to `mean-plus-standard-deviation threshold` if that is what the primary paper establishes; otherwise the Chinese must not add `標準`.

### Simplified Chinese

No Simplified-only character was found. This criterion passes.

### Machine-translated or memo-like Chinese

At minimum, replace these:

| Location | Offending text | Exact replacement |
|---|---|---|
| Line 2 | `這個題目投稿會面對的場域` | `也是這類研究通常投稿的主會議` |
| Heading 5 | `衛星載體在一個週期內進場` | `衛星網路研究集中在最近一輪出現` |
| Line 6 | `它在時間上的形狀` | `它的年度分布` |
| Line 22 | `面對一次不好的 contact，可以選擇睡過去` | `遇到品質不佳的 contact 時，可以停用無線電並等待下一次 contact` |
| Line 23 | `讓它成為適合動工之處` | `因此提供了可延伸的研究基礎` |
| Line 27 | `本報告持續盯著它` | `本報告納入這條軌跡` |
| Line 38 | `congestion state 必須跨越以分鐘計的空檔繼續老去` | `congestion state 必須在持續數分鐘的中斷期間保留，並明確判定何時失效` |
| Line 44 | `新穎性邊際最薄` | `可主張的新貢獻範圍也最小` |
| Line 65 | `軌道物理需要被教會` | `軌道物理限制必須清楚說明` |
| Line 74 | `仍然沒有主會議論文處理的是` | `在已篩查的紀錄中，尚無主會議論文處理以下情境` |
| Line 77 | `全集中最強的` | `整個集合中最強的` |
| Line 80 | `以較低的「programme 層級身分已查核」層級進入紀錄` | `僅以「programme 身分已查核」的較低證據層級列入` |
| Line 90 | `主會議上的這個開口是被預期的` | `這些 workshop 顯示該題目已進入議程，但不足以證明主會議層級的新穎性` |
| Line 96 | `這個問題對這個社群而言是現在就讀得懂的` | `這個社群已明確把狀態搬運列為當前研究議題` |
| Heading 104 | `紀錄揭露的五個開口` | `紀錄揭露的五個研究切入點` |
| Line 105 | `不是來自願望清單` | `並非任意列舉` |
| Line 106 | `框住了前兩個開口` | `界定了前兩個研究切入點的範圍` |
| Line 112 | `預測錯誤會受罰` | `其效能會因預測錯誤而下降` |
| Line 118 | `成本高到必須先編預算` | `運算成本高，必須明確納入實驗資源估算` |
| Line 120 | `在線終端` | `實際運作中的終端` |
| Line 121 | `第三個開口最空` | `第三個研究切入點的直接相關工作最少` |
| Line 121 | `決策解在地面` | `決策由地面規劃器計算` |
| Line 122 | `可量測地改變了什麼` | `帶來哪些可量測的改變` |
| Line 123 | `值得先走` | `值得優先研究` |

### House-style technical terms

The specified terms—`collective`, `fabric`, `contact`, `primary text`, and the cache term—are generally retained in English. For consistency, use `KV cache` rather than alternating between `key-value cache`, `KV-Cache`, and Chinese descriptions.

## Verdict

**FAIL** — the section contains multiple unexplained first-use terms, unsupported per-paper numbers, an incorrect CCSDS definition, omitted programme-screen caveats, and several claims that overreach beyond the reviewed corpus. The Chinese contains no Simplified characters, but it also needs substantial de-calquing before publication.