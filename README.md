# AI Infrastructure Optimizations for Agentic LLM Workflows

[![GitHub Pages](https://img.shields.io/badge/Website-Live-brightgreen)](https://hungchun0201.github.io/agentic-ai-survey/)
[![Papers](https://img.shields.io/badge/Papers-76-blue)]()
[![Repos Analyzed](https://img.shields.io/badge/Repos%20Analyzed-38-orange)]()

A survey of **76 systems research papers (2023–2026)** on infrastructure optimizations for agentic LLM workloads, covering OSDI, SOSP, ISCA, FAST, MLSys, NeurIPS, ICML, ICLR, EuroSys, ASPLOS, NSDI, ATC, and SIGCOMM.

**[Browse the Interactive Survey](https://hungchun0201.github.io/agentic-ai-survey/)** (Chinese / English)

---

## Scope

| # | Area | Papers | Key Focus |
|---|------|--------|-----------|
| S1 | Workload Characterization | 5 | Profiling agentic traffic patterns, CPU bottlenecks, sustainability |
| S2 | Prefill-Decode Disaggregation | 13 | PD splitting, storage NIC bottlenecks, CXL, RDMA |
| S3 | KV Cache Management | 19 | PagedAttention, RadixAttention, position-independent, workflow-aware, cross-agent KV reuse |
| S4 | KV Cache TTL & Retention | 4 | Pin/evict during tool-call pauses, AIMD admission, model-driven eviction |
| S5 | Scheduling & Routing | 11 | Program-level DAGs, stage isolation, declarative workflows, on-device |
| S6 | Learning-based Cache | 10 | Regret-minimization, RL eviction, combinatorial bandits |
| S7 | Adjacent Optimizations | 14 | Chunked prefill, MLA compression, speculative decoding critique, multi-path all-to-all, agentic context engineering |

## Paper List

### S1 — Workload Characterization

| Paper | Venue | arXiv |
|-------|-------|-------|
| Continuum — KV Cache TTL for Agent Scheduling | arXiv'25 | 2511.02230 |
| The Cost of Dynamic Reasoning | HPCA'26 | 2506.04301 |
| A CPU-Centric Perspective on Agentic AI | arXiv'25 | 2511.00739 |
| PrefillShare — Shared Prefill for Multi-LLM | arXiv'26 | 2602.12029 |
| AgentInfer — Co-Design of Inference Architecture | arXiv'25 | 2512.18337 |

### S2 — Prefill-Decode Disaggregation

| Paper | Venue | arXiv |
|-------|-------|-------|
| DistServe — PD Disaggregation for Goodput | OSDI'24 | 2401.09670 |
| Splitwise — Phase Splitting for LLM Inference | ISCA'24 | 2311.18677 |
| Mooncake — KVCache-centric Architecture | FAST'25 ★ | 2407.00079 |
| DualPath — Storage Bandwidth Bottleneck Fix | arXiv'26 | 2602.21548 |
| TaiChi — Hybrid Aggregation-Disaggregation | arXiv'25 | 2508.01989 |
| NVIDIA Dynamo — Smart Router + KV Manager | GTC'25 | — |
| TraCT — CXL Shared Memory KV Cache | arXiv'25 | 2512.18194 |
| WindServe — Stream-based Dynamic Scheduling | ISCA'25 | — |
| NanoFlow — Nano-grained Pipeline Parallelism | OSDI'25 ★ | 2408.12757 |
| FlowKV — Low-Latency KV Transfer | arXiv'25 | 2504.03775 |
| PPD — Routing Append-Prefills to Decode Nodes | arXiv'26 | 2603.13358 |
| DuetServe — Adaptive GPU Multiplexing | arXiv'25 | 2511.04791 |
| BanaServe — Layer-level Weight Migration | arXiv'25 | 2510.13223 |

### S3 — KV Cache Management & Prefix Caching

| Paper | Venue | arXiv |
|-------|-------|-------|
| vLLM — PagedAttention | SOSP'23 | 2309.06180 |
| SGLang — RadixAttention | NeurIPS'24 | 2312.07104 |
| LMCache — Multi-tier KV Storage Layer | arXiv'25 | 2510.09665 |
| CachedAttention — Hierarchical KV Persistence | ATC'24 | 2403.19708 |
| llm-d — K8s-native KV Cache Indexer | OSS'26 | — |
| CacheGen — KV Cache Compression Codec | SIGCOMM'24 | 2310.07240 |
| CacheBlend — Non-prefix KV Cache Reuse | EuroSys'25 ★ | 2405.16444 |
| EPIC — Position-Independent Caching | ICML'25 | 2410.15332 |
| IC-Cache — Semantic In-context Caching | SOSP'25 | 2501.12689 |
| KVFlow — Workflow-aware Prefix Caching | NeurIPS'25 | 2507.07400 |
| Marconi — Prefix Caching for Hybrid LLMs | MLSys'25 ★HM | 2411.19379 |
| DiffKV — Differentiated KV Memory | SOSP'25 ★ | 2412.03131 |
| Jenga — Heterogeneous KV Embeddings | SOSP'25 | 2503.18292 |
| Pie — Programmable Serving System | SOSP'25 | 2510.24051 |
| DeepSeek MLA — Multi-Head Latent Attention | arXiv'24 | 2405.04434 |
| MHA2MLA — Retrofitting MLA | ACL'25 | 2502.14837 |
| Oaken — Hybrid KV Cache Quantization | ISCA'25 | 2503.18599 |
| TokenLake — Unified Segment Prefix Cache | arXiv'25 | 2508.17219 |
| KVCOMM — Cross-context KV-cache Communication | NeurIPS'25 | 2510.12872 |

### S4 — KV Cache TTL & Retention

| Paper | Venue | arXiv |
|-------|-------|-------|
| InferCept — KV Cache Preserve for Tool Calls | ICML'24 | 2402.01869 |
| Concur — AIMD Agent Admission Control | arXiv'26 | 2601.22705 |
| ThunderAgent — Program-aware Pause/Restore | arXiv'26 | 2602.13692 |
| SideQuest — Model-driven KV Eviction | arXiv'26 | 2602.22603 |

### S5 — Scheduling & Routing

| Paper | Venue | arXiv |
|-------|-------|-------|
| Autellix — Program-level DAG Scheduling | arXiv'25 | 2502.13965 |
| Cortex — Stage-isolated Resource Pooling | arXiv'25 | 2510.14126 |
| Murakkab — Declarative Workflow Optimization | arXiv'25 | 2508.18298 |
| Agent.xpu — On-device SoC Scheduling | arXiv'25 | 2506.24045 |
| Preble — Cluster-level KV-aware Scheduling | ICLR'25 | 2407.00023 |
| AI Metropolis — Out-of-order Multi-Agent | MLSys'25 | 2411.03519 |
| Helium — Query-plan Agentic Workflows | arXiv'26 | 2603.16104 |
| Sherlock — Reliable Agentic Workflow | arXiv'25 | 2511.00330 |
| Aragog — Just-in-Time Model Routing | arXiv'25 | 2511.20975 |
| SOLA — State-aware SLO Scheduling | MLSys'25 | — |
| SuperServe — Fine-grained Serving | NSDI'25 | 2312.16733 |

### S6 — Learning-based Cache Management

| Paper | Venue | arXiv |
|-------|-------|-------|
| LeCaR — Regret-based LRU/LFU Weighting | HotStorage'18 | — |
| CACHEUS — Fully Adaptive Cache Replacement | FAST'21 | — |
| RLCache — Multi-task RL Cache Management | arXiv'19 | 1909.13839 |
| Cold-RL — Offline RL for NGINX Eviction | arXiv'25 | 2508.12485 |
| KV Policy — Per-head RL KV Eviction | arXiv'26 | 2602.10238 |
| Semantic Cache Bandit — MAB for Cache Eviction | arXiv'25 | 2508.07675 |
| Attention-Gate — In-context KV Eviction | arXiv'24 | 2410.12876 |
| NACL — General KV Cache Eviction | ACL'24 | 2408.03675 |
| LookaheadKV — Future Attention Prediction | arXiv'26 | 2603.10899 |
| Ada-KV — Adaptive Per-head Budget | NeurIPS'25 | 2407.11550 |

### S7 — Adjacent Optimizations

| Paper | Venue | arXiv |
|-------|-------|-------|
| Sarathi-Serve — Chunked Prefills | OSDI'24 | 2308.16369 |
| DeepSpeed-FastGen — Dynamic SplitFuse | arXiv'24 | 2401.08671 |
| Speculative Tool Calling | arXiv'25 | 2512.15834 |
| Speculative Actions — Lossless Agent Speedup | arXiv'25 | 2510.04371 |
| ServerlessLLM — Fast Cold-start | OSDI'24 | 2401.14351 |
| FlashInfer — Customizable Attention Engine | MLSys'25 ★ | 2501.01005 |
| NEO — CPU Offloading for KV + Attention | MLSys'25 | 2411.01142 |
| HCache — Fast KV State Restoration | EuroSys'25 | 2410.05004 |
| Pensieve — Stateful Multi-turn Serving | EuroSys'25 | 2312.05516 |
| Helix — Heterogeneous GPU Max-Flow | ASPLOS'25 | 2406.01566 |
| Weaver — Multi-LLM Attention Offloading | ATC'25 | — |
| ACE — Agentic Context Engineering | ICLR'26 | 2510.04618 |
| NIMBLE — Multi-Path All-to-All for GPU Clusters | arXiv'26 | 2604.00317 |
| Speculative Decoding: Performance or Illusion? | arXiv'26 | 2601.11580 |

★ = Best Paper &nbsp; ★HM = Outstanding Paper Honorable Mention
