# Orbital AI networking survey: technical review round 1

Score: **8.8/10**. Release threshold: **9.0/10**. Current disposition: **revision and fresh review**.

Reviewed artifact: `ai-infra-basics/space-ai/index.html`. Snapshot modification time: 2026-10-02 05:04:22 local. SHA-256: `3638c93c817ca9042ca90a4545bf56d26fdc891670208c31e2988323602b34a7`.

The survey supplies a substantial primary-source foundation, carefully scoped physical examples, a complete scoped SIGCOMM census, and an unusually strong evaluation discussion. Two revisions would bring its beginner reading path and project-baseline specificity to the requested release standard. The score assesses the rendered 35-paper version, including CosMAC and OrbitalBrain.

## Evidence reviewed

I read the fifteen core sections, all 35 structured paper records, the updated rendered thesis, gap matrix, project plan and census, both investigation reports, the assembler’s publication grouping, the captions, original-figure contact sheets, and selected desktop/mobile screenshots. Independent primary-text checks covered OrbitalBrain’s formulation, model-averaging mechanism, evaluation and Tables 2–4; CosMAC’s conflict graph and Figure 10; SaTE’s runtime and online-demand metrics; the COTS measurement’s thermal findings; and CommSAR’s component-level evaluation. Official-program entries and the saved full yearly programs establish the census scope.

The current artifact contains 35 detailed paper records, 35 original figures, eleven concept SVGs, and twelve displayed equations. The appendix distinguishes eleven satellite-targeted SIGCOMM main papers from the Loon stratospheric adjacency. The other venue rows explicitly describe representative coverage. The source-quotation annotations distinguish original titles and image text from authored prose.

## Required revisions

### R1: Make the terrestrial comparison executable

**Location:** `#terrestrial-comparison`, `#gap-matrix`, `#designs`.

**Observed wording:** Project 1 lists fixed fabric, adaptive TE, schedule-informed collective placement and a small-instance MILP. The prose invokes mature terrestrial AI-fabric techniques. These are useful comparison families; concrete implementations and source references establish the actual experiment.

**Consequence:** A researcher implementing this proposal still has to select the collective library, the synthesis or scheduling method, the optical reconfiguration comparator, and their adaptation rules. Those choices can determine the apparent orbital mechanism gain.

**Revision:** Add a compact named-baseline table with at least one actual collective implementation, one topology-aware collective synthesis or scheduling method, and one reconfigurable optical scheduler. Give each its primary source, controlled mechanism, relevant regime, and explicit adaptation to orbital forecasts, terminal degree and setup costs. Retain the stated equal-information and equal-resource budgets. Preserve the explicit OrbitalBrain-style utility scheduler and the common-quality-target comparison.

**Acceptance check:** A reader can name and obtain the baseline implementation or formulate its documented algorithm, understand the orbital adaptation, and identify the metric that compares it with the proposed mechanism. A software collective and a federated-learning scheduler each receive a workload-specific comparison.

### R2: Complete the beginner vocabulary path

**Location:** `#satellite-primer`, `#regimes`, `#mechanisms`, `#reading-map`, `#evaluation`.

**Observed wording:** ECMP and ECN first appear as acronyms in the control table; GNN enters the SaTE spotlight; MILP enters the OrbitalBrain spotlight; NIC enters the evaluation table; KV appears in the regime-C concept before the state definition. Doppler appears in paper models before its physical meaning receives an explanation. MEO and GEO appear in operator coverage.

**Consequence:** The reading sequence assumes networking and radio vocabulary at several early points, increasing friction for the specified beginner audience.

**Revision:** Add a concise bilingual glossary before the first affected concept/table. Expand ECMP, ECN, GNN, ILP/MILP, MPC, NIC and KV, and define the networking action or resource each names. Explain Doppler through relative radial motion, received-frequency shift and synchronization. Define MEO and GEO when those classes support the operator comparison. A one-sentence definition of a collective would also help the opening thesis.

**Acceptance check:** The beginner can read the core path and understand every acronym that carries an argument before following an appendix paper. English and Chinese definitions retain the same physical and algorithmic scope.

## Small mathematical improvement

**Location:** illustrative traffic-engineering equation A3.

The displayed program states capacity and conservation constraints. Add the variable domains `f ≥ 0` and `u ≥ 0` directly to the mathematical statement. This makes the illustrative optimization self-contained for a reader translating it into a solver. Its routing-change penalty and unit-scaling explanation are useful.

## Verified technical strengths

### Census and source identity

The scoped main-track counts are 1, 0, 0, 6 and 4 for 2022–2026, yielding eleven satellite-targeted papers. Loon receives its separate adjacent-substrate interpretation. The 2025 list includes LeoCC and SN², and the 2026 list includes CoOrbit. These three identities often escape topic searches; their presence improves the census. The official [2025 paper program](https://conferences.sigcomm.org/sigcomm/2025/program/papers-info/) and [2026 paper program](https://conferences.sigcomm.org/sigcomm/2026/program/papers/) support the corresponding inventories. The broad-venue table clearly presents a curated mechanism map.

### Algorithm classification and metric scope

SaTE is classified as supervised GNN inference from solver labels. CosMAC is classified through overlap-aware access control and a weighted independent-set downlink scheduler. SpaceSched uses genetic search. Collaborative inference uses A* layer assignment and inner compression optimization. The MDP and Markov-chain discussion defines their separate roles and treats RL as a model-dependent tool.

The SaTE record correctly separates the 17 ms allocation stage from the separate 56 ms path calculation. Its online demand improvements depend on charged controller computation and the tested connectivity arrangement. CosMAC’s 50-packet/day case correctly reports 1,388 bps versus 211 bps and 922 bps for its two combined end-to-end baselines; the large throughput gain belongs to simulation calibrated through hardware components.

The OrbitalBrain record correctly identifies cloud-side planning, shortest-path-tree weight averaging, final-five-layer image-model adaptation, five-minute windows, bounded 100 Mbps ISLs, and trace-driven learning simulation. Table 3’s speedup uses each compared baseline’s own 24-hour final accuracy. The page’s common-quality-target requirement strengthens the future fabric experiment. The record also makes the accuracy-function surrogate required for a solver-ready MILP explicit.

### Physical accounting and workload arithmetic

The 550 km circular-orbit example gives approximately 95.5 minutes, and the overhead propagation example gives 1.83 ms per space–ground hop. The 100 m² solar assumptions yield approximately 29.4 kW usable and a 34-accelerator electrical screening bound. The separate ideal radiator assumptions yield approximately 41.3 kW at 300 K and 31.4 kW at 280 K. The text states environmental terms, emitting area, fixed loads and component-temperature scope.

The ring example correctly counts 24.5 GB outbound per rank for eight ranks and a 7B-element, two-byte gradient. Serialization is 1.96 seconds at 100 Gbps and 19.6 ms at 10 Tbps. The grouped-query KV example gives 1.074 GB and 85.9 ms at 100 Gbps. Decimal units and payload scope are explicit. The PP and EP formulas state their aggregation and vector-width assumptions.

Suncatcher’s bench throughput, multi-Tbps design estimate, compact geometry and radiation testing remain separate evidence layers. The 34-accelerator screening example carries its own assumptions. The COTS record identifies the measured edge-board configuration and its operating limits. CommSAR distinguishes actual uplink measurements, downlink-channel replay and UAV waveform testing. The orbital-AI claim therefore rests on appropriate subsystem evidence.

### Evaluation and research reasoning

The service-path inverse problem receives clear treatment: observed endpoint events support measured service behavior, while spacecraft assignment requires corroborating identification evidence. The plan matches future information, terminal capacity, memory, power and background traffic. It charges controller cost, calibrates replay, defines independent sampling units, and reports distributions and correctness.

The updated thesis acknowledges OrbitalBrain as direct training precedent. The resulting gap concerns measured LLM communication dependencies and physically calibrated network service. Project continuation and stopping rules define falsifiable decisions. Regime B’s evidence remains conditional on credible optical setup and link behavior, which is appropriate for a prospective research plan.

### Presentation and bilingual scope

The concept diagrams communicate distinct substrate, contact, state and workload structures. Original figures and source captions give concrete architecture and measurement context. The reviewed desktop and 375-pixel Chinese screenshots preserve readable concept labels and clear diagram legends. English and Chinese core fields maintain the same assumptions, units, hypotheses and evidence boundaries. The shared results label now accommodates analytical and simulation outputs alongside hardware measurements.

## Acceptance rubric for round 2

| Criterion | Release evidence |
|---|---|
| Beginner foundation | Vocabulary definitions precede their conceptual use; Doppler and orbit classes receive concise explanations. |
| Paper identity and coverage | 35 records, 35 original figures, eleven scoped SIGCOMM main papers and the Loon adjacency agree across page and corpus. |
| Algorithms and mathematics | Actual algorithm families, variable domains, units and example arithmetic remain correct. |
| Evaluation | Baseline information/resource budgets, observable-versus-latent scope, sampling units and hardware/simulation layers remain explicit. |
| Physical substrate | Accelerator screening, source engineering estimates and prototypes retain their separate parameter provenance. |
| LLM contribution | OrbitalBrain prior art, named terrestrial baselines, workload-specific adaptation and measurable novelty support the project claims. |
| Bilingual and visual reading | EN/ZH explanations preserve scope; figures retain source identity and legible concept labels. |
| Affirmative prose | Independent scan returns zero excluded authored-prose matches; source quotations and code receive separate treatment. |

## Artifact QA log

Independent rendered/translation-attribute prose scan: **0 excluded matches**. The scan removed scripts, styles, labelled source quotations and code before testing authored visible text and both translation attributes. English matching used case-insensitive word boundaries; Chinese matching used the requested excluded characters. Original source titles and source-image labels retain their literal-evidence classification.

Review-artifact lexical scan: **0 excluded matches**. This review changes its owned Markdown artifact and preserves the site and author packages.
