# Implied residency prices (public constants only) — 2026-07-06
| channel | $/MTok/hr |
|---|---|
| Anthropic via 5-min pings (0.1x read x 12/hr) | 3.60 |
| Anthropic 1h-vs-5m write premium ((2-1.25)x$3 / 55min) | 2.45 |
| Gemini explicit storage (Flash / Pro) | 1.00 / 4.50 |
| DRAM cost floor (131KB/tok, $0.001-0.004/GB-hr) | 0.13-0.52 |

Findings: (a) menu inconsistency inside Anthropic (ping>40min irrational yet shipped tools
ping); (b) 3.6x cross-provider spread for the same good; (c) residency priced 7-27x above
storage cost -> lifecycle-bit contract at storage+margin Pareto-dominates (to formalize).
