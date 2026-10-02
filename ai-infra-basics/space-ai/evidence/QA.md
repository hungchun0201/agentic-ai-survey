# Survey acceptance record / Survey 驗收紀錄

Audit date: 2026-10-02. Artifact: [bilingual survey](../index.html). The source and rendered HTML are the delivery formats. 本次交付為中英雙語 HTML，包含原始論文圖、概念圖與公式。

## Research scope / 研究範圍

The [primary corpus](paper-corpus.json) contains 37 papers with full-text technical extraction, source anchors, figure provenance and asset hashes. The scoped SIGCOMM census covers every satellite-centric main-track paper in 2022–2026: eleven papers, plus Loon as an adjacent stratospheric system. The other requested venues provide a curated mechanism map. [Evidence adjudication](ADJUDICATION.md) records identity, metric scope and physical assumptions. Programme-only BIER-DC and publisher-metadata SECO carry their respective evidence tiers outside the full-primary corpus.

37 篇全文分析包含 problem、design、model、evaluation、baseline、result 與 evidence boundary。SIGCOMM 2022–2026 的衛星核心題目完整收錄十一篇；Loon 另列平流層系統。其他會議採代表性機制整理。BIER-DC 與 SECO 保留 programme 與 metadata 證據層級。

## Verification / 驗證

| Gate | Result | Reproduction evidence |
|---|---|---|
| Original paper figures | 37 / 37 pass | [Figure report](figure-qa.json); primary PDF crops or public ACM eReader crops; full-resolution links and source credits |
| Structured extraction | 37 records; 0 schema errors | [Schema report](schema-qa.json); 5 existing-schema advisory entries |
| Bilingual content | 15 core sections; 37 paper analyses | EN/ZH translation attributes and language round trips |
| Concept figures | 12 SVGs | Text containment, collision checks and rendered screenshots |
| Mathematics | 12 rendered equations; 0 formula errors | Local KaTeX 0.16.21; variable domains, units and worked arithmetic |
| Responsive layout | 16 browser/viewport/language cells pass | [Responsive report](responsive-qa.json); Chromium and WebKit; widths 375, 414, 768 and 1440 px; EN/ZH |
| Diagram typography | At least 9 px at mobile; at least 12 px at 1200 px | Computed SVG text geometry |
| Page behavior | 0 runtime exceptions | Language state, document language, homepage backlink, fragment targets and bundled assets |
| Figure loading | Deferred below-fold loading | Browser checks explicitly request all assets during validation |
| Affirmative prose | 0 excluded authored-prose matches | [Lexical report](lexical-qa.json); case-insensitive English and Chinese-character scan |

## Independent review / 獨立審查

[Technical round 1](technical-review-r1.md) scored 8.8/10. Its required revisions concerned executable terrestrial comparators, beginner vocabulary and optimization variable domains. The current artifact adds NCCL, TACCL, TopoOpt and OrbitalBrain comparison rules, an early bilingual glossary and explicit A3 domains. [Technical round 2](technical-review-r2.md) scores **9.3/10**, with a **PASS** verdict. [Code review](code-review.md) scores **9.6/10**, with an **APPROVE** verdict and zero actionable findings. Publication follows the user’s 9/10 technical acceptance threshold.

第一輪技術審查為 8.8/10，修訂包含具名地面 baselines、前置術語表與 A3 variable domains。第二輪技術審查為 **9.3/10，PASS**，程式審查為 **9.6/10，APPROVE**；發布採使用者指定的 9/10 技術驗收門檻。

## Prose and literal audit / 文句與原文稽核

The lexical gate scans visible HTML prose, both translation attributes, authored captions and image descriptions, concept SVG labels, bilingual corpus fields, structured-extraction prose and this evidence directory’s Markdown reports. Exact primary-paper titles and original paper-image labels retain their source spelling and quotation annotations. Mathematical/code identifiers, schema-required sentinel values and the bundled MIT software license retain their technical literals. The delivery format uses HTML; the rendered text scan follows browser text and translation attributes.

文句檢查涵蓋可見 HTML、中英 translation attributes、caption、概念圖文字、corpus、extraction 與 QA Markdown。原始題名及原圖保留 source quotation 標記；公式與程式符號、schema sentinel 與 MIT license 保留技術原文。掃描結果記錄於 lexical report。
