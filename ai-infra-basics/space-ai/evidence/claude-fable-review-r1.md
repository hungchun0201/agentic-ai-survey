# Independent review — "Satellite Networking for Orbital AI Centers"

**Score: 8.4 / 10 — Verdict: REVISE**

The census is correct and the mathematics checks out, yet six substantive gaps hold the artifact below the 9.0 release bar. The largest is the terrestrial-baseline set for the three LLM projects, which stops at 2023 while SIGCOMM 2024–2026 published the closest prior art.

**Reviewed file:** `site/ai-infra-basics/space-ai/index.html`

**SHA256:** remains open in this review. My toolset (Read, Glob, Grep, WebFetch) excludes hashing. Two hashes in the evidence directory belong to earlier review snapshots, and their match to the current file is unconfirmed; the lead should attach a fresh hash to the next round.

**Independence note:** `evidence/QA.md:28` states earlier review scores, and I saw them while inspecting the QA record. The score above derives only from the findings below. I left `technical-review-r1.md`, `technical-review-r2.md`, `code-review.md` and `fable-review/response-r1.jsonl` unopened, apart from one grep line for the hash.

---

## 1. Yearly census (my inspection of the official programmes)

The survey's count of 11 satellite-centric main-track papers plus Loon is confirmed. One aerial-adjacency candidate in 2026 awaits explicit adjudication.

| Year | Programme | Satellite-centric main-track papers (exact titles, quoted) | Adjacent / candidates |
|---|---|---|---|
| 2022 | [program](https://conferences.sigcomm.org/sigcomm/2022/program.html) — all 55 research titles read | "A Case for Stateless Mobile Core Network Functions in Space" (Technical Session 4: Wide Area Networks; `sources-a/program-2022.txt:747`) | "SDN in the Stratosphere: Loon's Aerospace Mesh Network" (`:686`) — included as adjacent ✔ |
| 2023 | [program](https://conferences.sigcomm.org/sigcomm/2023/program.html) — all 73 titles across 17 sessions read | Zero | Zero |
| 2024 | [program](https://conferences.sigcomm.org/sigcomm/2024/program/) — all 62 titles read | Zero | Zero |
| 2025 | [papers-info](https://conferences.sigcomm.org/sigcomm/2025/program/papers-info/) | "LeoCC: Making Internet Congestion Control Robust to LEO Satellite Dynamics" (Measurements; `program-2025.txt:64`); "DeepSpace: Super Resolution Powered Efficient and Reliable Satellite Image Data Acquistion" (source spelling; AI for SysNet; `:119`); "SaTE: Low-Latency Traffic Engineering for Satellite Networks" (`:352`); "Small-scale LEO Satellite Networking for Global-scale Demands" (`:357`); "Direct-to-Cell Satellite Network without Satellite Navigation" (`:361`); "StarCDN: Moving Content Delivery Networks to Space" (`:365`) | Zero |
| 2026 | [papers](https://conferences.sigcomm.org/sigcomm/2026/program/papers/) | Quoted session name "Research Session 16: Satellite & Non-Terrestrial Networks" (`program-2026.txt:1984`): "CommSAR: Enabling Bidirectional Communication in SAR Imaging Satellites via Shared Waveform" (`:1986`); "Planet-Scale IoT Connectivity via LEO Satellites" (`:2010`); "Dissecting the StarLink: Characterizing Queuing and Flow Dynamics in the Starlink Network" (`:2026`); "Achieving Efficient Storage and Communication via Collaboration" (`:2045`) | **Candidate:** "Unveiling Low-Altitude 5G Performance: Linking Key Influencing Factors with UAV Flight Parameters" (Research Session 4: Cellular & RAN Systems; `:464`) |

Totals: 1 + 0 + 0 + 6 + 4 = 11, plus Loon. This matches the page's audit table and `evidence/ADJUDICATION.md:11-17`.

---

## 2. Checks performed

**My inspection**
- **English text:** all 2,376 lines of `page-en.txt`.
- **Chinese text:** main narrative lines 1–840 and the audit block 1104–1163 of `page-zh.txt`; the rest of the Chinese appendix was sampled through corpus fields and a Simplified-character scan.
- **Corpus:** all 37 record identities (id, venue, year, URL, figure number, acquisition mode); full bilingual fields for the first two records.
- **Programmes:** two broad term scans over the complete local snapshots of all five years, covering satellite, orbit, aerospace, balloon, UAV, flight, GNSS, Earth observation, free-space optics and about forty related terms. Titles were read in full for 2022–2024 and by session and targeted region for 2025–2026.
- **Live site:** WebFetch of the 2023–2026 programmes. Each fetch returned only the opening sessions (2023: 11 of 17; 2025 and 2026: Day 4 and Session 16 fell outside the returned window), so the live results corroborate the opening portions and the local snapshots carry the complete evidence.
- **Arithmetic:** recomputed the worked numbers for A1, B1, B2, B3, B4 and the reconfiguration duty fraction, and inspected A2–A6, B5 and B6 for formal correctness.
- **Primary-source spot checks**, all matching the page:
  - SpaceCore Table 4 (`sources-a/spacecore.txt:997,1058`).
  - TinyLEO satellite counts (`tinyleo.txt:808-829`).
  - Suncatcher 800 Gbps / 1.6 Tbps / 9.6 Tbps / 81 spacecraft / 650 km / 67 MeV (`sources-b/suncatcher.txt:188-192,558,594`).
  - Dark Clouds 3.03 m²/kW, 10 kg/m², 44.3 kg, 30.5 kg, 68.8 % (`dark-clouds.txt:105-106,250`).
  - SN² 4.4–23.5× and 1.9–12.3× (`sn2-reader.txt:121-124`).
  - LeoCC 95.2 / 95.8 % and Jain 0.98–0.99 (`leocc-reader.txt:13723,13879`).
  - OrbitalBrain venue identity (`orbitalbrain.txt:31,56`).
  - SIGCOMM '26 and LEO-NET '26 DOIs share prefix 10.1145/3789240, consistent across five source headers.
- **Screenshots:** five of sixteen (EN desktop hero, workloads, regime B; ZH mobile hero, regime B, lab).
- **Original figures:** five of 37 (LeoCC, CoOrbit, Planet-IoT, First Look, Hypatia).

**Machine-report evidence (read, with my own verification limited to what is listed above)**
- `evidence/responsive-qa.json`: 16 engine/width/language cells pass, 12 math blocks painted, 37 images, zero SVG overlaps.
- `evidence/figure-qa.json`: 37 of 37 figures pass.
- `evidence/QA.md`: gate table.

**Verified strengths**
- Census: 11 papers plus Loon confirmed against the programmes.
- Counts: 37 corpus records match the venue table (12+5+3+2+3+3+1+1+1+2+4).
- Every worked number I recomputed is correct: 95.5 min orbit; 1.83 / 3.67 ms; 29.4 kW usable; 34 / 51 / 37 accelerators; 41.3 / 31.4 kW rejection; 24.5 GB per rank; 1.96 s / 19.6 ms; 1.074 GB KV; 85.9 / 859 ms; 9.1 % / 99.0 %.
- Evidence tiers (measured, replayed, simulated, analytical) are separated carefully throughout the records, e.g. CommSAR, Planet-IoT, CosMAC, Suncatcher.
- OrbitalBrain is treated candidly as direct training prior art.
- The three project gates carry numeric thresholds and stop rules.

---

## 3. Required findings and concrete fixes

### F1 — Terrestrial baselines stop at 2023; the target venue's own 2024–2026 programmes hold the closest prior art (Requirement 6; major)

The page names NCCL, TACCL (NSDI 2023), TopoOpt (NSDI 2023) and OrbitalBrain. A search of the page for TE-CCL, CacheGen, KVServe, Connex, Theseus, TDTCP and Flare returns zero matches. The official programmes contain:

- **Project 1 (temporal collective service)**
  - SIGCOMM 2024: "Rethinking Machine Learning Collective Communication as a Multi-Commodity Flow Problem"; "MCCS: A Service-based Approach to Collective Communication for Multi-Tenant Cloud"; "Crux: GPU-Efficient Communication Scheduling for Deep Learning Training".
  - SIGCOMM 2026 Session 3 (`program-2026.txt:285-360`): "Theseus: Runtime-Adaptive GPU Collective Communication with Hot-Swappable Schedules"; "OptCCL: Scalable Synthesis of Optimal Collective Communication Algorithms"; "Trivance: Latency-Optimal AllReduce by Shortcutting Multiport Networks".
  - Time-varying-path transport and fabrics: "Time-division TCP for Reconfigurable Data Center Networks" (2022, `program-2022.txt:185`); "Realizing RotorNet: Toward Practical Microsecond Scale Optical Networking" and three sibling reconfigurable-network papers (2024); Flare (2025, `program-2025.txt:337`).
- **Project 2 (contact-aware KV residency)**
  - "CacheGen: KV Cache Compression and Streaming for Fast Large Language Model Serving" (2024).
  - SIGCOMM 2026 Session 1: "KVServe: …" (`:89`), "DualPath: …" (`:113`), and "Connex: Endpoint Mobility Primitives for Dynamic LLM Serving" (`:154`). The Connex abstract describes a mobility contract, epoch-based routing and explicit handover with KV transfers in flight (`:161-173`), which overlaps directly with the page's "byte-and-deadline contract" and handover-token-gap hypothesis.
- **Project 3 (power-aware communication islands)**
  - "Janus: A Unified Distributed Training Framework for Sparse Mixture-of-Experts Models" (2023, `program-2023.txt:655`).
  - "UBEP: Re-architecting Expert Parallelism Communication Library for Production Superpods" and "HyNA: Taming Tail Latency in MoE Training with Hybrid Switch Silicon" (2026, `:583`, `:514`).

**Fix:**
1. Add a "Terrestrial prior art at SIGCOMM 2022–2026" table that maps each of the three projects to these works.
2. For each project, state the residual novelty once a schedule-informed variant of the nearest work receives the same contact forecast.
3. Extend the named-baseline table with at least a collective-as-flow synthesizer, a runtime-adaptive collective library, a KV compression/streaming system, an endpoint-mobility serving system and a time-division transport.
4. Label these entries with their evidence tier (programme abstract read, or full text read).

### F2 — The regime taxonomy has three classes; the requirement names four (Requirement 5; major)

The page defines A wide-area LEO, B tight AI formation and C hybrid space–ground. Regime A merges three physically distinct cases: communication constellations, a global orbital compute mesh, and contact-limited Earth-observation fleets. Resulting labels conflict with the regime's own definition ("Long ISLs, limited optical degree"):

- CoOrbit carries "A · Wide-area LEO", while its own figure caption states that EO satellites lack inter-satellite links (`figures/coorbit.png`, panel b).
- OrbitalBrain, SpaceSched, Phoenix and CosMAC carry the same label, though their bottleneck is sparse ground contact.
- SpaceCore, SN² and LeoCC (communication service) share that label with SpaceMoE (global compute mesh).

**Fix:** split into four regimes — communication satellite constellation; global orbital compute mesh; compact formation fabric; EO-contact regime — plus the space–ground chain as a cross-cutting path. Relabel all 37 records and give each regime a parameter row (ISL presence, contact duty, bottleneck resource, representative papers).

### F3 — The spacecraft budget gives numbers for power and heat only (Requirement 5; moderate)

Mass appears as a symbolic ledger (`page-en.txt:642`) with zero worked values. Optical terminals appear qualitatively and as a degree sweep, with zero power, mass or aperture entries in the example.

**Fix:** add a worked mass row and a terminal row using sourced or explicitly assumed values:
- Radiator: 100 m² × 10 kg/m² = 1,000 kg under the Dark Clouds areal density.
- Array mass from a stated specific power.
- Terminal count × per-terminal power, with the 50 W transceiver assumption from Dark Clouds as one bundle and the Suncatcher 5 W / 10 cm telescope as another.
- Show the accelerator count after subtracting terminal power for degree 2 / 4 / 8.
- Correct the cross-reference at `page-en.txt:656` ("the other terms in B2") to point to the mass ledger.

### F4 — Evidence routes are generic; the inference from accepted papers lacks an explicit synthesis (Requirement 4; moderate)

The evaluation sections give a general evidence-layer table and two worked examples (Collaborative LLM, CommSAR). The per-paper evidence sits in the appendix, and the reader must derive the pattern.

**Fix:** add a matrix of the 11 SIGCOMM papers against evidence route (live service measurement, in-orbit asset, production deployment, hardware prototype, trace replay, container emulation, orbit simulation, analytical model) and calibration anchor. Then state counted inferences labelled as inference, for example:
- LeoCC and "Dissecting the StarLink" rely on live terminals plus replay.
- SpaceCore, SN² and TinyLEO rely on protocol hardware plus constellation replay or containers.
- SaTE, StarCDN and CoOrbit rely on trace-driven simulation with a solver or production-trace anchor.
- CommSAR and Planet-IoT include an operational space asset.

Follow with the reviewer-expectation statements each pattern supports.

### F5 — One aerial-adjacency candidate awaits adjudication (Requirement 1; moderate)

"Unveiling Low-Altitude 5G Performance: Linking Key Influencing Factors with UAV Flight Parameters" (`program-2026.txt:464-483`) concerns aerial terminals on commercial 5G. The 2026 row of the page shows zero adjacent entries, and the census search list in `investigation-a.md:17` omits UAV and low-altitude terms.

**Fix:** add an "adjudicated candidates" table to the audit section with this paper and a stated decision. My recommendation is "adjacent aerial access, listed with a one-paragraph note, outside the satellite count". The same table should record mechanism-adjacent terrestrial titles (Time-division TCP; "Cyclops: FSO-based Wireless Link for VR Headsets"; the reconfigurable-fabric papers), so the breadth of the scope decision is visible.

### F6 — Per-paper mathematics is a list of technique names (Requirement 3; moderate)

Every record has problem, design, model, evaluation, baselines, results, scope and an attributed figure, which satisfies the structure. The "Mathematical and graph model" field names methods (e.g. SaTE: "Path-based multi-commodity throughput maximization…") and stops short of the formulation.

**Fix:** for the 11 SIGCOMM papers plus OrbitalBrain, TACCL and TopoOpt, add one rendered equation or constraint set each, with the source equation number. Examples:
- SaTE path-flow objective and capacity constraint.
- TinyLEO equations 2–4.
- LeoCC estimator update.
- Planet-IoT lookahead flow-control objective.
- CosMAC transmission probability (Eq. 1).
- OrbitalBrain Equation 1.

### F7 — Beginner path leaves several terms undefined that the appendix then uses (Requirement 2; moderate)

"+Grid", "Walker", "TLE" and the 15-second Starlink reconfiguration interval occur only in appendix records (`page-en.txt:1550, 1050, 997, 962`). The tutorial's routing, handover and congestion-control paragraphs carry zero worked examples.

**Fix:** add to the foundations:
- Intra-plane and inter-plane ISLs, with a +Grid figure.
- Walker constellation notation.
- TLE and orbit propagation.
- The globally scheduled 15-second reassignment, with LeoCC, SATPIPE and "Dissecting the StarLink" as evidence.
- One numeric handover example and one snapshot-versus-temporal routing example on the existing A0–C2 time-expanded graph.
- Remove the duplicated MPC glossary row (`page-en.txt:66-68` and `:101-103`).

### F8 — Concept diagram and browser-evidence coverage (Requirement 7; moderate)

- **Workload diagram:** `rendered/chromium-en-1440-workloads.png` shows four identical "Sender → Receiver" rows, while the caption states the communication graphs are distinct. Redraw as a ring among n ranks (DP), a stage chain with a reverse arrow (PP), a dispatch/combine all-to-all (EP) and a one-shot state move (KV).
- **Screenshot coverage:** the 16 files cover English at 1440 px and Chinese at 375 px, for four regions only. Add English 375 px, Chinese 1440 px, one equation block, one wide table at 375 px, one original-figure card and one appendix record.
- **Mobile nav:** `chromium-zh-375-hero.png` shows a navigation item occluded beside the language toggle, and a single-character last line in the title.
- **Hypatia crop:** `figures/hypatia.png` clips the x-axis label at the bottom edge; re-crop with margin.
- **LeoCC figure:** `figures/leocc.png` is a low-resolution article-reader capture; replace with a higher-resolution crop.

### F9 — Identity and tier slips (Requirement 8; minor)

- Link text "Dark Clouds in Space" (`page-en.txt:655`; `index.html:535`) differs from the title "Dark Clouds Rising in Low-Earth Orbit: On Environmental Limits to Massive Orbital AI".
- "Space-XNet's SpaceMoE simulation" (`page-en.txt:652`): the string "Space-XNet" has zero occurrences in the local primary text `sources-b/spacemoe.txt`. Cite its origin or drop it.
- NINeS tier conflict: the page labels OrbitalBrain "Main conference", while `ADJUDICATION.md:21` lists it under "Workshop papers". The source header reads "1st New Ideas in Networked Systems (NINeS 2026)" with an OASIcs DOI. Use one label, e.g. "NINeS 2026 · inaugural conference (OASIcs)", in both places.
- Twelve corpus records (suncatcher through topoopt) omit the `evidence_status` key that the first 25 carry; align the schema.

### F10 — Chinese text (Requirement 7; minor)

- **Simplified characters in Traditional text**, seven places in `page-zh.txt`:
  - `:37` "觀测"
  - `:451` and `:1387` "試" written as "试"
  - `:709` "实际"
  - `:969` and `:1723` "结"
  - `:2208` "对"
- **Omitted sentence:** `page-zh.txt:794` drops the English sentence "Orbital hardware feasibility follows its own component ledger."
- **Mistranslation:** `page-zh.txt:728` renders "dated paper coverage" as "逐日文獻覆蓋範圍"; "具日期" matches the English.
- **Heavy English retention** in some lines (e.g. `:483`, `:38`) reduces beginner readability; translate the function words and keep only the technical nouns.

### F11 — Small numeric consistency items (Requirement 7; minor)

- `page-en.txt:569` gives a 500 km period "near 94.6 minutes". With the page's stated R_E = 6.371×10⁶ m the value is 94.5 minutes; 94.6 follows from the 6,378 km equatorial radius. Use one radius.
- B4 has worked numbers for DP and KV only. Add one numeric PP, EP and checkpoint example (e.g. 7×10⁹ parameters × 2 bytes = 14 GB of weights) and a TP expression.

---

## 4. Rubric

| # | Requirement | Score | Basis |
|---|---|---|---|
| 1 | SIGCOMM 2022–2026 census and appendix | 9.0 | 11 + Loon confirmed against five programmes; one aerial candidate awaiting adjudication (F5) |
| 2 | Beginner foundations | 8.5 | All six control problems and the terrestrial comparison present; undefined appendix terms and few worked examples (F7) |
| 3 | Per-paper depth | 8.5 | Complete structure, actual baselines, metric scope, attributed figures; mathematics at naming level (F6) |
| 4 | Evidence routes and reviewer expectations | 8.0 | Sound general ladder and confounder table; explicit accepted-paper synthesis absent (F4) |
| 5 | Orbital compute substrate | 8.0 | Correct power/thermal screening and accelerator counts; three-way taxonomy, symbolic mass, qualitative terminals (F2, F3) |
| 6 | LLM traffic, prior art, experiments, gates | 7.5 | Correct byte derivations, OrbitalBrain positioning, numeric gates; 2024–2026 same-venue prior art absent (F1) |
| 7 | Bilingual, figures, mathematics, browser evidence | 8.5 | Faithful narrative, correct arithmetic, machine checks pass; diagram, coverage and character slips (F8, F10, F11) |
| 8 | Source identity and scope honesty | 9.0 | Tiers and measured/simulated scopes handled carefully; four identity slips (F9) |
| | **Mean** | **8.4** | REVISE |

**Route to release:** F1 and F2 are the largest; resolving F1–F8 would place the artifact above 9.0 on this rubric. F9–F11 are quick corrections.

---

## 5. Evidence boundaries

- **Chinese appendix records** (`page-zh.txt` lines 841–1103 and 1164–2376) fall outside my direct line-by-line reading. I sampled them through the corpus fields and a Simplified-character scan.
- **Corpus:** only the first two records were read with full bilingual fields; the other 35 were checked for identity metadata, and their English content was read through the rendered page.
- **Programme abstracts:** read in full for the first half of 2022 and for the satellite sessions of 2025 and 2026. All other abstracts were covered by the two term scans over complete local snapshots, plus full title reading for 2022–2024.
- **Live programme pages:** each fetch returned a truncated view, so live corroboration covers only the opening sessions.
- **Figures and screenshots:** 5 of 37 figures and 5 of 16 screenshots viewed; the rest rest on the machine reports.
- **Primary-source verification:** the six papers spot-checked above; the remaining quantitative claims rest on the survey's stated source anchors.
- **SHA256** of the current `index.html` awaits computation by the lead.
- All actions in this review were read-only.