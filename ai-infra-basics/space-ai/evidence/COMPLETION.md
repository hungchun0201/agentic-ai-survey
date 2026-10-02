# Research survey completion audit / 研究報告完成核對

Census date: 2026-10-02. Accepted artifact: [bilingual orbital AI networking survey](../index.html). [Review provenance](claude-fable-provenance.json) identifies the actual Claude Fable runtime, reviewed snapshots and acceptance scores.

## Question and thesis / 問題與主張

The survey builds satellite-network foundations, derives orbital compute budgets and identifies falsifiable LLM networking experiments for SIGCOMM. Its thesis treats forecast-bounded contact expiry, application progress and coupled terminal/memory/energy resources as candidate additions to established satellite and terrestrial AI mechanisms. Each proposed experiment equips named baselines with the same forecasts, usable capacity and recovery service, then measures application outcomes and correctness.

本報告建立衛星網路基礎、推導軌道運算資源預算，並提出面向 SIGCOMM 的 LLM networking 實驗。候選主張聚焦 forecast-bounded contact expiry、application progress 與 terminal／memory／energy coupling；具名 baseline 取得相同 forecast、可用容量與 recovery service，實驗量測 application outcome 與 correctness。

## Requirement mapping / 需求對照

| Requested scope | Delivered evidence |
|---|---|
| Beginner satellite networking | Orbital periods, Walker constellation notation, TLE/SGP4, +Grid links, temporal routing, TE, handover, congestion control and resource allocation; worked examples and glossary |
| Recent networking papers | 60 full-primary analyses across satellite systems, orbital AI proposals, aerospace adjacency and terrestrial AI/optical comparators; explicit venue and source tiers |
| SIGCOMM 2022–2026 census | Five official programme inventories and abstract-level scans; eleven satellite-centric main papers, annual counts 1/0/0/6/4; two aerial adjacencies and a terminal-comparator ledger |
| Individual paper analysis | Problem, formulation, algorithm, mathematics, evaluation, named baselines, results and scope; structured extraction for all 60 identities |
| Constellation-limited evaluation | Measurement, calibrated simulation, trace replay, hardware emulation and solver-scale analysis; eleven-paper evidence matrix and labelled reviewer-methodology inferences |
| Original and teaching figures | 60 attributed original-paper figures; 15 conceptual frames with 18 SVG panels; full-resolution assets and figure provenance |
| Physical compute constraints | Accelerator count, electrical power, sunlight, batteries, radiator, thermal rejection, mass and optical terminal setup; four satellite populations and a crosscutting space–ground path |
| LLM training and inference | DP/TP/PP/EP/KV traffic models, byte arithmetic, collective/circuit prior art and a gap matrix; three projects with baselines, implementation contracts and continuation criteria |
| Mathematical tools | Temporal graphs, optimization, LP/MILP, heuristics, queueing, Markov models, learning methods and 43 source-anchored or explicitly derived equation blocks |
| Quality acceptance | Actual Claude Fable revisions, final PASS ≥9/10, independent code review, source adjudication, 60-figure gate, 16 browser cells and lexical scan |
| Personal survey integration | English and Chinese topic-survey cards link to the same bilingual page; GitHub Pages deployment publishes page, figures and extraction records |

## Evidence scope / 證據範圍

The exhaustive census applies to satellite-centric SIGCOMM main-track papers from 2022 through 2026 under the stated application and aerospace-adjacency criteria. NSDI, MobiCom, CoNEXT, IMC and INFOCOM contribute curated mechanism coverage. The 22 current terrestrial comparator additions comprise 21 AI/fabric identities and Cyclops; TACCL and TopoOpt supply two additional foundational references. Programme-level BIER-DC and metadata-level SECO carry their source-status labels.

完整普查範圍為 2022 至 2026 年 SIGCOMM 衛星主會議論文，並明列空中相鄰系統與光學終端參照。其餘五個會議提供代表性機制分析。新增比較工作共 22 篇，涵蓋 21 篇 AI／fabric 工作與 Cyclops；TACCL、TopoOpt 另提供兩篇基礎參照。BIER-DC 與 SECO 採其對應的 programme／metadata 證據層級。

[Acceptance record](QA.md), [adjudication](ADJUDICATION.md), [structured corpus](paper-corpus.json), [responsive checks](responsive-qa.json), [figure checks](figure-qa.json) and [lexical checks](lexical-qa.json) provide the reproducible delivery evidence. Final source identity uses the accepted page SHA-256 in the provenance record; production verification checks that hash, image bytes, homepage cards and the generated extraction index.

## Addendum: the opening derives from the record / 增補：以紀錄推導開頭（2026-10-02）

The accepted artifact opened with an abstract statement of its thesis and named one paper. The
opening now reads the publication record first and derives the thesis and the available research
openings from it. Three things were added.

A title-level screen of five SIGCOMM programme years, recorded in
[program-screen.json](program-screen.json) with its classification rule and per-title labels. It
measures the venue rather than the corpus: titles listed per year are 57, 73, 62, 88 and 109; titles
whose subject is a network built for a machine-learning workload are 1, 3, 7, 15 and 29; titles
whose subject is a satellite substrate are 1, 0, 0, 6 and 4. The screen also measures the corpus's
own coverage of the venue, which is twelve of the twenty-nine AI-infrastructure titles from 2026.

A new section, `#venue-record`, that reads both tracks, states what each already settles and what
physical assumption each rests on, examines where the two meet and where they do not, lists what the
reviewed corpus leaves out, and derives five research openings with a discriminating experiment for
each. Three of the five map onto the falsifiable designs the page already carried.

A source record, [venue-record-sources.json](venue-record-sources.json), holding every identity the
section names that the corpus does not carry, each with the official page or DOI that confirms it
and the tier it enters at.

已驗收的成品以抽象的論點陳述開頭，並且只點名一篇論文。現在的開頭先閱讀出版紀錄，再由紀錄推導論點與
可進行的研究方向。新增三項內容：其一，對五個 SIGCOMM 年度的題名層級篩查，連同分類規則與逐篇標記記錄於
[program-screen.json](program-screen.json)；它量測的是會議而非 corpus：各年度列出的題名為 57、73、62、
88、109，主題為「為機器學習工作負載而建的網路」者為 1、3、7、15、29，主題為衛星載體者為 1、0、0、6、4，
並量出 corpus 對 2026 年二十九個 AI 基礎設施題名的覆蓋為十二個。其二，新章節 `#venue-record`，
閱讀兩條軌跡、陳述各自已解決的問題與所依賴的物理假設、檢視交會與未交會之處、列出已審閱 corpus 漏掉的部分，
並推導五個研究開口與各自的判定性實驗，其中三個對應頁面既有的可否證設計。其三，來源紀錄
[venue-record-sources.json](venue-record-sources.json)，收錄本節指名而 corpus 未收錄的每一筆身分、
佐證頁面或 DOI，以及其進入的證據層級。
