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
## 寫作規則（2026-10-02 擁有者指令，優先於其他風格指引）

頁面上的文字是一篇給人讀的文章。目標是讀者一路讀下去就懂這件事在幹嘛。

**內容**
- 直接寫結論與事實。2023 年零篇就寫零篇。
- 查核、審閱、普查、驗證這類工作過程留在 evidence 檔案裡，文章裡一個字都不要出現。
- `corpus` 這個詞禁止出現在文章中。要講論文就講論文。
- 文章服務的是讀者想知道的事，不是我做了什麼。

**句式**
- 嚴格禁止大量使用分號、冒號、破折號。能用句號分成兩句就分成兩句。
- 嚴格限制否定句。禁止「不是…而是…」「並非」「不能」這類句型。把正確的講出來就好。
- 嚴禁預設讀者會在哪裡理解錯，再去否定那個錯誤。那是稻草人，浪費讀者時間。
- 短句優先。一句話講一件事。

**結構**
- 先給全貌，再給細節，最後給意涵。
- 每一節回答一個讀者會問的問題。
- 表格之前先用一段話說明這張表在回答什麼。

## Writing rules (owner instruction, 2026-10-02, outranks other style guidance)

Page text is an article for a human to read. A reader should follow it straight through.

- State conclusions and facts directly. Zero papers in 2023 means write zero.
- Keep auditing, reviewing, census and verification work inside the evidence files. None of it belongs in the article.
- The word `corpus` is banned from article text. Write about papers.
- Strictly limit semicolons, colons and em-dashes. Two sentences beat one joined sentence.
- Strictly limit negation. Avoid "X is not Y but Z", "fails to", "does not". State the correct thing.
- Never set up a reader misconception and then knock it down.
- Short sentences. One idea each.
- Whole picture first, then detail, then what it means. Every section answers one reader question. Every table gets a sentence of lead-in.

<!-- ARIS:BEGIN -->
## ARIS Skill Scope
ARIS skills installed in this project: 81 entries.
Manifest: `.aris/installed-skills.txt` (lists every skill ARIS installed and its upstream target).
For ARIS workflows, prefer the project-local skills under `.claude/skills/` over global skills.
Do not modify or delete files inside any skill that is a symlink (symlinks point into `/home/hclin/aris_repo`).
Update with: `bash /home/hclin/aris_repo/tools/install_aris.sh`  (re-runnable; reconciles new/removed skills).
<!-- ARIS:END -->
