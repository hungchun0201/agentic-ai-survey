# CLAUDE.md — agentic-ai-survey-deploy

## Project Overview
GitHub Pages site for agentic AI survey. Deployed at `https://hungchun0201.github.io/agentic-ai-survey/`.

## Key Directories
- `papers/continuum/index.html` — Continuum implementation analysis (i18n EN/ZH)
- `papers/continuum/execution-note.html` — Execution note: hands-on experiments & verification
- `ai-infra-basics/vllm/scheduler.html` — vLLM v1 scheduler deep dive

## Style & Conventions
- **Skill `paper-page`** (`.claude/skills/paper-page/SKILL.md`) — the single authoritative reference for creating/updating paper pages. Covers CSS, HTML structure, i18n, content methodology, paper figures, KaTeX LaTeX, and quality checklist. Read it before creating any new paper page.
- Also see `PAPER_PAGE_GUIDE.md` for legacy reference (the skill supersedes it).
- Dark theme (`#0e0b12`), all CSS embedded in `<style>` tag per page
- Bilingual: `<span class="i18n" data-en="..." data-zh="...">default text</span>`
- File paths and code values should NOT be translated
- No ASCII art — use HTML elements (`.vflow`, `.flow`, `.tbar`, `.diagram`, `.cards`)
- Paper figures: white `background:#fff` on all images, `fig-sm` for oversized, KaTeX CDN for LaTeX
- File path references: always use full paths (e.g., `vllm/v1/core/sched/scheduler.py` not `scheduler.py`)

