# Independent review R3 — "Satellite Networking for Orbital AI Centers"

**Score: 9.2 / 10 — Verdict: PASS**

All five R2 findings are closed, and the five new prior-art records match their primary texts on every number I checked. The census holds at 11 central papers, two aerial adjacencies and one optical-terminal ledger entry. Six text-level corrections remain; two touch factual consistency (R3-1, R3-2), and each is a wording change that leaves every technical conclusion intact.

**Reviewed file:** `site/ai-infra-basics/space-ai/index.html`

**SHA256:** `d9affd454e985a8ab9950f9b33f6e145445b01bcfd3341cfc758d1fcff1a9bca`, as computed by the lead and recorded in `evidence/snapshot-qa.json:2`. My toolset excludes hashing, so the hash rests on those two matching records. This PASS applies to that snapshot.

**Independence:** `prompt-r3.txt`, `response-r3.jsonl`, `stderr-r3.txt`, `QA.md`, `technical-review-r1/r2.md` and both code-review files stayed closed. All actions were read-only.

---

## 1. Yearly census (my inspection)

Evidence this round is the 393-title inventory plus an abstract-level term scan over the five complete local programme snapshots in `fable-review/official-current/`.

| Year | Satellite-centric main-track papers (source titles, quoted) | Adjacency |
|---|---|---|
| [2022](https://conferences.sigcomm.org/sigcomm/2022/program.html) | "A Case for Stateless Mobile Core Network Functions in Space" (`official-current-inventory.json:30`) | "SDN in the Stratosphere: Loon's Aerospace Mesh Network" (`:28`); "Cyclops: FSO-based Wireless Link for VR Headsets" (`:52`, terminal ledger) |
| [2023](https://conferences.sigcomm.org/sigcomm/2023/program.html) | Zero (zero term hits in `program-2023.html`) | Zero |
| [2024](https://conferences.sigcomm.org/sigcomm/2024/program/) | Zero (zero term hits in `program-2024.html`) | Zero |
| [2025](https://conferences.sigcomm.org/sigcomm/2025/program/papers-info/) | "LeoCC: Making Internet Congestion Control Robust to LEO Satellite Dynamics" (`:238`); "DeepSpace: Super Resolution Powered Efficient and Reliable Satellite Image Data Acquistion" (source spelling, `:249`); "SaTE: Low-Latency Traffic Engineering for Satellite Networks" (`:298`); "Small-scale LEO Satellite Networking for Global-scale Demands" (`:299`); "Direct-to-Cell Satellite Network without Satellite Navigation" (quoted title, `:300`); "StarCDN: Moving Content Delivery Networks to Space" (`:301`) | Zero |
| [2026](https://conferences.sigcomm.org/sigcomm/2026/program/papers/) | Session quoted as "Research Session 16: Satellite & Non-Terrestrial Networks" (`program-2026.html:1523`): "CommSAR: Enabling Bidirectional Communication in SAR Imaging Satellites via Shared Waveform" (`:418`); "Planet-Scale IoT Connectivity via LEO Satellites" (`:419`); "Dissecting the StarLink: Characterizing Queuing and Flow Dynamics in the Starlink Network" (`:420`); "Achieving Efficient Storage and Communication via Collaboration" (`:421`) | "Unveiling Low-Altitude 5G Performance: Linking Key Influencing Factors with UAV Flight Parameters" (`:346`) |

- **Totals:** 1 + 0 + 0 + 6 + 4 = 11 central papers, two aerial adjacencies, one terminal ledger entry. This matches `page-en-r3.txt:1645-1677` and `ADJUDICATION.md:11-17`.
- **2022 abstract hits:** confined to Loon, SpaceCore and Cyclops (`program-2022.html:1662-1842, 3443-3486`).
- **2025 and 2026 abstract hits:** confined to the listed papers, plus the LEO-NET workshop menu link.
- **Missing candidates:** zero found. Requirement 1 is satisfied.

---

## 2. Checks performed

**My inspection**
- **English text:** all 3,865 lines of `page-en-r3.txt`.
- **Chinese text:** lines 1–528, 711–1178, 1643–1742 and 3447–3621 of `page-zh-r3.txt`, read line by line. This covers every core section, the 22-row comparator table, the gap matrix, the projects, the audit ledger and the five new records.
- **Simplified-character scan:** a class of about 400 Simplified-only characters over the whole Chinese text and `paper-corpus.json` returned zero hits.
- **Corpus:** title, year, venue, `evidence_status` and `display_regime_en` for all 60 records. SIGCOMM holds 35; the venue table sums to 60 (`page-en-r3.txt:1185-1217`).
- **Arithmetic:** every worked number I recomputed is correct.
  - Spacecraft: 29.3976 kW usable, 40.83 kW peak, accelerator counts 34/34/34 and 34/33/31, 41.3 and 31.4 kW rejection, 2,200.3 kg.
  - New B2 thermal bounds: 51/50/49 at 300 K and 36/36/34 at 280 K.
  - Foundations: 95.5 and 94.5 min periods, 2.8 s temporal route, 8.612 s and 449.6 ms handover.
  - Workloads: 24.5 GB, 1.074 GB, 67.109 MB, 201.327 MB, 1.879 GB, 14 and 98 GB.
- **Math blocks:** 43 = 6 (A) + 8 (B) + 15 (P) + 14 source formulations, matching `snapshot-qa.json:8`.
- **Figures:** all five new figures viewed; each is legible and matches its caption.
- **Screenshots:** 8 of 64, covering English and Chinese at 375 and 1440 px, including the two R2 occlusion cases.
- **Live site:** the 2025 and 2026 fetches returned truncated views. They corroborate the UAV paper, LeoCC, DeepSpace and MixNet; the local snapshots carry the complete evidence.

**Primary-source spot checks for the five new records, all matching the page**

| Paper | Claims confirmed | Anchor |
|---|---|---|
| Harvest | DP recurrence and reconfiguration-count choice | `harvest.txt:369-383` |
| | 6.4×/4.7×/20× and 7.3×/10×/5.3× | `:546-547, 562-563` |
| | About 3× over a static ring; α = 30.32 µs, 85.11 Gbps | `:582, 587-588` |
| | Under 20 µs to 64 nodes, under 35 µs to 1024 | `:641-642` |
| | BlueField-3 step emulation with a fixed added switch penalty | `:506-517` |
| Opus | Exposed-delay expression | `opus.txt:413` |
| | Polatis and L40 testbed; 200 ms optics, about 6 s and 3 s link-up | `:485-487, 513-525` |
| | 6.13 % to 0.79 %; 1.01×/1.02× with provisioning | `:574, 591-593` |
| | 5.31 %, 2.49 %, 11.22 %; 22.5 % at 88.9 % EP traffic | `:649-655, 710-712` |
| | 23.9×/15.4× power and 4.3×/3.2× cost | `:720-723` |
| MixNet | 1.2–1.5× and 1.9–2.3×; 2.5× over TopoOpt | `mixnet.txt:38, 92, 95` |
| | 128 H800; 25 ms setup | `:267, 671` |
| | 41.44–46.75 ms OCS; 5.67 s and 6.33 s NIC reactivation | `:1395, 1427` |
| GeoOrchestra | Check-and-Commit; gateway commit ACK with byte-range restart or reroute | `geoorchestra-reader.txt:4239, 4400-4421` |
| | 2000 km WAN; 12 % and 18 % prediction error | `:4585, 4802, 4857` |
| | 32 % physical; 1.63× and 1.8× simulated; 5 % simulator error | `:4977, 5000, 5015-5040` |
| PReCCL | NCCL v2.29; 0.11 %/0.97 % overhead | `preccl-reader.txt:3393, 3528` |
| | 1.19×/1.21×/1.18×; 5.5 %/22.1 % | `:3660-3664, 3814-3817` |
| | Five round-trips, 78.0 % retained | `:4430` |
| | 146 jobs, 5.7 %/51.2 %, 21.4 % | `:4485-4497` |
| | Immutable allocations, auxiliary socket, observational label | `:7082, 7200, 7831` |

**Machine evidence (read; verified only as far as the items above)**
- `responsive-qa.json`: 16 cells pass, 43 of 43 math blocks painted, 60 images, `navControlsOverlap` false in all 16 cells.
- `figure-qa.json`: pass.
- `lexical-qa.json`: zero Simplified matches.
- `fable-r3-c/audit.md`: its Appendix A reconciliation arithmetic is correct (0.96875⁵ = 0.8532).

**R2 closure**

| R2 finding | Status | Evidence |
|---|---|---|
| R2-1 prior art | Closed | Five full records with formulas, baselines and figures; 22-row table; gap matrix and ranked designs name them; hypothesis renamed; Harvest cited at the setup fraction (`page-en-r3.txt:490-524, 1034-1037, 1101, 1111, 1125, 1133`) |
| R2-2 Simplified characters | Closed | Zero hits in page text and corpus |
| R2-3 labels and anchors | Closed | "D or B" (`:962`); single name for population B (`:167, 203, 1399`); X/X/T badges (`:1280, 1595, 1602`); corpus display fields; TinyLEO §4.1 (`:1790, 1801`); 5 W transmitted output (`:926`); terminal heat term (`:877-878, 930`) |
| R2-4 localization and captures | Closed | Chinese field labels; spacing fixed (`page-zh-r3.txt:268`); both R2 captures now clear of the navigation bar |
| R2-5 reviewer expectations | Closed | Three labelled inference paragraphs (`page-en-r3.txt:834-836`) |

---

## 3. Required findings and concrete fixes

### R3-1 — Adjacency ledger carries stale comparator counts (Requirements 1, 8; minor, factual)

The page gives two different comparator totals:
- `page-en-r3.txt:365` and `:1669` say 22 works (21 AI/fabric plus Cyclops).
- `:1699` says "17-work comparator table".
- `:1705` says "16 AI/fabric identities; together with Cyclops, 17", and the list at `:1703` omits Harvest, Opus, MixNet, GeoOrchestra and PReCCL.

The same strings sit in `page-zh-r3.txt:1699, 1703, 1705` and `index.html:539`.

**Fix:** change to 22-work, 21 identities and 22 records in both languages, and append the five names to the list.

### R3-2 — Opus measured version is absent from visible text (Requirement 8; minor)

- The corpus records the reviewed text as "arXiv 2602.12521v3, 2026-07-03" (`paper-corpus.json:3489`).
- The rendered record shows only "Full primary PDF: … audited" under a Main conference badge (`page-en-r3.txt:3485`).
- The arXiv identifier appears in `index.html` only inside a script alias (`:645`).
- KVServe, DualPath, UBEP and Trivance all state their measured version in visible text (`:411, 446, 453, 474`).
- The five new comparator rows also omit the source version under a column headed "Evidence and source version" (`:495-523`).

**Fix:** add the `source_version` phrase to the Opus status line and to the five new comparator rows: Harvest author-hosted ACM-format PDF, Opus arXiv v3 with DOI verified, MixNet author-hosted conference PDF, GeoOrchestra and PReCCL official reader.

### R3-3 — English wording defects (Requirements 3, 6, 7; minor)

- `:1124` reads "expiry-aware progress commit lower p95"; use "lowers".
- `:3503` reads "5.31% over EPS", which can read as a gain. The source says Opus is 5.31 % slower than EPS (`opus.txt:650`); the Chinese text already says overhead. Use "slower than EPS".
- `:2991` reads "report reported" and "reports reported" (also `paper-corpus.json:2083`).
- Numerals are fused to words in many records, for example "uses128 H800 GPUs and128", "has48 GPUs:24 H20-141GB and24", "rates105Kbps", "routinely20+ balloons over3000+km" (`:509, 516, 675, 1285`; corpus `:3558, 3654, 324, 418`). Restore the spaces with a regex pass over the English fields.

### R3-4 — Duplicated paragraph (Requirement 6; minor)

The "five optical/WAN additions" paragraph appears verbatim at `:1116` and `:1176`, in both languages. Keep it in the gap section and replace the second copy with a one-sentence pointer.

### R3-5 — Chinese localization residue (Requirement 7; minor)

- 27 evidence-status lines stay in English in Chinese mode (for example `page-zh-r3.txt:3451, 3519, 3587`), beside 33 that read "完整 primary text 已審閱".
- The T badge has two names: "T · 地面比較基準" (`:358`) and "T · 地面參照" (`:3449`).
- A stray space follows the full stop at `:878, 930, 1125, 1133, 1145, 1175, 3607`.
- `:1154` uses "交換 schedule" for schedule swapping; `:395` uses "切換", which matches the source meaning.

### R3-6 — Corpus schema consistency (Requirement 8; minor)

`year` mixes integers and strings, and SIGCOMM 2026 appears as both `2026` and `"2026-08"`. Normalize to one string format.

**Optional polish:** in the population-B diagram the label "Short optical links" sits across the middle vertical link (`webkit-en-1440-regime-b.png`).

These corrections change wording and metadata only. A diff check plus a rerun of the lexical and responsive gates is adequate verification for them.

---

## 4. Rubric

| # | Requirement | Score | Basis |
|---|---|---|---|
| 1 | SIGCOMM census and appendix | 9.4 | 11 central, two aerial and Cyclops verified at title and abstract level; stale ledger counts |
| 2 | Beginner foundations | 9.2 | +Grid, Walker, TLE/SGP4, worked routing and handover examples, glossary |
| 3 | Per-paper depth | 9.2 | 60 complete records, 43 math blocks, five new records verified; English wording defects |
| 4 | Evidence routes and reviewer expectations | 9.2 | 11-row matrix, counted inference, three labelled patterns |
| 5 | Orbital compute substrate | 9.3 | Four populations plus path layer; mass, terminal and heat sweeps all recompute |
| 6 | LLM traffic, prior art, experiments, gates | 9.3 | 22 comparators, residual narrowed to exogenous expiry and resource coupling, named baselines, numeric gates; duplicate paragraph |
| 7 | Bilingual, figures, mathematics, browser evidence | 9.1 | Zero Simplified characters, localized labels, clean captures; English status lines in Chinese mode |
| 8 | Source identity and scope honesty | 9.0 | Tiers and measured/simulated scopes handled carefully across 60 records; Opus version disclosure gap |
| | **Mean** | **9.2** | PASS |

---

## 5. Evidence boundaries

- **Hash:** established by the lead's computation and `snapshot-qa.json`; I had only read access.
- **Chinese text:** lines 529–710, 1179–1642, 1743–3446 and 3622–3865 were covered by the Simplified scan and by the English reading of the same records, rather than line by line.
- **Corpus:** identity and display fields for all 60 records; record bodies were read through the rendered English text.
- **Programmes:** abstracts were covered by term scans over complete snapshots, with every matched region read. The live fetches were truncated and corroborate a subset.
- **Primary sources this round:** the five new papers at the anchors in Section 2. The eight papers checked in R2 carry over; other quantitative claims rest on the survey's stated anchors.
- **Figures and screenshots:** 5 of 60 figures and 8 of 64 screenshots viewed this round; the remainder rests on the machine reports.
- **Formula gate metadata:** `fable-r3-a/katex-qa.json` and the `qa.json` files stayed closed. Formula correctness rests on my reading of the rendered blocks and on the Harvest and Opus source checks.