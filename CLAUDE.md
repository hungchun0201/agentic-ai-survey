# CLAUDE.md — agentic-ai-survey-deploy

## Project Overview
GitHub Pages site for agentic AI survey. Deployed at `https://hungchun0201.github.io/agentic-ai-survey/`.

## Key Directories
- `papers/continuum/index.html` — Continuum implementation analysis (i18n EN/ZH)
- `papers/continuum/execution-note.html` — Execution note: hands-on experiments & verification
- `ai-infra-basics/vllm/scheduler.html` — vLLM v1 scheduler deep dive

## Style & Conventions
- **Full guide: `PAPER_PAGE_GUIDE.md`** — the single authoritative reference for creating paper pages (CSS, HTML structure, i18n, content depth, workflow, checklist). Read it before creating any new paper page.
- Dark theme (`#0e0b12`), all CSS embedded in `<style>` tag per page (no external CSS)
- Bilingual: use `<span class="i18n" data-en="..." data-zh="...">default text</span>`
- File paths and code values (e.g., `None`, `find`, `pytest`) should NOT be translated
- Use `<code style="background:rgba(233,69,96,.12);border:1px solid rgba(233,69,96,.3);color:#e94560;padding:2px 8px;border-radius:4px">` for paper-modified file paths (red)
- Use `<code style="background:rgba(166,227,161,.1);border:1px solid rgba(166,227,161,.3);color:#a6e3a1;padding:2px 8px;border-radius:4px">` for external file paths (green)
- No ASCII art — use HTML elements (`.vflow`, `.flow`, `.tbar`, `.diagram`, `.cards`)
- **Paper figures & LaTeX**: Use skill `embed-paper-figures` (`.claude/skills/embed-paper-figures/SKILL.md`) when embedding original paper figures or converting math to KaTeX. Key rules: white `background:#fff` on all images, `fig-sm` for oversized figures, KaTeX CDN for LaTeX.
- File path references: always use full paths (e.g., `vllm/v1/core/sched/scheduler.py` not `scheduler.py`)

