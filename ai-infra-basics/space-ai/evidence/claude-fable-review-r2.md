# Independent review R2 — "Satellite Networking for Orbital AI Centers"

**Score: 8.9 / 10 — Verdict: REVISE**

The census is correct and nine of my eleven R1 findings are closed. Two gaps hold the artifact just below the 9.0 release bar:
- The closest same-venue prior art on optical reconfiguration for AI collectives is absent from the page.
- Three Simplified-character strings reported as fixed are still present, plus one new one.

**Reviewed file:** `site/ai-infra-basics/space-ai/index.html`

**SHA256:** `e4e6ff9a476dfee275a284e99d026feca9dc2be9c527d34a67757ad79d6b4654`, as computed by the lead and recorded in `evidence/snapshot-qa.json:2`. My toolset excludes hashing, so the hash rests on those two records.

**Independence:** `response-r2.jsonl`, `prompt-r2.txt`, `QA.md`, `technical-review-r1/r2.md` and `code-review.md` stayed unopened. All actions were read-only.

---

## 1. Yearly census (my inspection)

I read all 393 title entries in `official-current-inventory.json` and ran an abstract-level term scan over the complete local programme snapshots for all five years. The scan covered satellite, orbit, LEO, Starlink, aerospace, balloon, UAV, drone, aerial, NTN, GNSS, FSO, HAPS and related terms.

| Year | Satellite-centric main-track papers (source titles, quoted) | Adjacency |
|---|---|---|
| [2022](https://conferences.sigcomm.org/sigcomm/2022/program.html) | "A Case for Stateless Mobile Core Network Functions in Space" (`sources-a/program-2022.txt:747`) | "SDN in the Stratosphere: Loon's Aerospace Mesh Network" (`:686`); "Cyclops: FSO-based Wireless Link for VR Headsets" (`:1377`, terminal ledger) |
| [2023](https://conferences.sigcomm.org/sigcomm/2023/program.html) | Zero (73 titles, zero term matches in abstracts) | Zero |
| [2024](https://conferences.sigcomm.org/sigcomm/2024/program/) | Zero (62 titles, zero term matches in abstracts) | Zero |
| [2025](https://conferences.sigcomm.org/sigcomm/2025/program/papers-info/) | "LeoCC: Making Internet Congestion Control Robust to LEO Satellite Dynamics" (`program-2025.txt:64`); "DeepSpace: Super Resolution Powered Efficient and Reliable Satellite Image Data Acquistion" (source spelling, `:119`); "SaTE: Low-Latency Traffic Engineering for Satellite Networks" (`:352`); "Small-scale LEO Satellite Networking for Global-scale Demands" (`:357`); "Direct-to-Cell Satellite Network without Satellite Navigation" (`:361`); "StarCDN: Moving Content Delivery Networks to Space" (`:365`) | Zero |
| [2026](https://conferences.sigcomm.org/sigcomm/2026/program/papers/) | Session quoted as "Research Session 16: Satellite & Non-Terrestrial Networks" (`program-2026.txt:1984`): "CommSAR: Enabling Bidirectional Communication in SAR Imaging Satellites via Shared Waveform"; "Planet-Scale IoT Connectivity via LEO Satellites" (`:2010`); "Dissecting the StarLink: Characterizing Queuing and Flow Dynamics in the Starlink Network" (`:2027`); "Achieving Efficient Storage and Communication via Collaboration" (`:2045`) | "Unveiling Low-Altitude 5G Performance: Linking Key Influencing Factors with UAV Flight Parameters" (`:465`) |

Totals are 1 + 0 + 0 + 6 + 4 = 11 central papers, two aerial adjacencies and one optical-terminal ledger entry. This matches the page audit (`page-en-r2.txt:1563-1625`) and `ADJUDICATION.md:11-17`.

Other candidates were cleared by reading their abstracts:
- The 2025 "Global IoT" paper is terrestrial LoRaWAN (`program-2025.txt:388`).
- The 2025 "drone" match is underwater (`:394`).
- The 2022 "GPS" match is a port-scanning system (`program-2022.txt:1214`).

Requirement 1 is satisfied; I found zero missing satellite candidates.

---

## 2. Checks performed

**My inspection**
- **English text:** all 3,595 lines of `page-en-r2.txt`.
- **Chinese text:** lines 1–493, 676–1134 and 1563–1662 of `page-zh-r2.txt`, plus two Simplified-character scans over the whole file.
- **Corpus:** identity fields for all 55 records; 55 `regime` and 55 `evidence_status` keys are present.
- **Arithmetic:** every worked number I recomputed is correct.
  - Spacecraft: 40.83 kW peak, 408.3 kg array, 2,200.3 kg total, accelerator counts 34/34/34 and 34/33/31, 41.3 and 31.4 kW rejection.
  - Foundations: 94.5 min period at 500 km, 2.8 s temporal route, 8.612 s and 449.6 ms handover.
  - Workloads: 67.109 MB, 201.327 MB, 1.879 GB, 14 and 98 GB, 1.074 GB.
  - CommSAR: 105.1 kbps.
- **Screenshots:** 9 of 64, covering English and Chinese at 375 and 1440 px.
- **Figures:** 4 of 55 (LeoCC, Hypatia, UAV, Theseus).
- **Live site:** the 2025 and 2026 fetches returned truncated views. They corroborate LeoCC, DeepSpace and the UAV paper in Research Session 4; the local snapshots carry the complete evidence.

**Primary-source spot checks, all matching the page**
- HyNA: 7.35×, 84.5 Gbps, 2.9 %, 14 % (`hyna-compact.txt:1735,1324,1896`).
- UBEP: 52.4 %, 11.1 %, 256 NPU dies, inference scope (`ubep.txt:31-32,108`).
- Connex: 85 % and epoch routing (`connex.txt:50,142`).
- Janus: 16× and 2.06× (`janus.txt:132`).
- Theseus: 1.73× and 1.07×.
- TinyLEO Equations 2–4 (`tinyleo.txt:363-365`).
- CommSAR Equation 9 (`commsar.txt:374-375`).
- OrbitalBrain Equation 1 (`orbitalbrain.txt:407-416`).

**Machine evidence (read, unverified beyond the items above)**
- `responsive-qa.json`: 16 cells pass, 38 of 38 math blocks painted, 55 images.
- `figure-qa.json`: 55 figures pass.
- `lexical-qa.json`: pass.
- `fable-formulas/audit.md` and `fable-prior-art/audit.md`.

**R1 closure**

| R1 finding | Status |
|---|---|
| F2–F9, F11 | Closed |
| F1 | Partially closed: 17 works added, closest optical group absent (R2-1) |
| F10 | Partially closed: three flagged strings persist (R2-2) |

---

## 3. Required findings and concrete fixes

### R2-1 — The closest optical-reconfiguration prior art for Projects 1 and 3 is absent (Requirement 6; major)

A search of the page for Harvest, Opus, MixNet, GeoOrchestra and PReCCL returns zero matches. All five are in the audited programmes:

- **"Harvest: Adaptive Photonic Switching Schedules for Collective Communication in Scale-up Domains"** (SIGCOMM 2026, `program-2026.txt:2153-2172`). It synthesizes reconfiguration schedules that minimize collective completion time, balancing reconfiguration delay against congestion and propagation.
- **"Opus: Photonic Rail-Optimized Fabric in ML Datacenters"** (SIGCOMM 2026, `:1293-1312`). It reconfigures circuits in-job at parallelism phase boundaries on a physical OCS testbed.
- **"MixNet: A Runtime Reconfigurable Optical-Electrical Fabric for Distributed Mixture-of-Experts Training"** (SIGCOMM 2025, `program-2025.txt:257-260`). It performs in-training topology reconfiguration for MoE on 32 A100 GPUs.
- **Secondary:** "GeoOrchestra" (`program-2026.txt:1516`), wide-area training with time-slot slicing; "PReCCL" (`:560`), epoch-based reallocation at collective boundaries.

These overlap the page's own mechanism text:
- `page-en-r2.txt:995` proposes reserving optical circuits for an upcoming collective under setup time τ.
- The Project 1 hypothesis (`:1081`) is worded "phase-aware reservations", which is Opus's established contribution.
- Project 3 (`:1071`) couples expert placement to terminal reservation, which MixNet addresses terrestrially.

The gap matrix (`:1052`) says it names the strongest adjacent mechanisms, so this omission affects the novelty argument a SIGCOMM reviewer would test first. R1 named only the 2024 reconfigurable-fabric papers; these three surfaced in this round's full title reading.

**Fix:**
1. Add full records and comparison-table rows for Harvest, Opus and MixNet; add GeoOrchestra and PReCCL with their evidence tier labelled.
2. Gap matrix: add Harvest and Opus to Project 1 and MixNet to Project 3. Restate the residual as exogenous, forecast-bounded contact expiry plus progress commit, since terrestrial controllers choose their own reconfiguration instants.
3. Ranked designs: add Harvest with τ set to measured PAT/setup, and Opus-style phase-boundary reconfiguration, as Project 1 baselines. Add MixNet as the Project 3 fabric baseline. Rename the hypothesis, for example to "expiry-aware progress commit".
4. Cite Harvest at the setup-fraction paragraph (`:995`).
5. Update the counts: SIGCOMM tier 30, corpus 55, comparator table 17, hero tile, `ADJUDICATION.md` and `snapshot-qa.json`.

### R2-2 — Simplified characters persist in the Traditional text (Requirement 7; moderate)

The repair mapping reports F10 as fixed. Three R1-flagged strings are still present and a new one arrived with the prior-art table:

| Quoted string | Rendered text | `index.html` | `paper-corpus.json` |
|---|---|---|---|
| "測试" | `page-zh-r2.txt:640,1928` | `:535,551` | `:313` |
| "结合 ASN" | `:1302,2304` | `:539,569` | `:823` |
| "相对 Switch" | `:2809` | `:599` | `:1804` |
| "独立 dense" (new) | `:481` | `:525` | — |

**Fix:** correct to 測試, 結合, 相對 and 獨立 in both files. Add a Simplified-character scan to the lexical gate, since the current gate passed with these present.

### R2-3 — Label and anchor consistency (Requirements 3, 5, 8; minor)

- **Stale regime code:** `page-en-r2.txt:924` says coarse PP stages "may fit A or B". Under the four-population taxonomy the distributed mesh is D.
- **Three names for population B:** "Compact formation fabric" (`:167`), "Local AI fabric" (`:203`), "Tight AI formation" (`:1354`). Choose one.
- **Adjacency badges:** Loon shows "Adjacent · Stratospheric network" (`:1235`), UAV shows "X · Aerial adjacency" (`:1550`), and Cyclops shows "T · Terrestrial reference" (`:1557`) while the ledger calls it terminal adjacency (`:1618`).
- **Corpus versus page:** ten records carry a single-population `regime` in the corpus while the page shows a composite badge (starcdn, deepspace, planet-iot, serval, coorbit, cosmac, mobility-measurement, cost-network, dark-clouds, loon). Add a display field to the corpus or align the labels.
- **TinyLEO anchor:** the record says "§3 equations 2–4" (`:1721`); the equations sit in §4.1 (`tinyleo.txt:289,363`), as the P5 anchor states (`:1710`).
- **Terminal wording:** `:891` says "5 W optical input"; Suncatcher's P_T is transmitted optical output.
- **Terminal heat:** add terminal draw to the B2 heat term. Under the 250 W stress case at q=8, the thermal bound moves from 51 to 49 at 300 K and from 37 to 34 at 280 K; the electrical bound of 31 stays binding.

### R2-4 — Chinese localization and capture quality (Requirement 7; minor)

- The field labels "Problem formulation", "Evaluation methodology", "Baselines" and "Built for" stay in English in Chinese mode (`page-zh-r2.txt:1636,1647,1649,367`) beside translated sibling labels.
- `page-zh-r2.txt:268` has "分布或uncertainty範圍" with the spacing dropped.
- `webkit-zh-1440-appendix.png` and `webkit-en-375-wide-table.png` show the sticky navigation painted across content mid-capture. Hide the navigation during element captures and add an occlusion check.

### R2-5 — Reviewer-expectation synthesis is one sentence (Requirement 4; minor)

The eleven-row matrix and the counted inference (2 live, 2 spacecraft asset, 7 scalable models) are sound (`page-en-r2.txt:761-798`). Add one expectation line per pattern, each labelled as inference:
- Live-service claims pair with controlled replay.
- Asset claims carry per-direction scope.
- Model-scale claims carry a hardware or solver anchor.

---

## 4. Rubric

| # | Requirement | Score | Basis |
|---|---|---|---|
| 1 | SIGCOMM census and appendix | 9.5 | 11 central, two aerial and Cyclops ledger verified at title and abstract level |
| 2 | Beginner foundations | 9.1 | +Grid, Walker, TLE/SGP4, 15-second cadence, worked routing and handover examples; stale regime code |
| 3 | Per-paper depth | 9.1 | 55 complete records, 15 source formulations plus 9 baseline formulas; TinyLEO anchor slip |
| 4 | Evidence routes and reviewer expectations | 9.0 | Matrix and counted inference present; expectation text brief |
| 5 | Orbital compute substrate | 9.0 | Four populations plus path layer, worked mass and terminal sweeps; naming and heat-term items |
| 6 | LLM traffic, prior art, experiments, gates | 8.2 | Correct byte derivations, 17 comparators, numeric gates; Harvest, Opus and MixNet absent |
| 7 | Bilingual, figures, mathematics, browser evidence | 8.4 | Faithful narrative, correct mathematics, repaired figures; Simplified characters and mixed labels |
| 8 | Source identity and scope honesty | 9.2 | Versions, tiers and measured/simulated scopes handled carefully; corpus/badge mismatch |
| | **Mean** | **8.9** | REVISE |

**Route to release:** closing R2-1 and R2-2 lifts Requirements 6 and 7 above 9.0. R2-3 to R2-5 are quick corrections.

---

## 5. Evidence boundaries

- **Chinese text:** lines 494–675 and 1663–3595 of `page-zh-r2.txt` were covered by the Simplified-character scans, one appendix screenshot and the English reading of the same records, rather than line-by-line reading.
- **Corpus:** I read identity fields only; record bodies were read through the rendered English text.
- **Programmes:** abstracts were covered by term scans over complete snapshots, with targeted reading of every matched region and of the five prior-art abstracts in R2-1. The other abstracts were left unread.
- **Live pages:** the fetches were truncated, so live corroboration covers the opening sessions only.
- **Screenshots and figures:** 9 of 64 and 4 of 55 viewed; the remainder rests on the machine reports.
- **Primary sources:** the eight papers listed in Section 2; other quantitative claims rest on the survey's stated anchors.
- **R2-1 papers:** my evidence is their programme abstracts. Their full texts are still to be acquired and audited by the lead.