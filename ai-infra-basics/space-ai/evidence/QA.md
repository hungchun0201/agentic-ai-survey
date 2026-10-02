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
