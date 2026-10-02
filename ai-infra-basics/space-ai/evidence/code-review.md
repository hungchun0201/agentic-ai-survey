# Orbital AI survey code review

Code review score: **9.6 / 10**. Verdict: **APPROVE**. The reviewed page passes language round trips, equation rendering, asset resolution, and mobile layout checks. The language controls expose their selected state to assistive technology.

Review scope: the new bilingual page, its embedded JavaScript, the staging assembler, and the English and Chinese homepage cards. This review evaluates code behavior and security boundaries; the companion technical review evaluates research claims and content coverage.

## Resolved accessibility finding

File: `ai-infra-basics/space-ai/index.html:520`

Assembler: `authoring-stage/assemble-page.py:191` and `:252`.

The selected language link now carries `aria-current="true"` in both the initial HTML and the live language-switch state. Browser checks confirm that the selected control exposes this state and the companion control returns to its ordinary link state. The homepage backlink follows the selected language, directing English readers to `index-en.html` and Chinese readers to `index-zh.html`.

Open actionable findings: **0**.

## Resolved final delta findings

The linked `evidence/QA.md` artifact and companion `evidence/ADJUDICATION.md` now exist in the generated page directory. Every local evidence link resolves.

All thirty-seven original figures now use the code literal `loading="lazy"`. Browser validation requests eager loading exclusively within its test session, then decodes all thirty-seven images successfully. This preserves deferred production transfers and complete image verification.

## Verification evidence

- Read staged and working-tree diffs. The homepage change adds one survey card in each language; each target resolves to the new page.
- Read the assembler and page structure. Translation HTML originates in local author packages, attribute values pass through HTML escaping, paper titles pass through text escaping, and the embedded JSON escapes closing script delimiters. The reviewed browser DOM contains zero executable translation fragments.
- JavaScript syntax validation passes through `node --check`.
- Chrome renders all twelve KaTeX equations with zero formula errors and zero page exceptions.
- Repeated English–Chinese–English transitions restore the English translation DOM exactly. The document language and title follow each selected language.
- Every section fragment and every bundled script, stylesheet, image, and full-resolution figure link resolves. All thirty-seven original paper images decode successfully. The linked QA artifact resolves to its restored evidence record.
- Viewports of 320, 390, 768, and 1440 pixels retain the viewport width. The sticky language controls remain visible; diagrams, sections, and figures fit within the viewport.
- Final delta checks confirm TACCL and TopoOpt receive the terrestrial T family in the census, appendix and bibliography. The terrestrial-reference SVG translates cleanly and its text fits the viewbox in each language. All 1,902 translation elements carry both language attributes.
- The three original empty source links for `planet-iot` received canonical URLs in the latest rebuild. This repair closes the earlier source-navigation finding.

Snapshot SHA-256: `b76825643c6d41ebfeb75409669342c039caf3bf73367cffc5ecf666f077d042`.

Final publication normalization trims whitespace from CSS blank lines. This formatting adjustment preserves page content and JavaScript behavior. The final sixteen browser, viewport and language validation cells pass.

## Artifact QA

The report source received a case-insensitive English lexical scan and a Chinese character scan. Excluded prose matches: **0**. Exact code and protocol attributes retain their technical spelling. The report artifact is Markdown; its source carries the headings, evidence list, and summary table.

## Review Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0 | pass |
| HIGH | 0 | pass |
| MEDIUM | 0 | pass |
| LOW | 0 | pass |

Verdict: **APPROVE** — language, math, diagram, figure-link, evidence-access and deferred-loading checks pass.
