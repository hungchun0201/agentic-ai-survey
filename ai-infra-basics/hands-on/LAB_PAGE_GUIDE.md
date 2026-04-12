# Hands-On Lab Page Guide — AI Inference Infrastructure

> **Coding agent 必讀**：為某一週的實驗建立獨立頁面前，請先完整閱讀本文件。所有實驗頁面必須遵循此規範。
> 參考範本：`hands-on/index.html`（目前的單頁版本，各週內容段落即為範本素材）

---

## 1. Overview

### What This Guide Is For

This is the single, authoritative guide for creating **individual hands-on lab pages** in the AI Inference Infrastructure course. Each of the 16 weekly labs gets its own self-contained HTML page, while `index.html` serves as the hub/overview page linking to them all.

This guide covers both **style conventions** (CSS, HTML structure, i18n) and **content methodology** (what sections to include, how deep to go, expected components per lab).

### Quality Expectations

- **Minimum length:** 250 lines of HTML
- **Target length:** 350–600 lines (larger for labs with many experiments or extra background)
- **Maximum length:** ~800 lines (avoid padding; every line should carry information)
- **Self-contained:** Single `.html` file with all CSS inlined in a `<style>` block. No external CSS, no JavaScript libraries, no images.
- **Dark theme only:** All pages use the canonical hands-on dark theme defined in this guide.
- **Bilingual (i18n):** All user-visible text must have EN/ZH translations.
- **Copy-pasteable commands:** All experiment commands should be ready to paste into a terminal.
- **Technical depth:** The page should enable a graduate student to complete the lab independently.

### Design Philosophy

Each lab page follows a **measure-first, understand-second** approach:

1. **Run experiments** — observe a phenomenon
2. **Collect metrics** — quantify the effect
3. **Read source code** — understand the mechanism
4. **Write analysis** — synthesize understanding

The page structure mirrors this workflow.

---

## 2. File Structure

```
ai-infra-basics/hands-on/
├── index.html              ← Hub page: course overview, roadmap, env setup, links to each week
├── LAB_PAGE_GUIDE.md       ← This guide
├── week-01.html            ← Week 1: First LLM Serving
├── week-02.html            ← Week 2: Offline Throughput & Profiling
├── ...
└── week-16.html            ← Week 16: Disaggregated P/D
```

- 每週實驗一個 HTML 檔案，命名用 `week-NN.html`（zero-padded two digits）
- 一個 HTML 檔案 = 一個完整頁面，**不使用外部 CSS/JS 檔案**，所有樣式寫在 `<style>` 標籤內
- `index.html` 保留為課程總覽 + 環境設定 + 路線圖頁面，每週卡片加上連結指向 `week-NN.html`

---

## 3. HTML Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Week N — 實驗標題 | Hands-On Labs</title>
  <style>
    /* 完整 CSS 嵌入此處（見第 4 節） */
  </style>
</head>
<body>

  <!-- 1. 頂部導航列 -->
  <nav>...</nav>

  <!-- 2. Hero 區塊 -->
  <section class="hero">...</section>

  <!-- 3. 主內容 -->
  <div class="container">
    <div class="section" id="section-id">...</div>
    <!-- 更多 section -->
  </div>

  <!-- 4. 頁尾 -->
  <footer>...</footer>

  <!-- 5. i18n 切換腳本 -->
  <script>
    function setLang(l){document.querySelectorAll('.i18n').forEach(function(e){if(e.dataset[l])e.innerHTML=e.dataset[l]});document.getElementById('lang-en').classList.toggle('active',l==='en');document.getElementById('lang-zh').classList.toggle('active',l==='zh');localStorage.setItem('lang',l)}
    (function(){var l=localStorage.getItem('lang');if(l)setLang(l)})();
  </script>
</body>
</html>
```

---

## 4. CSS Specification

### 4.1 Theme System

Hands-on lab pages use a **blue-toned dark theme** (`#16213e` base), distinct from the paper pages' `#0e0b12` base. This gives the hands-on section its own visual identity.

Each lab page uses a **phase accent color** to indicate which course phase it belongs to:

| Phase | Weeks | `--phase` | `--phase-rgb` | Theme |
|-------|-------|-----------|---------------|-------|
| **Phase 1** | 1–3 | `#54a0ff` | `84,160,255` | Foundations & Benchmarking |
| **Phase 2** | 4–6 | `#2ecc71` | `46,204,113` | Memory & KV Cache |
| **Phase 3** | 7–9 | `#f5a623` | `245,166,35` | Scheduling & Batching |
| **Phase 4** | 10–12 | `#9b59b6` | `155,89,182` | Optimizations |
| **Phase 5** | 13–16 | `#00d2d3` | `0,210,211` | Multi-GPU & System Integration |

在 CSS 中透過 `--phase` 和 `--phase-rgb` 變數控制 hero gradient、section-label、step-num 色彩。

### 4.2 Complete CSS (directly copy into `<style>`)

```css
/* ===== PHASE ACCENT (change per lab — see Section 4.1) ===== */
:root {
  --dark: #16213e; --mid: #0f3460;
  --phase: #54a0ff;                    /* 按 phase 選色 */
  --phase-rgb: 84,160,255;            /* 同色 RGB */
  --green: #2ecc71; --amber: #f5a623; --purple: #9b59b6; --cyan: #00d2d3;
  --blue: #54a0ff; --code-bg: #1e1e2e; --text: #e0e0e0; --text-muted: #a0aec0;
  --border: #2d3e5e; --surface: #1e2d4a; --card-bg: #1a2744;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',system-ui,-apple-system,sans-serif; background:var(--dark); color:var(--text); line-height:1.7; }

/* ===== STICKY NAV ===== */
nav { position:sticky; top:0; z-index:1000; background:rgba(22,33,62,0.95); backdrop-filter:blur(12px); border-bottom:1px solid rgba(var(--phase-rgb),0.25); padding:0 2rem; }
nav ul { display:flex; list-style:none; max-width:1200px; margin:0 auto; gap:0.25rem; overflow-x:auto; scrollbar-width:none; }
nav ul::-webkit-scrollbar { display:none; }
nav ul li a { display:block; padding:0.85rem 1rem; color:var(--text-muted); text-decoration:none; font-size:0.85rem; font-weight:500; white-space:nowrap; transition:color .2s,border-bottom .2s; border-bottom:2px solid transparent; }
nav ul li a:hover, nav ul li a.active { color:#fff; border-bottom:2px solid var(--phase); }
.lang-switch { margin-left:auto; display:flex; align-items:center; gap:6px; list-style:none; }
.lang-switch a { color:rgba(255,255,255,.7); text-decoration:none; padding:4px 12px; border-radius:14px; font-size:.78rem; border:1px solid rgba(255,255,255,.3); transition:all .2s; cursor:pointer; }
.lang-switch a:hover, .lang-switch a.active { color:#fff; background:rgba(255,255,255,.2); border-color:rgba(255,255,255,.5); }
.week-nav { display:flex; gap:4px; margin-left:auto; }
.week-nav a { color:var(--text-muted); text-decoration:none; padding:4px 10px; border-radius:4px; font-size:.82rem; transition:all .2s; }
.week-nav a:hover { color:#fff; background:rgba(var(--phase-rgb),.15); }

/* ===== HERO ===== */
.hero { background:linear-gradient(135deg,var(--dark) 0%,var(--mid) 40%,#1a1a3e 70%,var(--dark) 100%); padding:4rem 2rem 3rem; text-align:center; position:relative; overflow:hidden; }
.hero::before { content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%; background:radial-gradient(circle at 30% 50%,rgba(var(--phase-rgb),0.06) 0%,transparent 50%),radial-gradient(circle at 70% 50%,rgba(0,210,211,0.06) 0%,transparent 50%); animation:rotateBg 30s linear infinite; }
@keyframes rotateBg { to { transform:rotate(360deg); } }
.hero h1 { font-size:2.4rem; font-weight:800; position:relative; color:#fff; margin-bottom:0.5rem; }
.hero h1 span { color:var(--phase); }
.hero .subtitle { font-size:1.05rem; color:var(--text-muted); position:relative; max-width:700px; margin:0 auto; }
.hero .badges { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; position:relative; margin-top:1.2rem; }
.hero .badge { display:inline-block; background:rgba(var(--phase-rgb),0.15); border:1px solid rgba(var(--phase-rgb),0.3); color:var(--phase); padding:0.3rem 0.9rem; border-radius:20px; font-size:0.8rem; font-weight:600; }

/* ===== CONTAINER ===== */
.container { max-width:1100px; margin:0 auto; padding:2rem; }

/* ===== SECTIONS ===== */
.section { margin-bottom:3rem; }
.section-label { display:inline-block; background:rgba(var(--phase-rgb),0.12); color:var(--phase); font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:0.25rem 0.75rem; border-radius:4px; margin-bottom:0.75rem; }
h2 { font-size:1.9rem; font-weight:700; color:#fff; margin-bottom:1rem; }
h2.section-title { position:relative; display:inline-block; }
h2.section-title::after { content:''; position:absolute; bottom:-4px; left:0; width:100%; height:3px; background:linear-gradient(90deg,var(--phase),var(--cyan)); border-radius:2px; }
h3 { font-size:1.35rem; font-weight:600; margin-bottom:0.75rem; color:var(--blue); }
h4 { font-size:1.1rem; font-weight:600; margin-bottom:0.5rem; color:var(--cyan); }
p { margin-bottom:1rem; }
a { color:var(--cyan); text-decoration:none; }
a:hover { text-decoration:underline; }

/* ===== CARDS ===== */
.card { background:var(--card-bg); border:1px solid var(--border); border-radius:12px; padding:1.75rem; margin-bottom:1.5rem; }
.card.highlight-blue { border-left:4px solid var(--blue); }
.card.highlight-green { border-left:4px solid var(--green); }
.card.highlight-amber { border-left:4px solid var(--amber); }
.card.highlight-purple { border-left:4px solid var(--purple); }
.card.highlight-cyan { border-left:4px solid var(--cyan); }
.card.highlight-orange { border-left:4px solid #ffa500; }
.card.highlight-red { border-left:4px solid #e74c3c; }

/* ===== CODE BLOCKS ===== */
pre { background:var(--code-bg); border:1px solid var(--border); border-radius:8px; padding:1.25rem; overflow-x:auto; font-size:0.82rem; line-height:1.65; margin-bottom:1.5rem; font-family:'Consolas','Fira Code',monospace; }
code { font-family:'Consolas','Fira Code',monospace; font-size:0.85em; }
p code, li code, td code { background:rgba(0,210,211,0.1); color:var(--cyan); padding:0.15rem 0.4rem; border-radius:4px; }
.kw{color:#c678dd} .fn{color:#61afef} .cl{color:#e5c07b} .st{color:#98c379} .cm{color:#5c6370;font-style:italic} .op{color:#56b6c2} .nb{color:#e06c75} .nr{color:#d19a66}

/* ===== TABLES ===== */
table { width:100%; border-collapse:collapse; margin-bottom:1.5rem; font-size:0.88rem; }
th,td { padding:0.65rem 1rem; text-align:left; border-bottom:1px solid rgba(var(--phase-rgb),0.25); }
th { background:var(--surface); color:var(--phase); font-weight:600; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; }
tr:hover { background:rgba(var(--phase-rgb),0.04); }
div[style*="overflow-x"] { -webkit-overflow-scrolling:touch; }

/* ===== STEP FLOW (experiment steps) ===== */
.step-flow { display:flex; flex-direction:column; gap:0; }
.step { position:relative; padding:1.5rem 1.8rem 1.5rem 4rem; background:var(--card-bg); border:1px solid var(--border); border-radius:10px; margin-bottom:0.5rem; transition:all .3s; }
.step:hover { border-color:rgba(var(--phase-rgb),.25); background:var(--surface); }
.step-num { position:absolute; left:1.2rem; top:1.5rem; width:2rem; height:2rem; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.85rem; color:#fff; }
.step-num.s1 { background:linear-gradient(135deg,#54a0ff,#2e86de); }
.step-num.s2 { background:linear-gradient(135deg,#2ecc71,#27ae60); }
.step-num.s3 { background:linear-gradient(135deg,#f5a623,#e09200); }
.step-num.s4 { background:linear-gradient(135deg,#9b59b6,#8e44ad); }
.step-num.s5 { background:linear-gradient(135deg,#00d2d3,#01a3a4); }
.step-num.s6 { background:linear-gradient(135deg,#e74c3c,#c0392b); }

/* ===== CALLOUTS ===== */
.callout { border-left:4px solid var(--phase); background:rgba(var(--phase-rgb),0.06); padding:1rem 1.25rem; border-radius:0 8px 8px 0; margin-bottom:1.5rem; }
.callout.warn { border-left-color:var(--amber); background:rgba(245,166,35,0.06); }
.callout.key { border-left-color:var(--green); background:rgba(46,204,113,0.06); }
.callout.critical { border-left-color:#e74c3c; background:rgba(231,76,60,0.06); }
.callout strong { color:var(--phase); }
.callout.key strong { color:var(--green); }
.callout.warn strong { color:var(--amber); }
.callout.critical strong { color:#e74c3c; }

/* ===== PHASE BADGE ===== */
.phase-badge { display:inline-block; padding:0.2rem 0.6rem; border-radius:4px; font-size:0.72rem; font-weight:700; letter-spacing:0.04em; margin-bottom:0.4rem; }
.phase-badge.p1 { background:rgba(84,160,255,.15); color:#54a0ff; border:1px solid rgba(84,160,255,.3); }
.phase-badge.p2 { background:rgba(46,204,113,.15); color:#2ecc71; border:1px solid rgba(46,204,113,.3); }
.phase-badge.p3 { background:rgba(245,166,35,.15); color:#f5a623; border:1px solid rgba(245,166,35,.3); }
.phase-badge.p4 { background:rgba(155,89,182,.15); color:#9b59b6; border:1px solid rgba(155,89,182,.3); }
.phase-badge.p5 { background:rgba(0,210,211,.15); color:#00d2d3; border:1px solid rgba(0,210,211,.3); }

/* ===== FILE TAG ===== */
.file-tag { display:inline-block; background:rgba(84,160,255,.12); border:1px solid rgba(84,160,255,.25); color:var(--blue); padding:.15rem .5rem; border-radius:4px; font-size:.75rem; font-family:'JetBrains Mono','Consolas',monospace; margin-bottom:.4rem; }

/* ===== GRIDS ===== */
.grid-2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:1.2rem; margin:1rem 0; }
.grid-3 { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; margin:1rem 0; }

/* ===== LISTS ===== */
ul, ol { margin:0 0 1rem 1.5rem; }
li { margin-bottom:0.35rem; }

/* ===== FOOTER ===== */
footer { background:var(--dark); border-top:1px solid var(--border); padding:2rem; text-align:center; color:var(--text-muted); font-size:.85rem; margin-top:3rem; }
footer a { color:var(--cyan); }
.footer-nav { display:flex; justify-content:space-between; max-width:600px; margin:0 auto 1rem; }
.footer-nav a { color:var(--phase); font-weight:600; text-decoration:none; }
.footer-nav a:hover { text-decoration:underline; }

/* ===== RESPONSIVE ===== */
@media(max-width:768px) {
  .hero h1 { font-size:1.8rem; } .container { padding:1rem; } .card { padding:1.25rem; }
  pre { font-size:.75rem; padding:1rem; } .grid-2,.grid-3 { grid-template-columns:1fr; }
  .step { padding-left:3.5rem; }
}
@media(max-width:600px) {
  .hero h1 { font-size:1.5rem; } .hero .subtitle { font-size:.9rem; }
  nav ul { gap:0; } nav ul li a { padding:.7rem .6rem; font-size:.78rem; }
  h2 { font-size:1.5rem; } h3 { font-size:1.15rem; }
  table { font-size:.78rem; } th,td { padding:.45rem .6rem; }
}
```

### 4.3 Phase-to-CSS Variable Mapping

設定 `:root` 時，依據該週所屬 phase 替換 `--phase` 和 `--phase-rgb`：

| Week | Phase | `--phase` | `--phase-rgb` |
|------|-------|-----------|---------------|
| 1–3 | P1 | `#54a0ff` | `84,160,255` |
| 4–6 | P2 | `#2ecc71` | `46,204,113` |
| 7–9 | P3 | `#f5a623` | `245,166,35` |
| 10–12 | P4 | `#9b59b6` | `155,89,182` |
| 13–16 | P5 | `#00d2d3` | `0,210,211` |

不隨 phase 變化的固定色：

| 用途 | 色碼 | 原因 |
|------|------|------|
| 頁面背景 | `#16213e` | 全站 hands-on 統一深藍底 |
| 卡片背景 | `#1a2744` | 全站 hands-on 統一 |
| 程式碼背景 | `#1e1e2e` | 全站統一 |
| 主文字色 | `#e0e0e0` | 全站統一 |
| Learning Objectives 卡片 | `highlight-blue` | 固定語意：學習目標 |
| Source Code Reading 卡片 | `highlight-purple` | 固定語意：原始碼閱讀 |
| Written Analysis 卡片 | `highlight-green` | 固定語意：書面分析 |
| Callout 提示 | `.callout.warn` (amber) | 固定語意：背景知識/提示 |
| Related Deep Dive | `.callout.key` (green) | 固定語意：延伸連結 |

---

## 5. Page Components

### 5.1 Navigation (nav)

```html
<nav><ul>
  <li><a href="index.html">&larr; Hands-On Labs</a></li>
  <li><a href="#objectives">Objectives</a></li>
  <li><a href="#experiments">Experiments</a></li>
  <li><a href="#metrics">Metrics</a></li>
  <li><a href="#source-code">Source Code</a></li>
  <li><a href="#analysis">Analysis</a></li>
  <li class="week-nav">
    <a href="week-NN.html">&larr; Week N-1</a>
    <a href="week-NN.html">Week N+1 &rarr;</a>
  </li>
  <li class="lang-switch">
    <a onclick="setLang('en')" id="lang-en" class="active">EN</a>
    <a onclick="setLang('zh')" id="lang-zh">ZH</a>
  </li>
</ul></nav>
```

Rules:
- 第一個連結**固定**為 `← Hands-On Labs`，指向 `index.html`
- 中間為各 section 的錨點連結
- `.week-nav` 包含前後週連結（Week 1 無 prev；Week 16 無 next）
- 最後為語言切換按鈕（EN/ZH）

### 5.2 Hero Section

```html
<section class="hero">
  <span class="phase-badge pN">PHASE N</span>
  <h1><span class="i18n" data-en="Week N — " data-zh="第 N 週 — ">Week N — </span><span>Topic Name</span></h1>
  <p class="subtitle"><span class="i18n"
    data-en="One-line description of what this lab covers"
    data-zh="此實驗涵蓋內容的一行描述">One-line description of what this lab covers</span></p>
  <div class="badges">
    <span class="badge"><span class="i18n" data-en="3-5 hrs" data-zh="3-5 小時">3-5 hrs</span></span>
    <span class="badge">1× A100 80GB</span>
    <span class="badge">vLLM · SGLang</span>
  </div>
</section>
```

Hero should be scannable in 3 seconds — phase badge, week number + title, subtitle, time/hardware/tools badges.

### 5.3 Section Structure

```html
<div class="section" id="unique-id">
  <span class="section-label"><span class="i18n" data-en="Section Label" data-zh="章節標籤">Section Label</span></span>
  <h2 class="section-title"><span class="i18n" data-en="Section Title" data-zh="章節標題">Section Title</span></h2>
  <!-- 內容 -->
</div>
```

- 每個 section 有唯一 `id`，與 nav 連結對應
- `section-label` 為小型標籤（如 "Experiments", "Source Code"）

### 5.4 Footer

```html
<footer>
  <div class="footer-nav">
    <a href="week-NN.html">&larr; <span class="i18n" data-en="Week N-1: Topic" data-zh="第 N-1 週：主題">Week N-1: Topic</span></a>
    <a href="week-NN.html"><span class="i18n" data-en="Week N+1: Topic" data-zh="第 N+1 週：主題">Week N+1: Topic</span> &rarr;</a>
  </div>
  <p><a href="index.html"><span class="i18n"
    data-en="&larr; Back to Hands-On Labs Overview"
    data-zh="&larr; 返回實作實驗總覽">&larr; Back to Hands-On Labs Overview</span></a></p>
  <p><span class="i18n"
    data-en="Hands-On Labs — AI Inference Infrastructure (16-Week Graduate Course)"
    data-zh="AI 推理基礎設施實作實驗（16 週研究所課程）">Hands-On Labs — AI Inference Infrastructure (16-Week Graduate Course)</span></p>
</footer>
```

---

## 6. Internationalization (i18n)

### 6.1 Basic Usage

All user-visible text must be wrapped in `<span class="i18n">`:

```html
<span class="i18n" data-en="English text" data-zh="中文文字">English text (as default)</span>
```

### 6.2 Content That Should NOT Be Translated

Keep these in their original form:
- File paths (e.g., `vllm/v1/core/scheduler.py`)
- Command names and flags (e.g., `--max-num-seqs`, `benchmark_serving.py`)
- Code keywords and values (e.g., `None`, `True`, `self`)
- Class/function names (e.g., `AsyncLLM`, `EngineCore`)
- Model names (e.g., `meta-llama/Llama-3.1-8B-Instruct`)
- Metrics abbreviations (e.g., TTFT, ITL, tok/s)
- Mathematical formulas and numbers

### 6.3 Embedding HTML Inside i18n

`data-en` / `data-zh` values are set via `innerHTML`, so they can contain HTML tags:

```html
<span class="i18n"
  data-en="Use &lt;code&gt;--enable-prefix-caching&lt;/code&gt; flag"
  data-zh="使用 &lt;code&gt;--enable-prefix-caching&lt;/code&gt; 旗標">
  Use <code>--enable-prefix-caching</code> flag
</span>
```

Note: `<` and `>` must be escaped as `&lt;` / `&gt;` inside `data-*` attributes.

---

## 7. Code Block Syntax Highlighting

No JS highlighting library. Use manual `<span>` classes:

| Class | Purpose | Color |
|-------|---------|-------|
| `.kw` | Keywords (`class`, `def`, `if`, `for`, `do`, `done`) | `#c678dd` (purple) |
| `.fn` | Function/class names | `#61afef` (blue) |
| `.cl` | Class/component names (in diagrams) | `#e5c07b` (yellow) |
| `.st` | Strings | `#98c379` (green) |
| `.cm` | Comments (`#`, `//`) | `#5c6370` (gray, italic) |
| `.op` | Operators, arrows | `#56b6c2` (cyan) |
| `.nb` | Built-in names, errors | `#e06c75` (red) |
| `.nr` | Numbers | `#d19a66` (orange) |

Example:

```html
<pre><code><span class="kw">for</span> rate <span class="kw">in</span> 1 4 10 inf; <span class="kw">do</span>
  python benchmarks/benchmark_serving.py \
    --backend vllm \
    --num-prompts <span class="nr">200</span> \
    --request-rate $rate \
    2&gt;&amp;1 | tee results_rr${rate}.txt
<span class="kw">done</span></code></pre>
```

### Inline Code

Regular inline code inherits `p code` style (cyan tint) automatically. Use `.file-tag` for source file references:

```html
<span class="file-tag">vllm/v1/core/kv_cache_manager.py</span>
```

---

## 8. Component HTML Templates

### 8.1 Learning Objectives Card

**固定使用 `highlight-blue`**。每個 lab 都必須有。

```html
<div class="card highlight-blue">
  <h4><span class="i18n" data-en="Learning Objectives" data-zh="學習目標">Learning Objectives</span></h4>
  <ul>
    <li><span class="i18n" data-en="Objective 1" data-zh="目標 1">Objective 1</span></li>
    <li><span class="i18n" data-en="Objective 2" data-zh="目標 2">Objective 2</span></li>
    <!-- 3-5 objectives per lab -->
  </ul>
</div>
```

### 8.2 Experiment Step Flow

**核心組件** — 每個 lab 的主要實驗以 step-flow 呈現。

```html
<div class="step-flow">
  <div class="step">
    <div class="step-num s1">1</div>
    <h4><span class="i18n" data-en="Step Title" data-zh="步驟標題">Step Title</span></h4>
    <p><span class="i18n" data-en="Optional description" data-zh="選填描述">Optional description</span></p>
    <pre><code>command here</code></pre>
  </div>
  <div class="step">
    <div class="step-num s2">2</div>
    <h4>...</h4>
    <pre><code>...</code></pre>
  </div>
  <!-- Up to 6 steps (s1–s6 colors available) -->
</div>
```

Rules:
- 每個 step 包含：step-num（1-6）、h4 標題、可選 p 描述、pre/code 命令
- 最多 6 步（超過時拆成多個 step-flow 或合併步驟）
- 命令必須 copy-pasteable
- 用 `<span class="cm">` 為命令加註解

### 8.3 Metrics Table

**每個 lab 都必須有。**

```html
<h3><span class="i18n" data-en="Metrics to Collect" data-zh="收集指標">Metrics to Collect</span></h3>
<div style="overflow-x:auto;-webkit-overflow-scrolling:touch">
<table>
  <tr>
    <th><span class="i18n" data-en="Metric" data-zh="指標">Metric</span></th>
    <th><span class="i18n" data-en="Description" data-zh="描述">Description</span></th>
    <th><span class="i18n" data-en="Unit" data-zh="單位">Unit</span></th>
  </tr>
  <tr><td>Metric name</td><td><span class="i18n" data-en="..." data-zh="...">...</span></td><td>ms</td></tr>
</table>
</div>
```

### 8.4 Source Code Reading Card

**固定使用 `highlight-purple`**。每個 lab 都必須有。

```html
<div class="card highlight-purple">
  <h4><span class="i18n" data-en="Source Code Reading" data-zh="原始碼閱讀">Source Code Reading</span></h4>
  <ul>
    <li><span class="file-tag">full/path/to/file.py</span> — <span class="i18n" data-en="Description" data-zh="描述">Description</span></li>
  </ul>
</div>
```

Rules:
- 使用 `.file-tag` 顯示完整檔案路徑
- 每個檔案附簡短描述（閱讀該檔時應關注什麼）

### 8.5 Written Analysis Card

**固定使用 `highlight-green`**。每個 lab 都必須有。

```html
<div class="card highlight-green">
  <h4><span class="i18n" data-en="Written Analysis (1-2 pages)" data-zh="書面分析（1-2 頁）">Written Analysis (1-2 pages)</span></h4>
  <ul>
    <li><span class="i18n" data-en="Analysis question 1" data-zh="分析問題 1">Analysis question 1</span></li>
    <li><span class="i18n" data-en="Analysis question 2" data-zh="分析問題 2">Analysis question 2</span></li>
    <!-- 2-4 analysis questions per lab -->
  </ul>
</div>
```

Rules:
- 問題應要求學生結合數據與理解（不是單純的「列出結果」）
- 至少一題要求比較或解釋因果關係

### 8.6 Callout Boxes

```html
<!-- Background knowledge / Tips (amber border) -->
<div class="callout warn">
  <strong><span class="i18n" data-en="Tip:" data-zh="提示：">Tip:</span></strong>
  <span class="i18n" data-en="..." data-zh="...">...</span>
</div>

<!-- Related deep-dive links (green border) -->
<div class="callout key">
  <strong><span class="i18n" data-en="Related Deep Dive:" data-zh="相關深度解析：">Related Deep Dive:</span></strong>
  <a href="../vllm/index.html">vLLM Architecture &rarr;</a>
</div>

<!-- Critical warnings (red border) -->
<div class="callout critical">
  <strong><span class="i18n" data-en="Warning:" data-zh="警告：">Warning:</span></strong>
  <span class="i18n" data-en="..." data-zh="...">...</span>
</div>

<!-- Default (phase-colored border) -->
<div class="callout">
  <strong><span class="i18n" data-en="Note:" data-zh="注意：">Note:</span></strong>
  <span class="i18n" data-en="..." data-zh="...">...</span>
</div>
```

### 8.7 Side-by-Side Grid

```html
<div class="grid-2">
  <div class="card highlight-green">
    <h4><span class="i18n" data-en="Option A" data-zh="選項 A">Option A</span></h4>
    <ul><li>...</li></ul>
  </div>
  <div class="card highlight-purple">
    <h4><span class="i18n" data-en="Option B" data-zh="選項 B">Option B</span></h4>
    <ul><li>...</li></ul>
  </div>
</div>
```

### 8.8 Comparison Table

```html
<table>
  <tr>
    <th><span class="i18n" data-en="Method" data-zh="方法">Method</span></th>
    <th><span class="i18n" data-en="Advantage" data-zh="優勢">Advantage</span></th>
    <th><span class="i18n" data-en="Disadvantage" data-zh="劣勢">Disadvantage</span></th>
  </tr>
  <tr><td>Method A</td><td>...</td><td>...</td></tr>
</table>
```

### 8.9 Key Formulas Card

```html
<div class="card highlight-cyan">
  <h4><span class="i18n" data-en="Key Formulas" data-zh="關鍵公式">Key Formulas</span></h4>
  <ul>
    <li><span class="i18n" data-en="Formula: description" data-zh="公式：描述">Formula: description</span></li>
  </ul>
</div>
```

---

## 9. Section-by-Section Content Guide

Each lab page follows a **fixed section order**. Sections marked **[Required]** must appear in every lab; **[Conditional]** appear when applicable.

### Section 1: Learning Objectives [Required]

**ID:** `objectives`
**Label:** `Objectives`

**Required content:**
- 3–5 specific, measurable learning objectives
- Each begins with an action verb (Launch, Measure, Understand, Compare, Profile, ...)
- Objectives should cover both experiment skills and conceptual understanding

**Component:** `card.highlight-blue`

### Section 2: Background / Concept [Conditional]

**ID:** `background`
**Label:** `Background`

**When to include:** When the week introduces a new concept that needs explanation before experiments (e.g., PagedAttention, roofline model, speculative decoding).

**Required content:**
- 2–4 paragraph conceptual explanation
- Optional: key formulas card (`card.highlight-cyan`)
- Optional: comparison grid (`grid-2`) for tradeoffs (e.g., small vs large block sizes)

**Detail level:** Medium. Enough to understand *why* the experiments matter, but the main depth comes from the experiments themselves.

### Section 3: Setup & Configuration [Conditional]

**ID:** `setup`
**Label:** `Setup`

**When to include:** When the week requires setup beyond the base environment (e.g., special scripts, additional downloads, non-default server flags).

**Required content:**
- Copy-pasteable setup commands in `<pre><code>`
- If a helper script is needed, include the full script with syntax highlighting

**Detail level:** Low-medium. Just enough to get running. Assume `conda activate infer` and base models already available (from env-setup in `index.html`).

### Section 4: Experiments [Required]

**ID:** `experiments`
**Label:** `Experiments`

This is the **core section** of every lab.

**Required content:**
- `step-flow` with 3–6 numbered experiments
- Each step includes:
  - `step-num` (s1–s6)
  - `h4` title naming the specific experiment
  - Optional `p` description of what to observe
  - `pre/code` with the exact command(s) to run
- Commands must be:
  - Copy-pasteable (no pseudocode in shell blocks)
  - Self-contained (include all required flags)
  - Output-captured (pipe to `tee` when results are needed later)

**Detail level:** Very high. This section drives the lab. Include sweep loops, port numbers, model paths, output file names — everything needed to reproduce.

### Section 5: Metrics to Collect [Required]

**ID:** `metrics`
**Label:** `Metrics`

**Required content:**
- Table with columns: Metric, Description, Unit
- 3–6 metrics per lab
- Metrics must be extractable from the experiment output

**Component:** `<table>` with `overflow-x:auto` wrapper

### Section 6: Source Code Reading [Required]

**ID:** `source-code`
**Label:** `Source Code`

**Required content:**
- 2–4 source files to read
- Each entry: `.file-tag` with full path + one-sentence description of what to look for
- Files should be directly relevant to the week's phenomenon

**Component:** `card.highlight-purple`

### Section 7: Written Analysis [Required]

**ID:** `analysis`
**Label:** `Analysis`

**Required content:**
- 2–4 analysis questions
- Questions should require combining experimental data with conceptual understanding
- At least one question should ask "why?" (causal reasoning)
- At least one question should involve comparison (e.g., system A vs B, config X vs Y)

**Component:** `card.highlight-green`

### Section 8: Background Callouts [Conditional]

**When to include:** When the week benefits from conceptual context that doesn't fit in Section 2 (e.g., mid-page explainers of request rate, acceptance rate, etc.).

**Component:** `callout.warn` with bold title

### Section 9: Related Deep Dives [Conditional]

**When to include:** When the `ai-infra-basics/` section has a relevant deep-dive page.

**Component:** `callout.key` with link(s)

### Section 10: Bonus / Extra Experiments [Conditional]

**When to include:** Weeks that have optional extensions (e.g., Week 16 capstone).

**Component:** `card.highlight-cyan` or `card.highlight-orange`

---

## 10. Week-to-Content Reference

Quick reference for generating each week's page. The content already exists in `index.html` — extract and expand.

| Week | Phase | Title | Key Systems | GPU Requirement |
|------|-------|-------|-------------|-----------------|
| 1 | P1 | First LLM Serving | vLLM, SGLang | 1× A100 |
| 2 | P1 | Offline Throughput & Profiling | vLLM, PyTorch Profiler, Perfetto | 1× A100 |
| 3 | P1 | Roofline Model | nsys, ncu | 1× A100 |
| 4 | P2 | PagedAttention | vLLM, HuggingFace | 1× A100 |
| 5 | P2 | Prefix Caching (APC) | vLLM | 1× A100 |
| 6 | P2 | RadixAttention | SGLang | 1× A100 |
| 7 | P3 | Continuous vs Static Batching | vLLM, HuggingFace | 1× A100 |
| 8 | P3 | Chunked Prefill | vLLM | 1× A100 |
| 9 | P3 | Scheduling Policies | SGLang | 1× A100 |
| 10 | P4 | CUDA Graphs | vLLM | 1× A100 |
| 11 | P4 | Speculative Decoding | vLLM | 1× A100 |
| 12 | P4 | Quantization | vLLM, lm_eval | 1× A100 |
| 13 | P5 | Tensor Parallelism | vLLM | 2× A100 + NVLink |
| 14 | P5 | Mixture of Experts (MoE) | vLLM | 2× A100 + NVLink |
| 15 | P5 | LMCache | LMCache, vLLM | 1× A100 |
| 16 | P5 | Disaggregated P/D | vLLM, SGLang | 2× A100 |

---

## 11. Workflow Instructions

### Creating a New Lab Page

1. **Determine the week number and phase.** Set the `--phase` / `--phase-rgb` CSS variables accordingly (see Section 4.1).
2. **Extract content from `index.html`.** The monolithic page already contains all lab content — find the `<div class="section" id="week-NN">` block and extract it.
3. **Expand the content.** Individual pages can go deeper than the monolithic page:
   - Add a Background / Concept section if the topic warrants it
   - Expand callout boxes into full paragraphs with more context
   - Add comparison tables or formula cards where appropriate
   - Add more detail to experiment descriptions
4. **Write the HTML.** Use the skeleton from Section 3, CSS from Section 4.2, and follow the section order from Section 9.
5. **Set up navigation.** Add prev/next week links in both nav and footer. Update `index.html` roadmap cards to link to the new page.
6. **Review.** Verify commands are copy-pasteable, i18n is complete, responsive layout works.

### Updating `index.html` After Creating Lab Pages

Once individual pages exist, update the hub page:
- Keep: Environment Setup, Course Roadmap, Models & Datasets Reference, Grading Rubric
- Modify: Each week's roadmap card should link to `week-NN.html`
- Remove: The full week content (replaced by links)

---

## 12. Important Rules (Summary)

1. **No external dependencies** — no Bootstrap, highlight.js, Tailwind, external fonts, images
2. **All text bilingual** — every visible text must have `data-en` and `data-zh`
3. **Default English** — `<span>` innerHTML defaults to English
4. **Single-file self-contained** — CSS/JS all embedded, no external resources
5. **Responsive** — must include `@media(max-width:768px)` rules
6. **Nav back link** — first nav item is always `← Hands-On Labs` linking to `index.html`
7. **Dark theme only** — use the canonical hands-on CSS from Section 4.2
8. **Copy-pasteable commands** — all shell commands ready to paste, with `tee` for output capture
9. **Full file paths** — write `vllm/v1/core/kv_cache_manager.py` not `kv_cache_manager.py`
10. **Semantic card colors** — blue=objectives, purple=source-code, green=analysis (never mix)
11. **Step-num limit** — max 6 steps per step-flow (s1–s6); split or merge if more needed
12. **Phase accent consistency** — `--phase` must match the week's phase from Section 4.1

---

## 13. Example Prompt for LLM

```
Create an individual hands-on lab page for the AI Inference Infrastructure course.

Week: [N]
Title: [WEEK TITLE]
Phase: [1-5]

Source content: Extract from ai-infra-basics/hands-on/index.html, section id="week-[N]"

Write the output to: ai-infra-basics/hands-on/week-[NN].html

Instructions:
1. Read the week's content from the monolithic index.html.
2. Create a self-contained HTML page following LAB_PAGE_GUIDE.md.
   Required sections: Hero, Nav, Learning Objectives, Experiments (step-flow),
   Metrics to Collect, Source Code Reading, Written Analysis, Footer.
   Conditional sections: Background/Concept, Setup, Related Deep Dives, Bonus.
3. Expand the content:
   - Add a Background section if the concept needs explanation
   - Expand callout tips into full paragraphs
   - Add prev/next week navigation
4. Ensure:
   - Phase accent color matches (see Section 4.1)
   - All text bilingual (i18n EN/ZH)
   - Commands are copy-pasteable with tee output capture
   - Code blocks have syntax highlighting (.kw, .fn, .cm, .st, .nr)
   - Semantic card colors: blue=objectives, purple=source, green=analysis
   - 250+ lines minimum
```

---

## 14. Quality Checklist

### Structure
- [ ] Page is ≥250 lines of HTML
- [ ] Single self-contained `.html` file (no external CSS/JS/images)
- [ ] All CSS in `<style>` block in `<head>`
- [ ] DOCTYPE, charset, viewport meta tags present
- [ ] All nav links have corresponding section targets

### Theme & Style
- [ ] Uses canonical hands-on CSS from Section 4.2
- [ ] Background is `#16213e` (not paper-page `#0e0b12`)
- [ ] `--phase` and `--phase-rgb` match the week's phase
- [ ] Code blocks use `#1e1e2e` background
- [ ] Table headers use `var(--phase)` color

### i18n
- [ ] Every user-visible text wrapped in `<span class="i18n" data-en="..." data-zh="...">`
- [ ] Default innerHTML is English
- [ ] File paths, commands, model names, metrics abbreviations NOT translated
- [ ] `<` and `>` in data attributes escaped as `&lt;` / `&gt;`
- [ ] Language switch (EN/ZH) present in nav
- [ ] i18n script present before `</body>`

### Navigation
- [ ] First item is `← Hands-On Labs` → `index.html`
- [ ] `.week-nav` has correct prev/next links (Week 1: no prev; Week 16: no next)
- [ ] Last item is `.lang-switch` with EN/ZH
- [ ] All section anchor links work
- [ ] Footer has prev/next week links matching nav

### Required Sections (every lab)
- [ ] Hero with phase-badge, h1, subtitle, badges
- [ ] Learning Objectives card (`highlight-blue`)
- [ ] Experiments section with `step-flow` (3–6 steps)
- [ ] Metrics to Collect table (Metric / Description / Unit)
- [ ] Source Code Reading card (`highlight-purple`) with `.file-tag` paths
- [ ] Written Analysis card (`highlight-green`) with 2–4 questions

### Semantic Card Colors
- [ ] Learning Objectives → `highlight-blue` (always)
- [ ] Source Code Reading → `highlight-purple` (always)
- [ ] Written Analysis → `highlight-green` (always)
- [ ] Key Formulas → `highlight-cyan` (when present)
- [ ] Hardware warnings → `highlight-orange` or `callout.critical` (when present)
- [ ] Never use blue for source-code or green for objectives

### Commands
- [ ] All shell commands are copy-pasteable (no pseudocode in `<pre>`)
- [ ] Output captured with `tee` where results are needed later
- [ ] Model paths are full HuggingFace identifiers (e.g., `meta-llama/Llama-3.1-8B-Instruct`)
- [ ] Port numbers are explicit and consistent within the lab
- [ ] Sweep loops use proper bash `for` syntax with `do`/`done`

### Code Highlighting
- [ ] Shell keywords (`for`, `do`, `done`, `if`) use `.kw`
- [ ] Comments use `.cm`
- [ ] Strings use `.st`
- [ ] Numbers use `.nr`

### Footer
- [ ] Prev/next week links present (except edges)
- [ ] Back link to `index.html`
- [ ] Course title
- [ ] All text bilingual

---

## 15. Differences from PAPER_PAGE_GUIDE.md

For reference, here are the key differences between this guide and the paper page guide:

| Aspect | Paper Pages | Lab Pages |
|--------|-------------|-----------|
| Background color | `#0e0b12` (near-black) | `#16213e` (dark blue) |
| Accent system | Per-paper topic color | Per-phase color (5 phases) |
| Hero content | Paper title, arXiv, authors | Week N, topic, phase badge, time/hardware |
| Core sections | Architecture, Repo Analysis, Mechanisms | Objectives, Experiments, Metrics, Source Code, Analysis |
| Key component | `.vflow` diagrams | `.step-flow` experiment steps |
| Card semantics | `.card.hl` (generic highlight) | `.card.highlight-*` (color-coded by purpose) |
| Nav back link | `← Agentic Survey` | `← Hands-On Labs` |
| Target depth | 800–2500 lines | 250–800 lines |
| Target audience | Researchers understanding a paper | Students completing a lab |
| Content source | Paper PDF + repo | Existing `index.html` content + expansion |
