# Evidence adjudication / 證據判讀紀錄

Audit date: 2026-10-02. Scope: satellite networking foundations, orbital AI substrate and LLM communication research opportunities. 證據範圍涵蓋衛星網路基礎、軌道 AI 系統與 LLM 通訊研究機會。

## Coverage / 收錄範圍

The full-primary corpus contains 60 papers. The scoped SIGCOMM main-track census covers 2022–2026 and counts 1, 0, 0, 6 and 4 satellite-centric papers, respectively. The eleven papers use satellite service, spacecraft networking or orbital links as a central problem, design or evaluation substrate. Loon and the low-altitude 5G measurement study appear as explicitly scoped aerial adjacencies. Twenty-two additional current terrestrial AI/optical references strengthen the matched-resource baseline map. NSDI, MobiCom, CoNEXT, IMC and INFOCOM coverage provides a curated mechanism map. Older Hypatia, Motifs and StarPerf establish simulation and topology foundations. TACCL and TopoOpt supply terrestrial AI-fabric comparators.

60 篇納入全文證據庫。SIGCOMM 2022–2026 主會議依年度收錄 1、0、0、6、4 篇以衛星服務、太空網路或軌道鏈路為核心的論文。Loon 與 low-altitude 5G measurement study 另列空中相鄰系統，另補二十二篇近期地面 AI／光學參照以強化 matched-resource baselines。其他會議採代表性機制整理；Hypatia、Motifs、StarPerf 建立工具與拓樸背景，TACCL、TopoOpt 提供地面 AI 網路對照。

| Year | Satellite-centric main papers | Adjacent substrate | Official program |
|---|---|---|---|
| 2022 | SpaceCore | Loon | [SIGCOMM 2022](https://conferences.sigcomm.org/sigcomm/2022/program.html) |
| 2023 | 0 | — | [SIGCOMM 2023](https://conferences.sigcomm.org/sigcomm/2023/program.html) |
| 2024 | 0 | — | [SIGCOMM 2024](https://conferences.sigcomm.org/sigcomm/2024/program/) |
| 2025 | LeoCC, DeepSpace, SaTE, TinyLEO, SN², StarCDN | — | [SIGCOMM 2025](https://conferences.sigcomm.org/sigcomm/2025/program/papers-info/) |
| 2026 | CommSAR, Planet-Scale IoT, Dissecting StarLink, CoOrbit | Low-altitude 5G study | [SIGCOMM 2026](https://conferences.sigcomm.org/sigcomm/2026/program/papers/) |

## Identity and evidence tiers / 身分與證據層級

BIER-DC receives a programme-only pointer from the [ICNP 2026 programme](https://icnp26.cs.ucr.edu/program.html). Its technical mechanism and evaluation remain full-text review tasks. SECO receives publisher-metadata coverage in the research audit; the candidate author arXiv pointer resolves to FlocOff. The 60-paper detailed corpus uses verified full primary text. Workshop papers carry their workshop venue explicitly: connectivity and Dark Clouds at LEO-NET 2026. OrbitalBrain appears at the inaugural NINeS 2026 conference in OASIcs. Making Sense carries CoNEXT Companion 2023.

BIER-DC 以 ICNP 2026 programme 確認題名與會議身分，技術內容待全文審查。SECO 已確認 publisher metadata；候選 author arXiv 指向 FlocOff。60 篇詳細分析採已取得的原始全文。LEO-NET 屬 workshop；NINeS 2026 為 OASIcs 首屆主會議；CoNEXT Companion 保留其正式層級。

## Quantitative interpretations / 量化解讀

### suncatcher

The 800 Gbps one-way optical bench result and 1.6 Tbps bidirectional sum describe the measured link. The 24 × 400 Gbps DWDM design yields 9.6 Tbps. The 81-satellite, 1 km-radius formation is an engineering analysis at 650 km. Per-spacecraft accelerator count, radiator sizing and production fabric require additional parameters. [Primary source](https://arxiv.org/abs/2511.19468)

800 Gbps 單向與 1.6 Tbps 雙向合計屬量測；24 × 400 Gbps 的 9.6 Tbps 屬設計估計；81 顆、1 km 半徑與 650 km 高度屬 formation analysis。

### spacemoe

SpaceMoE is the current v2 identity of arXiv 2605.00515. Its 1,056-node, 200-snapshot experiment uses model-derived routing and compute latency. The reported per-token latency belongs to the stated CPU-effective throughput and assumed ISL capacity. Queuing, accelerator kernels and service tails require calibrated measurements. [Primary source](https://arxiv.org/abs/2605.00515)

SpaceMoE 採 v2 題名；1,056 nodes 與 200 snapshots 的結果依賴 CPU-effective throughput 與 ISL 假設，後續實驗需補 queue、GPU kernel 與服務尾端量測。

### collaborative-llm

The extended WCSP work evaluates ViT image classification, EuroSAT and RESISC45, using four Jetson AGX Orin devices and a ground RTX 4070 Ti. Its model partition and activation-compression method motivates LLM hypotheses; its measured task is image classification. The reported maximum delay gain is 42% and communication saving about 71% under the tested task constraints. [Primary source](https://arxiv.org/abs/2604.04654)

WCSP extended version 以 ViT、EuroSAT、RESISC45、四部 Jetson AGX Orin 與地面 4070 Ti 評估；partition 與 activation compression 可啟發 LLM 設計，原始實驗工作負載為影像分類。

### cost-network

The analytical comparison fixes 8,000 racks or spacecraft and 1 GW, contrasting a terrestrial Clos with an orbital torus. Table 3 reports bisection capacities of 28,800 TB/s versus 2.25 or 10 TB/s under its specific capacities. The inference or training conclusion requires workload cross-cut bytes and physically feasible topology assumptions. [Primary source](https://arxiv.org/abs/2607.14172)

Table 3 的 28,800、2.25、10 TB/s 是特定 Clos 與 torus 容量假設的解析結果，訓練適用性須結合工作負載跨 cut 流量與可實作拓樸。

### connectivity

The 81-node SSO relay/gateway shell in this paper is distinct from Suncatcher’s compact compute formation. Its ground-station and Walker constellation experiments measure geometric connectivity and path stability. All eligible relay choices represent a stated connectivity envelope. [Primary source](https://doi.org/10.1145/3789240.3827590)

本篇 81-node SSO relay/gateway shell 與 Suncatcher compact compute formation 各有其幾何模型；ground-station 與 Walker 實驗評估幾何連通及路徑穩定性。

### dark-clouds

The model’s 3.03 m²/kW radiator sizing and 10 kg/m² imply 30.3 kg/kW. Its 44.3 kg modeled mass includes about 30.5 kg radiator mass; bus, shielding and wiring require further accounting. The fixed 50 W optical terminal is a power assumption that needs capacity-dependent calibration. [Primary source](https://doi.org/10.1145/3789240.3827598)

3.03 m²/kW 與 10 kg/m² 推得 30.3 kg/kW；44.3 kg 模型含約 30.5 kg radiator，bus、shielding、wiring 需另計。50 W terminal 為模型參數。

### orbitalbrain

OrbitalBrain already studies orbital training coordination. It uses a ground-cloud utility planner, local image-model adaptation and shortest-path-tree averaging over 100 Mbps ISLs. Table 3 speedups of 1.52–12.42× use each baseline’s own 24-hour accuracy threshold. LLM fabric experiments should use a common quality target and calibrated training kernels. The appendix accuracy function requires an explicit linear surrogate for a solver-ready MILP. [Primary source](https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.NINeS.2026.5)

OrbitalBrain 已研究軌道訓練協調，採地面 utility planner、本地影像模型 adaptation 與 tree averaging；Table 3 依各 baseline 的 24-hour accuracy 衡量速度。LLM 比較應採共同品質目標與校準 training kernels。

### taccl

TACCL combines routing MILP, greedy chunk ordering and exact scheduling MILP. Its actual collective baseline is NCCL v2.8.4-1. Synthesis runtime and small-message gains belong to the reported machine sizes; its larger DGX-2 AllReduce cases include outcomes up to 9% slower than NCCL. Orbital epoch re-synthesis receives an explicit extension label and charged control cost. [Primary source](https://www.usenix.org/conference/nsdi23/presentation/shah)

TACCL 採 routing MILP、greedy chunk ordering、exact scheduling MILP；實際 baseline 為 NCCL v2.8.4-1。orbital epoch re-synthesis 須明示 adaptation，並計入控制時間。

### topoopt

TopoOpt alternates FlexFlow search and topology construction, with permutation selection, degree allocation, matching and host RDMA forwarding. Its faithful job topology is static between failure events. The OCS-reconfig comparator uses 10 ms setup and 50 ms demand refresh. The 12-server prototype uses four 25 Gbps ports per server; the 3.4× headline is a similar-cost simulated FatTree comparison. [Primary source](https://www.usenix.org/conference/nsdi23/presentation/wang-weiyang)

TopoOpt faithful topology 在 job 期間固定，failure 引發重建；OCS-reconfig baseline 採 10 ms setup、50 ms refresh。12-server prototype 每機四個 25 Gbps ports；3.4× 為 similar-cost FatTree 模擬比較。

### sate

SaTE’s 17 ms allocation inference and separate 56 ms incremental path calculation describe different controller stages. The GNN is supervised using solver labels. Its online improvements charge controller time; scaled 200 Mbps ISL and 50 Mbps access capacities define the evaluation setting. [Primary source](https://fardatalab.org/sigcomm25-wu.pdf)

17 ms allocation 與 56 ms path calculation 屬兩階段；GNN 以 solver labels supervised training，online 比較計入各方法控制時間。

### sn2

SN² activation gains of 4.4–23.5× refer to service activation speed. GNSS-available and disrupted cases use distinct localization comparators. The evaluation combines commodity-phone operation, an NTN protocol stack and GNSS emulation. [Primary source](https://doi.org/10.1145/3718958.3750522)

4.4–23.5× 指 service activation speed；GNSS 可用與受干擾情境各有 localization comparator，實驗結合手機、NTN stack 與 GNSS emulation。

### commsar

CommSAR separates an actual 112 kbps uplink experiment from a 105 kbps measured-channel downlink replay and UAV waveform tests. Each component supports its corresponding mechanism and channel setting. [Primary source](https://ym-zhao.com/publications/zhao2026commsar/commsar-sigcomm26.pdf)

CommSAR 的 112 kbps uplink 實測、105 kbps downlink channel replay 與 UAV waveform test 各支援對應 component claim。

### planet-iot

The eight-node, one-month deployment supports the end-to-end operational claim. The 200–300-node results extend through simulation. The time fraction exceeding 20 minutes falls from 23% to 11%, a 52.2% relative reduction. [Primary source](https://www4.comp.polyu.edu.hk/~csyqzheng/papers/sigcomm26-DtS.pdf)

八節點、單月 deployment 支援現場結果；200–300 nodes 採模擬。超過 20 minutes 的比例由 23% 降至 11%，相對降幅 52.2%。

### coorbit

The 108.6× result measures storage byte-hours in the Australian scenario; 41.6× describes full downlink volume. Ground Jetson experiments and constellation replay support the design. The baseline table separates actual evaluated comparators from related-work taxonomy. [Primary source](https://doi.org/10.1145/3789240.3829176)

108.6× 對應 Australian storage byte-hours；41.6× 對應 full downlink volume。baseline 欄位保留實際評估方法與 related-work 分類的證據差異。

### cosmac

CosMAC’s downlink scheduler uses a maximum-weight independent-set model with conflict repair. Hardware contacts calibrate the RF/CAD model; the 173-satellite, 100,000-device, 1,048-station scale and headline 6.5× result belong to simulation. [Primary source](https://doi.org/10.1145/3636534.3690657)

CosMAC 採 maximum-weight independent-set 與 conflict repair；硬體接觸校準 RF/CAD，173 衛星、100,000 devices、1,048 stations 與 6.5× 屬規模模擬。

### spacesched

SpaceSched uses a genetic heuristic. Its 36.46× result concerns imagery data fraction required to attain 95% coverage, with the reported constellation assumptions. [Primary source](https://doi.org/10.1145/3680207.3765249)

SpaceSched 採 genetic heuristic；36.46× 對應達成 95% coverage 的 imagery data fraction。

### mobility-measurement

The COTS compute measurement uses a 17.44 kg spacecraft with two Atlas 200 DK boards, two Raspberry Pi boards and two 115 Wh batteries. Six months, about 1,000 operating hours and ten million telemetry points establish the reported hardware setting and thermal behavior. [Primary source](https://feng-qian.github.io/paper/sat_mobicom24.pdf)

COTS compute 量測採 17.44 kg spacecraft、兩部 Atlas 200 DK、兩部 Raspberry Pi 與兩組 115 Wh batteries；六個月、約 1,000 hours 與一千萬 telemetry points 界定證據範圍。

## Research claim scope / 研究主張範圍

The three proposed directions concern temporal collective service, KV state continuity and expert/terminal resource co-design. Their continuation thresholds are hypotheses for a measured project: 15% p95 step-time improvement, 20% p99 handover-token-gap improvement, and 10% useful tokens/J improvement. Equal byte, capacity, memory, energy and forecast budgets accompany the corresponding baseline. An 8–32 GPU ground prototype supplies real collective and inference traces; a calibrated event simulator explores stated orbital envelopes. A successful reviewer argument joins component correctness, calibration, distributions, physical budget and workload-level improvement.

三個研究方向各有可測假說：temporal collective 的 p95 step time 提升 15%、KV continuity 的 p99 handover token gap 提升 20%、expert/terminal co-design 的 useful tokens/J 提升 10%。比較固定 bytes、capacity、memory、energy、forecast budgets。8–32 GPU 地面 prototype 提供實際 traces，校準 event simulator 探索明示軌道參數。Reviewer 判讀依據結合 component correctness、calibration、distribution、physical budget 與 workload-level 結果。

## Literal evidence / 原文證據

Exact source-paper titles, original figure pixels and labels, mathematical identifiers, software licenses and schema-required sentinel values retain their literal spelling. Authored explanations, captions, tables and concept labels follow the affirmative-prose gate. 原始題名、原圖文字、數學記號、software license 與 schema sentinel 保留原文；作者解說、caption、表格與概念圖通過直接肯定句檢查。

## Venue-record addendum / 頂會紀錄增補（2026-10-02）

The opening of the page now derives its argument from the publication record, which required two
additional evidence decisions.

First, the SIGCOMM main-track census of 1, 0, 0, 6 and 4 was re-derived from the official pages
rather than carried forward. Each programme or accepted-paper page in the table above was fetched
again and searched directly; the two zero years were each checked against a second independent
official page, the [2023 accepted list](https://conferences.sigcomm.org/sigcomm/2023/list-accepted.html)
and the [2024 programme](https://conferences.sigcomm.org/sigcomm/2024/program/), and both returned
no satellite, LEO, orbital, Starlink, constellation, non-terrestrial or direct-to-cell match. The
counts are therefore audited rather than asserted, and the full title-level screen behind them,
including its classification rule, is recorded in [program-screen.json](program-screen.json).

Second, the page now names papers that are not in the full-primary corpus. They enter at a lower
and explicitly labelled tier: programme-verified, meaning the exact title string was found in an
official programme page on the audit date, with venue and year established and the primary text not
reviewed; or DOI-verified, meaning title, container and year were resolved through Crossref. Each
such identity, the page that confirms it and the tier it enters at are recorded in
[venue-record-sources.json](venue-record-sources.json). Two limits are recorded there as well: the
ACM Digital Library returns HTTP 403 to the audit host, so per-paper DOIs for the programme-verified
SIGCOMM entries were not resolved and are not printed; and the LEO-NET 2026 page carries a call for
papers only, so the two LEO-NET records already in the corpus could not be re-confirmed from it.

頁面開頭現以出版紀錄作為論證基礎，因而需要兩項額外的證據判讀。其一，1、0、0、6、4 的 SIGCOMM 主會議
普查已重新從官方頁面推導，而非沿用既有數字；兩個「零」的年度各以第二個獨立官方頁面複查，均無任何
satellite、LEO、orbital、Starlink、constellation、non-terrestrial 或 direct-to-cell 命中，完整的
題名層級篩查與分類規則記錄於 [program-screen.json](program-screen.json)。其二，頁面現在會指名
不在全文證據庫中的論文，它們以較低且明確標示的層級進入：programme-verified（題名字串於官方 programme
頁面查得，會議與年度成立，primary text 未經審閱）或 DOI-verified（題名、container 與年度經 Crossref
解析）。各筆身分、佐證頁面與層級記錄於 [venue-record-sources.json](venue-record-sources.json)，
其中也記錄兩項限制：ACM Digital Library 對本次稽核主機回傳 HTTP 403，因此 programme-verified 項目的
逐篇 DOI 未解析、也不印出；LEO-NET 2026 頁面僅有徵稿資訊，corpus 既有的兩筆 LEO-NET 紀錄無法由該頁複查。
