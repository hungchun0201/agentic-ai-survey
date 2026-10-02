# Final closure review R4 — "Satellite Networking for Orbital AI Centers"

**Score: 9.3 / 10 — Verdict: PASS**

All six R3 fixes are closed in the R4 snapshot, in both languages and in the corpus. Every diff hunk maps to one of the six repairs; numbers, formulas and conclusions are identical across R3 and R4. Five cosmetic residues and one evidence-link item remain, all optional for release.

**Hash basis:** `1f54e484420d7b88d7206ccaf906028f75915e9fa64c1317337dde266ed23aeb`, computed by the lead and matching `evidence/snapshot-qa.json:2` and `QA.md:37`. My toolset excludes hashing, so the hash rests on those matching records. This PASS applies to that snapshot only.

## Closure table

| Fix | Status | Evidence |
|---|---|---|
| R3-1 ledger counts | Closed | `page-en-r4.txt:1699` reads "22-work"; `:1705` reads "21 AI/fabric identities; together with Cyclops, 22". The list now ends with Harvest, Opus, MixNet, GeoOrchestra and PReCCL. Chinese text matches at the same lines. Scans for the old 17/16 strings return zero hits in both texts, `index.html` and the corpus. |
| R3-2 Opus version | Closed | The Opus comparator row and appendix status line both show "arXiv 2602.12521v3, 2026-07-03" with DOI verified, matching `paper-corpus.json:3489`. The other four new comparator rows state author-hosted PDF or official ACM reader with page counts. Nine further appendix status lines also gained a source version. |
| R3-3 English wording | Closed, cosmetic residue | "lowers p95" at `:1121`; "5.31% slower than EPS" in the Opus record; the Crux duplicate wording is fixed. Number spacing is restored across the records, with model identifiers such as Mixtral8×7B intact. |
| R3-4 duplicate paragraph | Closed | The full paragraph stays once at `:1116`. `:1176` is now a one-sentence pointer to the gap analysis, in both languages. |
| R3-5 Chinese localization | Closed | All 60 appendix status lines begin "完整 primary text 已審閱" (67 hits including the seven featured cards). Zero English status prefixes remain. The T badge reads "地面比較基準" everywhere. Zero spaces follow a Chinese full stop. Theseus uses "切換 schedule". |
| R3-6 corpus years | Closed | All 60 `year` values are four-digit strings; the frozen R3 corpus mixed integers, `YYYY` and `YYYY-MM`. The 60 record IDs are identical in order and content to the frozen corpus. |

## Gates

- **Diff check:** I read both diffs in full (English 1,051 lines, Chinese 1,344 lines). Beyond the six repairs, the only visible change is the year display moving from `YYYY-MM` to `YYYY`, which follows from R3-6.
- **Lexical gate:** `lexical-qa.json` reports pass, zero authored-prose matches and zero Simplified matches.
- **Responsive gate:** `responsive-qa.json` reports pass for 16 cells (two engines, EN/ZH, 375/414/768/1440) plus two desktop typography checks. Each cell shows 43 of 43 math blocks painted, 60 images, root scroll width equal to viewport, and `navControlsOverlap` false. SVG overlap, outside and image-failure lists are all empty.
- **Figure and schema gates:** `figure-qa.json` passes for 60 figures; `schema-qa.json` passes for 60 records.
- **Math count:** 43 blocks in `page-en-r4.txt`, matching the snapshot record.
- **Screenshots:** I viewed 4 of 64. `chromium-zh-1440-appendix.png` shows the R4 localized status line, confirming the captures are fresh. The population-B label placement is unchanged from the R3-reviewed geometry.

The R3 procedure (diff check plus lexical and responsive reruns) was followed and is adequate for these wording and metadata changes.

## Residual items (optional)

1. **Month suffix in two comparator headings:** "MixNet · SIGCOMM 2025-09" and "GeoOrchestra · SIGCOMM 2026-08" (`:504`, `:511`, both languages) keep the month while every other row uses the year alone.
2. **Punctuation-fused numerals:** about a dozen remain after a comma, semicolon or colon, for example "four servers,32 A100 GPUs,16 ConnectX-6" and "a32×32" (`:509, 1628, 3533`), ";75%" (`:2104`), "a50W" (`:2790`), "26February2026" (`:3271`) and "ATP:7.35×" (`:3405`).
3. **Crux record:** one redundant "reported" remains in "and reported +4–7%".
4. **Chinese source-version values:** nine stay in English after the localized "來源版本" label (`page-zh-r4.txt:2120, 3211–3421`).
5. **QA links:** `QA.md:29` links `claude-fable-review-r3.md` and `claude-fable-provenance.json`. Both are absent from the evidence directory at inspection time, so the lead should add them, or repoint the links, when appending this report.
6. **Mobile equation width:** in `webkit-en-375-appendix.png` the widest SaTE constraint line runs past the block's right edge at 375 px. Page-level width stays at 375, and the layout is unchanged from R3.

## Rubric

| # | Requirement | R3 | R4 | Basis for change |
|---|---|---|---|---|
| 1 | SIGCOMM census and appendix | 9.4 | 9.5 | Ledger counts now consistent |
| 2 | Beginner foundations | 9.2 | 9.2 | Unchanged |
| 3 | Per-paper depth | 9.2 | 9.3 | Wording fixed; fused-numeral residue |
| 4 | Evidence routes and reviewer expectations | 9.2 | 9.2 | Unchanged |
| 5 | Orbital compute substrate | 9.3 | 9.3 | Unchanged |
| 6 | LLM traffic, prior art, experiments, gates | 9.3 | 9.4 | Duplicate removed |
| 7 | Bilingual, figures, mathematics, browser evidence | 9.1 | 9.3 | Status lines and badge localized |
| 8 | Source identity and scope honesty | 9.0 | 9.4 | Versions visible; years normalized |
| | **Mean** | 9.2 | **9.3** | PASS |

## Evidence boundaries

- **Read this round:** both diffs in full, plus pattern scans over `page-en-r4.txt`, `page-zh-r4.txt`, `index.html` and the current and frozen corpus. The complete R4 texts were covered through the diffs and scans rather than a fresh line-by-line read.
- **Carried from R3:** the census of 11 central papers, two aerial adjacencies and one terminal ledger entry; the arithmetic recomputation; the primary-source checks for the five new records; and the full English read. The diffs show those regions unchanged.
- **Corpus:** `year` and `id` for all 60 records, the Opus `source_version`, and stale-string scans. Other fields rest on the rendered diff.
- **Machine reports:** the lexical, responsive, figure and schema results are the lead's fresh runs, read from the JSON files. I verified them only through the 4 screenshots and the text scans above.
- **Left closed:** the primary-source folders, `page-r3-frozen.html`, the prompt and response logs, and the earlier attempt's files.