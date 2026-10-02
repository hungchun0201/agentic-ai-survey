# Survey acceptance record / Survey 驗收紀錄

Audit date: 2026-10-02. Artifact: [bilingual survey](../index.html). Delivery format: bilingual HTML with original paper figures, concept diagrams and rendered mathematics.

## Research scope / 研究範圍

The [primary corpus](paper-corpus.json) contains 60 full-primary papers. The SIGCOMM 2022–2026 satellite-centric census contains eleven main-track papers, with annual counts 1/0/0/6/4. Loon and the low-altitude 5G study form two aerial adjacencies. 22 additional terrestrial AI/optical references strengthen the source-specific baseline map. Other requested venues provide curated mechanism coverage. [Evidence adjudication](ADJUDICATION.md) records identities, metrics and physical assumptions. Programme-only BIER-DC and metadata-level SECO retain their respective source tiers.

全文證據庫共 60 篇。SIGCOMM 五年衛星主會議論文為十一篇，各年度 1／0／0／6／4；Loon 與 low-altitude 5G study 另列空中相鄰系統。新增 22 篇地面 AI／光學參照強化具名 baselines，其餘會議以代表性機制整理。

## Verification / 驗證

| Gate | Result | Evidence |
|---|---|---|
| Original paper figures | 60/60 pass | [Figure report](figure-qa.json), crop/reader provenance, source credits and full-resolution links |
| Structured extraction | 60 records; 0 schema errors | [Schema report](schema-qa.json), 5 existing-schema advisories |
| Bilingual content | 15 core sections; 60 primary analyses | EN/ZH attributes, language round trips and visible-text scans |
| Concept visuals | 15 framed diagrams; 18 SVG panels | Browser containment/collision measurements and screenshots |
| Mathematics | 43 rendered equation blocks; 0 formula errors | Local KaTeX 0.16.21, source anchors, domains, units and worked arithmetic |
| Responsive layout | 16 cells pass; 2 desktop typography checks | [Browser report](responsive-qa.json), Chromium/WebKit, 375/414/768/1440 px, EN/ZH |
| Diagram typography | Mobile ≥9 px; 1200 px desktop ≥12 px | Computed SVG text geometry |
| Runtime | 0 exceptions; 60 complete source images | Browser measurements and bundled assets |
| Authored prose | 0 excluded lexical matches | [Lexical report](lexical-qa.json), HTML/translations/captions/SVG/corpus/extractions/QA prose |

## Independent review / 獨立審查

The initial 37-paper snapshot received technical-agent scores 8.8 then 9.3 and code score 9.6. Those reports describe that historical snapshot. The user’s current acceptance gate uses an actual Claude CLI invocation with the Fable model alias; the runtime reports claude-fable-5-1.

Actual Claude Fable round 4: **9.3/10, PASS**. [Review report](claude-fable-review-r4.md) and [provenance](claude-fable-provenance.json) identify the inspected snapshot.

實際 Claude Fable 第 4 輪為 **9.3/10，PASS**；review report 與 provenance 記錄審查 snapshot。

The [current code review](code-review-fable.md) scores **9.6/10, APPROVE** and inspects assembly/export, bilingual state, source escaping and responsive behavior. Publication uses the accepted page hash and completed source/visual/lexical gates.

## Snapshot and literal scope / Snapshot 與原文範圍

Page SHA-256: `1f54e484420d7b88d7206ccaf906028f75915e9fa64c1317337dde266ed23aeb`.

Exact primary-paper titles, original image labels, code/protocol/math literals and schema sentinels preserve technical spelling. Authored image-alt prefixes, captions, bilingual prose and concept labels pass the lexical scan. Full-text algorithm/evaluation claims use the recorded source version; venue identity uses the official programme. Array and terminal sensitivity values carry explicit assumed-parameter labels.

原始題名、原圖文字與技術 literal 保留來源拼字；caption、雙語文句與概念圖文字通過詞彙檢查。算法與評估主張採已記錄全文版本，會議身分採官方 programme。Array 與 terminal sensitivity 參數明列其假設來源。

## Venue-record addendum / 頂會紀錄增補（2026-10-02）

This addendum covers one edit made after the round-four acceptance: the page's opening now derives
its argument from the top-venue publication record. The edit adds a section, `#venue-record`, with
its own nav entry, five subsections, four tables and one concept diagram; it adds a zero-background
opening paragraph and a forward pointer to the existing `#thesis` section; and it adds two evidence
files. No paper record, figure, equation or existing section text was removed or renumbered, so the
60-paper corpus, the 60 figures and the 43 equation blocks are unchanged.

本增補涵蓋第四輪驗收之後的一項修改：頁面開頭現以頂會出版紀錄推導其論證。該修改新增 `#venue-record`
章節與其導覽項目，含五個小節、四張表與一張概念圖；在既有 `#thesis` 章節加入一段零背景開場與指向新章節的
指引；並新增兩個 evidence 檔案。未刪除或重新編號任何論文紀錄、圖、方程式或既有章節文字，
因此 60 篇語料、60 張圖與 43 個方程式區塊維持不變。

| Gate | Result | Evidence |
|---|---|---|
| Programme screen | 5 programme years screened; per-year counts re-derived | [program-screen.json](program-screen.json), with the classification rule, per-title labels, source URLs and the zero-year double check |
| Source identity for added names | 36 entries, each confirmed on an official programme page or through Crossref | [venue-record-sources.json](venue-record-sources.json), with the tier each entry enters at and two recorded limits |
| Census reproduction | 1/0/0/6/4 reproduced from official pages; 2023 and 2024 confirmed against a second official page each | [adjudication addendum](ADJUDICATION.md) |
| Corpus consistency | 60 corpus records, 60 page cards and 60 manifest ids still agree; 0 dangling in-page anchors | structural check over the rendered page |
| Bilingual completeness | 3,160 translation nodes, every one carrying both languages; 288 new strings | structural check |
| Traditional Chinese | 0 Simplified characters in the new prose, under an OpenCC `s2t` round trip restricted to characters absent from the accepted snapshot | structural check |
| Responsive layout | 12 cells pass: Chromium and WebKit, 375/768/1440 px, EN and ZH | no horizontal overflow, 60 of 60 images decoded, 43 of 43 equation blocks rendered, 0 page exceptions |
| Diagram typography | Smallest diagram text 17 units in a 520-unit viewBox, which is above the 9 px floor at 375 px | measured through the SVG scale rather than the declared font size |

### Scope of the new claims / 新主張的範圍

The section's central observation is an absence, and it is stated only at the scope that was
screened: no SIGCOMM main-track paper from 2022 to 2026 joins the satellite track to the AI-fabric
track. The section states in the same place that two main-track papers at other venues, ACM
Multimedia 2025 and SenSys 2026, serve a large vision-language model across a satellite-to-ground
link, that three further peer-reviewed results sit outside the screened venues, and that the
inter-satellite case is occupied at preprint and workshop tier. The communications journals, the
parallel-computing conferences, the space-systems venues and the delay-tolerant-networking standards
line were not screened, and the section says so.

本節的核心觀察是一項缺席，而它只在已篩查的範圍內陳述：2022 至 2026 年沒有任何 SIGCOMM 主會議論文
把衛星軌跡與 AI fabric 軌跡接起來。同一處並陳述：其他場域有兩篇主會議論文（ACM Multimedia 2025 與
SenSys 2026）在衛星對地面鏈路上服務大型 vision-language model；另有三項同儕審查成果位於已篩查場域之外；
而 inter-satellite 的情形則由 preprint 與 workshop 層級占位。通訊期刊、平行運算會議、太空系統場域與
delay-tolerant networking 標準線並未篩查，本節亦明白陳述此點。

### Independent review of this addendum / 本增補的獨立審查

An independent model reviewed the new section in both languages against the evidence files and
returned **FAIL** with a located list: a wrong column reference, two numbers presented without their
experimental conditions, an unlabelled dispersion, an imprecise order-of-magnitude statement, four
claims that reached beyond the reviewed corpus, numbers quoted from papers with no corpus record,
acronyms unexplained on first use, two overloaded paragraphs, and calqued Chinese. Every item was
either fixed or explicitly declined with a reason. The report and the response are recorded in
[the review file](venue-record-review-sol.md).

一個獨立模型以雙語章節與 evidence 檔案為對象進行審查，結論為 **FAIL**，並列出逐項問題：欄位指涉錯誤、
兩個數字未附實驗條件、未標示的離散量、數量級敘述不精確、四處超出已審閱 corpus 範圍的主張、引用了沒有
corpus 紀錄的數字、首次出現未展開的縮寫、兩段內容過載，以及翻譯腔的中文。每一項都已修正，或明確說明不採納
的理由；報告與回應記錄於[審查檔案](venue-record-review-sol.md)。

### Snapshot after this addendum / 增補後的 snapshot

Page SHA-256: `03d2ccf6d4db15fd1a1838a83a180e1866c3be61ca303da34d04817543e307d5`. The hash on record above belongs to the round-four snapshot and is kept for provenance.

本增補後的頁面 SHA-256 為 `03d2ccf6d4db15fd1a1838a83a180e1866c3be61ca303da34d04817543e307d5`；上方記錄的 hash 屬於第四輪 snapshot，保留供溯源。
