# AI Infrastructure Optimizations for Agentic LLM Workflows

[![GitHub Pages](https://img.shields.io/badge/Website-Live-brightgreen)](https://hungchun0201.github.io/agentic-ai-survey/)
[![Papers](https://img.shields.io/badge/Papers-72-blue)]()
[![Repos Analyzed](https://img.shields.io/badge/Repos%20Analyzed-38-orange)]()
[![Best Papers](https://img.shields.io/badge/Best%20Papers-5-red)]()

A curated and continuously updated survey of **72 systems research papers (2023–2026)** on infrastructure optimizations for agentic LLM workloads, covering top venues including OSDI, SOSP, ISCA, FAST, MLSys, NeurIPS, ICML, EuroSys, ASPLOS, NSDI, ATC, and SIGCOMM.

**[Browse the Interactive Survey](https://hungchun0201.github.io/agentic-ai-survey/)** (Chinese / English)

---

## Overview

LLM-powered autonomous agents — systems that iteratively reason, invoke tools, and operate over dozens to hundreds of inference turns — have exposed fundamental mismatches between existing LLM serving infrastructure and the demands of agentic workloads. This survey organizes the rapidly growing body of systems research into **7 problem areas**:

| # | Area | Papers | Key Focus |
|---|------|--------|-----------|
| S1 | Workload Characterization | 5 | Profiling agentic traffic patterns, CPU bottlenecks, sustainability |
| S2 | Prefill-Decode Disaggregation | 13 | PD splitting, storage NIC bottlenecks, CXL, RDMA |
| S3 | KV Cache Management | 18 | PagedAttention → RadixAttention → position-independent → workflow-aware |
| S4 | KV Cache TTL & Retention | 4 | Pin/evict during tool-call pauses, AIMD admission, model-driven eviction |
| S5 | Scheduling & Routing | 11 | Program-level DAGs, stage isolation, declarative workflows, on-device |
| S6 | Learning-based Cache | 10 | Regret-minimization, RL eviction, combinatorial bandits |
| S7 | Adjacent Optimizations | 11 | Chunked prefill, MLA compression, speculative tool calls, serverless |

## Featured Best Papers

| Paper | Venue | Key Contribution |
|-------|-------|-----------------|
| [Mooncake](https://hungchun0201.github.io/agentic-ai-survey/papers/mooncake/index.html) | FAST'25 | KVCache-centric disaggregation, 100B+ tokens/day at Moonshot AI |
| [NanoFlow](https://hungchun0201.github.io/agentic-ai-survey/papers/nanoflow/index.html) | OSDI'25 | Nano-grained pipeline parallelism for near-optimal throughput |
| [CacheBlend](https://hungchun0201.github.io/agentic-ai-survey/papers/cacheblend/index.html) | EuroSys'25 | Non-prefix KV cache reuse via selective recomputation |
| [DiffKV](https://hungchun0201.github.io/agentic-ai-survey/papers/diffkv/index.html) | SOSP'25 | Differentiated memory management for keys vs. values |
| [FlashInfer](https://hungchun0201.github.io/agentic-ai-survey/papers/flashinfer/index.html) | MLSys'25 | Block-sparse attention engine with JIT-compiled templates |

## What Makes This Survey Different

Each paper has a dedicated analysis page that follows a **"repo first, paper second"** methodology:

1. **Explore the open-source implementation** (when available) — read the actual code
2. **Read the paper** — understand the claimed contributions
3. **Compare** — identify gaps between claims and implementation

This approach grounds the analysis in real artifacts rather than taking paper claims at face value.

## Paper Classification Tags

Every paper is tagged along multiple dimensions for easy filtering:

| Tag | Meaning |
|-----|---------|
| `Agentic ✓` | Explicitly designed for agentic workloads |
| `Agentic ~` | Partial agentic support |
| `PD Disagg` | Involves prefill-decode disaggregation |
| `Distributed` | Distributed / multi-node system |
| `repo` | Has open-source code |
| `★ Best Paper` | Best paper award at venue |

## Adding New Papers

This survey is designed for easy extension. To add a new paper:

1. **Add metadata** — Create `content/papers/your-paper.json` with the paper's metadata (title, venue, arXiv, tags, summaries)
2. **Create analysis page** — Use `PAPER_PAGE_TEMPLATE.md` (1,482 lines of detailed instructions) to guide an LLM in creating `papers/your-paper/index.html`
3. **Commit & deploy** — Push to `master`; GitHub Actions rebuilds the index automatically

See [`PAPER_PAGE_TEMPLATE.md`](PAPER_PAGE_TEMPLATE.md) for the complete guide.

## Repository Structure

```
├── index.html / index-zh.html / index-en.html   # Survey portal (bilingual)
├── data/
│   ├── sections.json          # 7 section definitions
│   └── papers-index.json      # All paper metadata (auto-generated)
├── content/papers/             # Individual paper metadata (72 JSON files)
├── papers/*/index.html         # Detailed analysis pages (72 papers)
├── PAPER_PAGE_TEMPLATE.md      # LLM instructions for creating paper pages
└── .github/workflows/deploy.yml
```

## Citation

If you find this survey useful, please consider citing the underlying papers. The survey itself is organized around the research question of **adaptive KV cache TTL policies** — see the [survey document](https://hungchun0201.github.io/agentic-ai-survey/) for the full analysis.

## License

The survey content is for educational and research purposes. Individual papers and repositories retain their original licenses.
