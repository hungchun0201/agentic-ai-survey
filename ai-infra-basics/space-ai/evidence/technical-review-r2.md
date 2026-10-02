# Orbital AI networking survey: technical review round 2

Score: **9.3/10**. Technical release verdict: **PASS**. Release threshold: **9.0/10**.

Reviewed artifact: `ai-infra-basics/space-ai/index.html`. SHA-256: `b76825643c6d41ebfeb75409669342c039caf3bf73367cffc5ecf666f077d042`.

The revised survey meets the requested technical standard. It teaches the satellite substrate, distinguishes three coherent physical regimes, connects recent primary research to actual models and evaluations, derives accelerator communication and spacecraft screening examples, and proposes falsifiable networking experiments with obtainable terrestrial baselines. OrbitalBrain receives explicit treatment as distributed-training prior art, and the research claim now targets measured LLM dependency and network-service mechanisms.

## Round 1 repairs verified

| Round 1 finding | Verified round 2 result |
|---|---|
| Executable terrestrial comparisons | The named table gives NCCL Ring/Tree/automatic selection, TACCL’s released synthesizer, TopoOpt’s job-static design and demand-driven OCS comparator, and OrbitalBrain’s utility planner. Each row states its mechanism, starting point, orbital adaptation, charged costs and comparison metrics. |
| Beginner vocabulary | An early bilingual glossary defines MEO/GEO, Doppler, RTT, ECMP/ECN, NIC/RDMA/PFC, GNN, MPC, LP/ILP/MILP, MDP/RL, KV/HBM and NCCL/SLO. The opening defines collective, AllReduce and fabric before using them to state the thesis. |
| Optimization variable domains | Equation A3 now includes nonnegative flow and utilization domains directly in its mathematical statement. |

The baseline table distinguishes faithful source configurations from clearly labelled epoch adaptations. The adaptations retain matched forecast information and legal physical edges and charge setup, terminal power, synthesis, installation and interrupted communication where relevant. This separation makes the prospective comparison causal and implementable.

## Independent source verification

I checked the new TACCL and TopoOpt primary texts alongside their rendered analyses, figures, baseline table and bilingual explanations. Their official [TACCL NSDI paper entry](https://www.usenix.org/conference/nsdi23/presentation/shah) and [TopoOpt NSDI paper entry](https://www.usenix.org/conference/nsdi23/presentation/wang-weiyang) establish publication identities. The current [NCCL algorithm-selection documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-algo) supplies an obtainable library comparator; the plan appropriately pins its actual experimental version.

TACCL’s record correctly describes sketches, profiled latency/bandwidth, relaxed routing MILP, heuristic chunk ordering, contiguity/exact scheduling and the execution runtime. Its 6.7× headline refers to a standalone collective condition. The page distinguishes that result from model-training improvements and preserves the large-message AllReduce regression and synthesis costs. The cited NCCL v2.8.4-1 reference matches the source evaluation.

TopoOpt’s record correctly describes alternating parallelization and topology search, degree-limited graph construction, TotientPerms collective paths, model-parallel matching and host forwarding. Its principal configuration fixes the topology for a training job. The separate OCS comparator assumes 10 ms reconfiguration and 50 ms demand refresh. The page labels orbital epoch adaptations explicitly. The 3.4× simulated comparison, 12-server hardware prototype, four 25 Gbps interfaces, and all-to-all forwarding sensitivity retain their original experimental scopes.

The new original figures correctly depict TACCL’s synthesis pipeline and TopoOpt’s optical switching planes. Their captions explain the mechanism and the orbital transfer conditions. The conceptual terrestrial-reference figure establishes the fixed-endpoint comparison before the later AI-fabric argument.

The round 1 primary checks continue to support OrbitalBrain’s baseline-specific accuracy thresholds, CosMAC’s simulated throughput conditions, SaTE’s separated inference/path costs, COTS thermal measurements, and CommSAR’s direction-specific component evidence. The physical and byte-count examples retain correct units and arithmetic.

## Research-plan assessment

Project 1 has a concrete collective implementation, a synthesis comparator, a topology/parallelism comparator, a schedule-informed adaptation and a small-instance optimization reference. The experiment measures application critical paths and charges controller costs. Its effect threshold and stop rule keep future-information and extra-capacity effects visible.

Project 2 connects resident KV state to measured access transitions and application token continuity. Sticky, handover-triggered and forecast-informed policies provide understandable comparisons. The evaluation separates observable service events from inferred operator mechanisms and compares memory, byte budgets and admission fairness.

Project 3 jointly accounts for expert communication, terminal resources and energy. Its continuation rule requires robustness to forecast error, expert skew and the thermal model. This is a prospective mechanism with explicit evidence obligations. Thermal and power parameter provenance therefore remains part of the operating envelope.

The lab plan supplies actual accelerator execution, calibrated packet replay, trace-driven topology, separate wide-area and formation bundles, versioned software, correctness, power and tail metrics. Extrapolated high-rate simulation receives a separate evidence label. A project implementation will choose the concrete trace generator, physical calibration data and adapted planner; the survey gives the constraints and acceptance tests that govern those choices.

## Corpus and presentation checks

Independent page inspection counts **37 paper records**, **37 original figures**, **12 concept SVGs**, and **12 displayed equations**. The structured corpus contains the same 37 paper identifiers. The eleven satellite-targeted SIGCOMM main papers and Loon adjacency preserve their scoped census interpretation. Terrestrial AI papers receive a distinct reference regime.

All internal fragment targets resolve. All 1,903 English translation nodes carry matching Chinese attributes. Sampled bilingual glossary, baseline, project and source-record passages preserve the same mechanisms, assumptions and experimental boundaries. The reviewed mobile concept figure remains readable and correctly labels its power/thermal scope.

The exported responsive evidence reports sixteen passing browser/language/viewport cells, twelve painted equations per cell, zero mathematics errors, and zero concept-label collisions. The original-figure evidence reports 37 passing figure identities. The schema evidence reports 37 records with a passing status.

## Packaging completion

The linked `evidence/QA.md` summary is present, alongside `ADJUDICATION.md`, the structured corpus and exported JSON evidence. The final page retains the accepted content and uses lazy loading for the original figures. The technical acceptance applies to the final content and page snapshot identified above.

## Remaining editorial refinement

MPC appears in both the compact glossary and the physical-link vocabulary table. Consolidating the second occurrence would slightly shorten the beginner section. The current definitions agree, so the duplicate carries a small reading-cost effect.

## Acceptance rubric

| Criterion | Round 2 assessment |
|---|---|
| Beginner satellite foundation | Pass: orbit, contacts, path layers, RF/optical service and early vocabulary form a coherent reading path. |
| Paper and venue scope | Pass: full-primary analyses, source figures, explicit venue tiers and scoped SIGCOMM census agree. |
| Models and mathematics | Pass: algorithm families, temporal constraints, variable domains, dimensions and examples remain sound. |
| Evaluation practice | Pass: observable/latent distinction, matched baselines, calibration, independence and evidence tiers are explicit. |
| Orbital engineering | Pass: power, heat, mass and terminal constraints remain physically scoped screening and source estimates. |
| LLM research novelty | Pass: prior art and named comparators support incremental, falsifiable networking hypotheses. |
| Bilingual/visual reading | Pass: sampled translation parity, clear concept labels and original-figure provenance meet the intended use. |
| Affirmative prose | Pass: independent authored visible-text and EN/ZH attribute scan returns zero excluded matches. |

## Artifact QA log

Independent page prose scan: **0 excluded matches**, using case-insensitive English word boundaries and the requested Chinese character set after separating scripts, styles, labelled original-source quotations and code. Both translation attributes were included.

Review-artifact lexical scan: **0 excluded matches**. This review writes its owned Markdown artifact and preserves the site and source packages.

## Final formatting verification

The final snapshot incorporates whitespace normalization on a CSS blank line. This formatting adjustment preserves the reviewed semantic content and retains the **9.3/10 PASS** technical verdict. The final responsive evidence reports sixteen passing cells. The SHA-256 above identifies the normalized release artifact.
