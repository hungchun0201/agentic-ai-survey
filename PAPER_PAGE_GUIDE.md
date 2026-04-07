# Paper Analysis Page Guide — agentic-ai-survey

> **Coding agent 必讀**：新增論文頁面前，請先完整閱讀本文件。所有論文頁面必須遵循此規範。
> 參考範本：`papers/continuum/index.html`

---

## 1. Overview

### What This Guide Is For

This is the single, authoritative guide for creating paper analysis pages in the Agentic AI KV Cache Management Survey. It covers both **style conventions** (CSS, HTML structure, i18n) and **content methodology** (what to write, how deep to go, workflow steps).

### Quality Expectations

- **Minimum length:** 800 lines of HTML
- **Target length:** 1000–2000 lines (higher for papers with repos)
- **Maximum length:** ~2500 lines (avoid padding; every line should carry information)
- **Self-contained:** Single `.html` file with all CSS inlined in a `<style>` block. No external CSS, no JavaScript libraries, no images.
- **Dark theme only:** All pages use the canonical dark theme defined in this guide.
- **Bilingual (i18n):** All user-visible text must have EN/ZH translations.
- **Colorful diagrams:** All diagrams built with HTML/CSS. Absolutely **no ASCII art**.
- **Technical depth:** The page should be useful to a researcher trying to understand or reproduce the paper.

### The "Repo First, Paper Second" Methodology

When a paper has an open-source implementation:

1. **Explore the repo first.** Read the README, understand the directory structure, identify key source files, and trace the main algorithms through the code.
2. **Read the paper second.** Understand the claims, contributions, evaluation setup, and theoretical framework.
3. **Compare.** Identify where the implementation matches, simplifies, or diverges from the paper's claims.

When a paper does NOT have a repo:

1. **Read the paper thoroughly.** Extract architecture details, algorithms, evaluation methodology, and results.
2. **Focus on technical depth.** Go deeper on theoretical contributions, mathematical formulations, and evaluation analysis.
3. **Skip repo-specific sections.** Omit "Repo Analysis" and "Paper vs Implementation" sections. Expand architecture, mechanisms, and performance sections instead.

---

## 2. File Structure

```
papers/<paper-slug>/index.html       ← 主論文頁面（單一 HTML 自包含）
papers/<paper-slug>/其他補充頁面.html  ← 可選
```

- 每篇論文一個資料夾，資料夾名稱用 kebab-case（如 `cold-rl`, `deepseek-mla`）
- 一個 HTML 檔案 = 一個完整頁面，**不使用外部 CSS/JS 檔案**，所有樣式寫在 `<style>` 標籤內

---

## 3. HTML Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>論文標題</title>
  <style>
    /* 完整 CSS 嵌入此處（見第 4 節） */
  </style>
</head>
<body>

  <!-- 1. 頂部導航列 -->
  <nav>...</nav>

  <!-- 2. Hero 區塊 -->
  <div class="hero">...</div>

  <!-- 3. 主內容 -->
  <div class="container">
    <section id="section-id">...</section>
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

### 4.1 Color System

| 用途 | 色碼 |
|------|------|
| 頁面背景 | `#0e0b12` |
| 主文字色 | `#d0d5e0` |
| 標題文字 | `#fff` |
| 連結色 | `#6ec6ff`（hover: `#ff9f43`） |
| 強調色（紅） | `#e94560` |
| 次強調色（橙） | `#ffb74d` |
| 輔助色（綠） | `#a6e3a1` / `#2ecc71` |
| 輔助色（藍） | `#0f3460` / `#89b4fa` |
| 次要文字 | `#8fa4c0` |
| 註解/弱化文字 | `#6c7086` |
| 程式碼背景 | `#1e1e2e` |
| 程式碼邊框 | `#2d2d44` |

### 4.2 Fonts

```css
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
code, pre code { font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace; }
```

### 4.3 Complete CSS (directly copy into `<style>`)

```css
/* ===== RESET & BASE ===== */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;font-size:16px}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0e0b12;color:#d0d5e0;line-height:1.7}
a{color:#6ec6ff;text-decoration:none;transition:color .2s}
a:hover{color:#ff9f43}

/* ===== STICKY NAV ===== */
nav{position:sticky;top:0;z-index:1000;background:rgba(45,12,22,0.95);backdrop-filter:blur(12px);border-bottom:1px solid rgba(233,69,96,0.25);padding:0 2rem}
nav ul{display:flex;list-style:none;max-width:1200px;margin:0 auto;gap:0.25rem;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none}
nav ul::-webkit-scrollbar{display:none}
nav ul li a{display:block;padding:0.85rem 1rem;color:#c0a0a8;text-decoration:none;font-size:0.85rem;font-weight:500;white-space:nowrap;transition:color 0.2s,border-bottom 0.2s;border-bottom:2px solid transparent}
nav ul li a:hover,nav ul li a.active{color:#fff;border-bottom:2px solid #e94560}
.lang-switch{margin-left:auto;display:flex;align-items:center;gap:6px;list-style:none}
.lang-switch a{color:rgba(255,255,255,.7);text-decoration:none;padding:4px 12px;border-radius:14px;font-size:.78rem;border:1px solid rgba(255,255,255,.3);transition:all .2s;cursor:pointer}
.lang-switch a:hover,.lang-switch a.active{color:#fff;background:rgba(255,255,255,.2);border-color:rgba(255,255,255,.5)}

/* ===== HERO ===== */
.hero{background:linear-gradient(135deg,#1e1020 0%,#2d1428 50%,#1a1030 100%);padding:4.5rem 2rem 3.5rem;text-align:center;position:relative;overflow:hidden;color:#fff}
.hero::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 40%,rgba(110,198,255,.06) 0%,transparent 50%),radial-gradient(circle at 70% 60%,rgba(255,159,67,.04) 0%,transparent 50%);animation:heroGlow 15s ease-in-out infinite alternate}
@keyframes heroGlow{0%{transform:translate(0,0)}100%{transform:translate(-2%,1%)}}
.hero h1{font-size:2.8rem;font-weight:800;color:#fff;margin-bottom:.6rem;position:relative}
.hero .sub{font-size:1.15rem;color:#8fa4c0;max-width:720px;margin:0 auto 1.5rem;position:relative}
.hero .badges{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;position:relative}
.hero .badge{display:inline-block;background:rgba(233,69,96,0.15);border:1px solid rgba(233,69,96,0.3);color:#e94560;padding:.3rem .9rem;border-radius:20px;font-size:.82rem;font-weight:600;position:relative}

/* ===== CONTAINER ===== */
.container{max-width:1100px;margin:0 auto;padding:2rem 1.5rem}

/* ===== SECTIONS ===== */
section{padding:2.5rem 0;border-bottom:1px solid rgba(110,198,255,.08)}
section:last-of-type{border-bottom:none}
h2{font-size:1.8rem;font-weight:700;color:#fff;margin:3rem 0 1.2rem;padding-bottom:.5rem;border-bottom:2px solid rgba(233,69,96,0.3);position:relative}
h2::before{content:'';position:absolute;bottom:-2px;left:0;width:60px;height:2px;background:linear-gradient(90deg,#6ec6ff,#ff9f43)}
h3{font-size:1.3rem;color:#e0e7f0;margin:1.8rem 0 .8rem;font-weight:600}
h4{font-size:1.05rem;color:#ffb74d;margin:1.2rem 0 .6rem;font-weight:600}
.container p,.container li{max-width:900px}

/* ===== CODE BLOCKS ===== */
pre{background:#1e1e2e;border:1px solid #2d2d44;border-radius:8px;padding:1rem 1.2rem;overflow-x:auto;font-size:.82rem;line-height:1.6;margin:.8rem 0}
pre code{font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;color:#cdd6f4}
code{font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:.85em}
p code,li code,td code{background:rgba(233,69,96,0.08);padding:.1em .4em;border-radius:4px;color:#f0a0b0;font-size:.85em}
.kw{color:#cba6f7}.fn{color:#89b4fa}.cm{color:#6c7086;font-style:italic}.st{color:#a6e3a1}.nu{color:#fab387}

/* ===== TABLES ===== */
table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}
th{background:rgba(233,69,96,0.1);color:#e94560;padding:.6rem .8rem;text-align:left;font-weight:600;border-bottom:2px solid rgba(233,69,96,0.3)}
td{padding:.55rem .8rem;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}
tr:hover td{background:rgba(110,198,255,.03)}

/* ===== CARDS ===== */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:1.5rem 0}
.card{background:rgba(30,30,46,.7);border:1px solid rgba(233,69,96,0.1);border-radius:12px;padding:1.5rem 1.8rem;transition:border-color .3s,box-shadow .3s}
.card:hover{border-color:rgba(233,69,96,0.3);box-shadow:0 4px 24px rgba(0,0,0,.3)}
.card.hl{border-left:4px solid #e94560}
.card h4{margin-top:0;color:#ffb74d}

/* ===== FLOW (horizontal steps) ===== */
.flow{display:flex;gap:0;margin:1.5rem 0;overflow-x:auto;padding-bottom:8px}
.flow .step{flex:1;min-width:170px;text-align:center;position:relative}
.flow .step .c{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-weight:700;font-size:1rem;color:#fff}
.flow .step:nth-child(1) .c{background:#0f3460}
.flow .step:nth-child(2) .c{background:#e94560}
.flow .step:nth-child(3) .c{background:#f5a623;color:#1a1030}
.flow .step:nth-child(4) .c{background:#2ecc71}
.flow .step .lbl{font-weight:600;font-size:.9rem;color:#e0e7f0}
.flow .step .desc{font-size:.8rem;color:#8fa4c0;margin-top:3px}
.flow .step::after{content:'';position:absolute;top:24px;right:-16px;width:32px;height:2px;background:rgba(255,255,255,.15)}
.flow .step:last-child::after{display:none}

/* ===== VERTICAL FLOW DIAGRAMS ===== */
.vflow{display:flex;flex-direction:column;gap:0;align-items:center;margin:1.5rem 0}
.vflow .box{width:100%;max-width:700px;padding:1rem 1.2rem;border-radius:10px;font-size:.85rem;position:relative}
.vflow .box.blue{background:rgba(15,52,96,.6);border:1px solid rgba(110,198,255,.3);color:#d0d5e0}
.vflow .box.red{background:rgba(233,69,96,.12);border:1px solid rgba(233,69,96,.35);color:#d0d5e0}
.vflow .box.green{background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.35);color:#d0d5e0}
.vflow .box.orange{background:rgba(245,166,35,.1);border:1px solid rgba(245,166,35,.35);color:#d0d5e0}
.vflow .box.gray{background:rgba(45,45,68,.7);border:1px solid rgba(255,255,255,.1);color:#8fa4c0}
.vflow .box h4{margin:0 0 .4rem;font-size:.95rem}
.vflow .box ul{margin:4px 0 0 16px;font-size:.82rem}
.vflow .box li{margin-bottom:2px}
.vflow .arrow{color:#6c7086;font-size:1.3rem;line-height:1;padding:2px 0}
.vflow .branch{display:flex;gap:12px;width:100%;max-width:700px;flex-wrap:wrap}
.vflow .branch .box{flex:1;min-width:200px}

/* ===== TIMELINE BAR ===== */
.tbar{display:flex;align-items:center;gap:0;margin:1rem 0 1.8rem;flex-wrap:nowrap;overflow:visible}
.tbar .seg{height:56px;display:flex;align-items:center;justify-content:center;font-size:.82rem;font-weight:500;white-space:nowrap;padding:0 16px;position:relative}
.tbar .seg.llm{background:rgba(110,198,255,.25);color:#6ec6ff;border-radius:6px 0 0 6px}
.tbar .seg.tool{background:rgba(233,69,96,.2);color:#e94560;flex:1;min-width:120px}
.tbar .seg.llm2{background:rgba(110,198,255,.25);color:#6ec6ff;border-radius:0 6px 6px 0}
.tbar .seg .marker{position:absolute;bottom:-18px;font-size:.7rem;color:#8fa4c0}

/* ===== DIAGRAM ===== */
.diagram{background:#1e1e2e;border:1px solid #2d2d44;border-radius:12px;padding:1.5rem;margin:1.5rem 0;overflow-x:auto}

/* ===== NOTES & WARNINGS ===== */
.note{background:rgba(255,159,67,.06);border-left:4px solid #ffb74d;padding:1rem 1.4rem;border-radius:0 8px 8px 0;margin:1rem 0;font-size:.88rem}
.note strong{color:#fff}
.warn{background:rgba(233,69,96,.06);border-left:4px solid #e94560;padding:1rem 1.4rem;border-radius:0 8px 8px 0;margin:1rem 0;font-size:.88rem}
.warn strong{color:#fff}

/* ===== LISTS ===== */
ul,ol{margin:8px 0 8px 22px}
li{margin-bottom:5px}

/* ===== COMPARISON INDICATORS ===== */
.check{color:#2ecc71;font-weight:bold}
.cross{color:#e94560;font-weight:bold}
.partial{color:#ffb74d;font-weight:bold}

/* ===== SIDE-BY-SIDE GRID ===== */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}

/* ===== FOOTER ===== */
footer{text-align:center;padding:3rem 2rem;color:#8fa4c0;font-size:.82rem;border-top:1px solid rgba(110,198,255,.12)}
footer a{color:#6ec6ff}

/* ===== RESPONSIVE ===== */
@media(max-width:768px){
  .hero h1{font-size:1.8rem}
  .container{padding:1rem}
  .cards{grid-template-columns:1fr}
  .grid-2{grid-template-columns:1fr}
  pre{font-size:.75rem;padding:.7rem}
  nav ul{gap:0}
  nav ul li a{padding:.7rem .6rem;font-size:.78rem}
}
```

---

## 5. Page Components

### 5.1 Navigation (nav)

```html
<nav>
  <ul>
    <li><a href="../../index.html">&larr; Agentic Survey</a></li>
    <li><a href="#section1">Section 1</a></li>
    <li><a href="#section2">Section 2</a></li>
    <!-- 更多章節連結 -->
    <li class="lang-switch">
      <a onclick="setLang('en')" id="lang-en" class="active">EN</a>
      <a onclick="setLang('zh')" id="lang-zh">ZH</a>
    </li>
  </ul>
</nav>
```

Rules:
- 第一個連結**固定**為 `← Agentic Survey`，指向 `../../index.html`
- 最後為語言切換按鈕（EN/ZH）
- 導航項目對應各 `<section id="...">`

### 5.2 Hero Section

```html
<div class="hero">
  <h1>論文標題</h1>
  <p class="sub"><span class="i18n" data-en="English subtitle" data-zh="中文副標題">English subtitle</span></p>
  <div class="badges">
    <span class="badge">arXiv:XXXX.XXXXX</span>
    <span class="badge">關鍵詞1</span>
    <span class="badge">關鍵詞2</span>
  </div>
  <p style="color:#8fa4c0;font-size:.92rem;margin-top:1.2rem;position:relative;max-width:none">
    作者列表（附上標機構編號）
  </p>
  <p style="color:#6a7a94;font-size:.85rem;position:relative;max-width:none">
    機構列表
  </p>
</div>
```

Hero should be scannable in 3 seconds — title, one-line subtitle, badges, authors only.

### 5.3 Section Structure

```html
<section id="unique-id">
  <h2><span class="i18n" data-en="1. Section Title" data-zh="1. 章節標題">1. Section Title</span></h2>
  <p><span class="i18n" data-en="..." data-zh="...">English content as default</span></p>
  <!-- 子標題用 h3, h4 -->
</section>
```

- 每個 section 有唯一 `id`，與 nav 連結對應
- h2 帶章節編號（`1.`, `2.`, ...）
- h3 帶子編號（`1.1`, `1.2`, ...）

### 5.4 Footer

```html
<footer>
  <p><span class="i18n" data-en="Paper Title (arXiv:XXXX.XXXXX) — Page Description" data-zh="...">...</span></p>
  <p><span class="i18n" data-en="Source code: github.com/..." data-zh="...">Source code: <code>github.com/...</code></span></p>
  <p><span class="i18n" data-en="Generated YYYY-MM-DD" data-zh="產生日期：YYYY-MM-DD">Generated YYYY-MM-DD</span></p>
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
- Code keywords and values (e.g., `None`, `True`, `self`)
- Command names (e.g., `find`, `pytest`, `grep`)
- Class/function names (e.g., `ToolCallParser`, `schedule()`)
- Mathematical formulas and numbers

### 6.3 Embedding HTML Inside i18n

`data-en` / `data-zh` values are set via `innerHTML`, so they can contain HTML tags:

```html
<span class="i18n"
  data-en="Use &lt;code&gt;schedule()&lt;/code&gt; to trigger"
  data-zh="使用 &lt;code&gt;schedule()&lt;/code&gt; 觸發">
  Use <code>schedule()</code> to trigger
</span>
```

Note: `<` and `>` must be escaped as `&lt;` / `&gt;` inside `data-*` attributes.

---

## 7. Code Block Syntax Highlighting

No JS highlighting library. Use manual `<span>` classes:

| Class | Purpose | Color |
|-------|---------|-------|
| `.kw` | Keywords (`class`, `def`, `if`, `return`) | `#cba6f7` (purple) |
| `.fn` | Function/class names | `#89b4fa` (blue) |
| `.cm` | Comments | `#6c7086` (gray, italic) |
| `.st` | Strings | `#a6e3a1` (green) |
| `.nu` | Numbers | `#fab387` (orange) |

Example:
```html
<pre><code><span class="kw">class</span> <span class="fn">MyClass</span>:
    <span class="kw">def</span> <span class="fn">__init__</span>(self):
        self.value = <span class="nu">42</span>  <span class="cm"># 初始值</span>
        self.name = <span class="st">"hello"</span></code></pre>
```

### Inline Code

Regular inline code inherits `p code` style (pink-ish tint) automatically.

Special file path highlighting with inline styles:
- **Modified by this paper** (red):
  ```html
  <code style="background:rgba(233,69,96,.12);border:1px solid rgba(233,69,96,.3);color:#e94560;padding:2px 8px;border-radius:4px">file/path.py</code>
  ```
- **External / non-core files** (green):
  ```html
  <code style="background:rgba(166,227,161,.1);border:1px solid rgba(166,227,161,.3);color:#a6e3a1;padding:2px 8px;border-radius:4px">external/path.py</code>
  ```

---

## 8. Component HTML Templates

### 8.1 Cards

```html
<div class="cards">
  <div class="card hl">
    <h4><span class="i18n" data-en="Card Title" data-zh="卡片標題">Card Title</span></h4>
    <p><span class="i18n" data-en="Description" data-zh="描述">Description</span></p>
  </div>
  <!-- 更多卡片 -->
</div>
```

- `.hl` class adds a red left-border highlight

### 8.2 Note / Warning Callouts

```html
<!-- Info note (orange left border) -->
<div class="note">
  <strong>Note:</strong> content
</div>

<!-- Warning (red left border) -->
<div class="warn">
  <strong>Warning:</strong> content
</div>
```

### 8.3 Vertical Flow Diagram

```html
<div class="vflow">
  <div class="box blue"><h4>Step 1</h4><p>Description</p></div>
  <div class="arrow">↓</div>
  <div class="box red"><h4>Step 2</h4><p>Description</p></div>
  <div class="arrow">↓</div>
  <!-- Branching -->
  <div class="branch">
    <div class="box green"><h4>Path A</h4></div>
    <div class="box orange"><h4>Path B</h4></div>
  </div>
</div>
```

Available box colors: `blue`, `red`, `green`, `orange`, `gray`

### 8.4 Horizontal Flow (Steps)

```html
<div class="flow">
  <div class="step"><div class="c">1</div><div class="lbl">Step Name</div><div class="desc">Description</div></div>
  <div class="step"><div class="c">2</div><div class="lbl">Step Name</div><div class="desc">Description</div></div>
  <div class="step"><div class="c">3</div><div class="lbl">Step Name</div><div class="desc">Description</div></div>
</div>
```

### 8.5 Timeline Bar

```html
<div class="tbar">
  <div class="seg llm">Phase 1</div>
  <div class="seg tool">Phase 2</div>
  <div class="seg llm2">Phase 3</div>
</div>
```

### 8.6 Diagram Container (tree structures / architecture)

```html
<div class="diagram">
  <!-- Use nested div + margin-left for tree structures -->
  <div style="font-weight:700;color:#ffb74d">root/</div>
  <div style="margin-left:16px">
    <div style="font-weight:600;color:#6ec6ff">subdir/</div>
    <div style="margin-left:16px;color:#6c7086;font-size:.82rem">file.py</div>
  </div>
</div>
```

### 8.7 Tables

```html
<table>
  <tr>
    <th><span class="i18n" data-en="Column 1" data-zh="欄位1">Column 1</span></th>
    <th><span class="i18n" data-en="Column 2" data-zh="欄位2">Column 2</span></th>
  </tr>
  <tr>
    <td>Value 1</td>
    <td>Value 2</td>
  </tr>
</table>
```

### 8.8 Claims vs Implementation Table

```html
<table>
  <tr>
    <th>Paper Claim</th>
    <th>Status</th>
    <th>Code Evidence</th>
  </tr>
  <tr>
    <td>[Claim]</td>
    <td><span class="check">YES</span></td>
    <td>[Reference to specific code]</td>
  </tr>
  <tr>
    <td>[Claim]</td>
    <td><span class="partial">PARTIAL</span></td>
    <td>[Explanation]</td>
  </tr>
  <tr>
    <td>[Claim]</td>
    <td><span class="cross">NO</span></td>
    <td>[What is missing]</td>
  </tr>
</table>
```

### 8.9 Side-by-Side Grid

```html
<div class="grid-2">
  <div class="card hl">
    <h4>Strengths</h4>
    <ul><li>...</li></ul>
  </div>
  <div class="card">
    <h4>Limitations</h4>
    <ul><li>...</li></ul>
  </div>
</div>
```

---

## 9. Diagram Guidelines

### CRITICAL RULE: No ASCII Art

All diagrams must be built with HTML elements and CSS. Use colored `<div>` blocks, flexbox for layout, and Unicode arrows (↓ for down, → for right) for flow.

### Available Diagram Patterns

| Pattern | CSS Classes | Use For |
|---------|-------------|---------|
| Vertical flow | `.vflow` + `.box.{color}` + `.arrow` | Decision trees, pipelines, algorithms |
| Horizontal steps | `.flow` + `.step` + `.c` + `.lbl` + `.desc` | Numbered process steps |
| Timeline bar | `.tbar` + `.seg` | Temporal sequences, request lifecycle |
| Tree / architecture | `.diagram` + inline nested divs | File trees, component hierarchy |
| Cards grid | `.cards` + `.card` | Parallel concepts, feature comparison |

### Color Usage Rules

- Use **at least 3 distinct colors** per diagram — monochrome diagrams look dull.
- Use the `.box` color variants (`blue`, `red`, `green`, `orange`, `gray`) for vertical flows.
- For horizontal steps, colors are auto-assigned by `:nth-child`.
- Use inline `style="background:..."` with gradients for special emphasis.

---

## 10. Section-by-Section Content Guide

### Section: Overview / Problem

**Purpose:** Establish context — what problem exists, what the paper does about it.

**Required content:**
- Problem description (2–4 sentences, specific about metrics/bottleneck)
- Core contributions (numbered list, bolded names)
- Key insight or approach (1–2 sentences)

**Detail level:** Medium. Use cards (`.card.hl`) to visually separate problem, contributions, and evaluation summary.

### Section: Architecture

**Purpose:** Show how the system is structured.

**Required content:**
- 1–2 introductory sentences
- **At least one colorful diagram** (`.vflow` or `.diagram`) showing main components and data flow
- A note (`.note`) highlighting a key architectural insight
- Optional: a second diagram showing a sub-component in detail

**Detail level:** High. The diagram should show every major component mentioned in the paper.

### Section: Repo Analysis (if repo exists)

**Purpose:** Map the paper's abstract concepts to concrete code.

**Required content:**
- File tree (`.diagram` with nested divs) showing repo structure with annotations
- Table mapping class names → files → purposes
- Brief description of implementation approach

**Detail level:** High. Include file paths, class names, and method names. Use the red/green inline code styles for modified vs external files.

### Section: Core Mechanisms

**Purpose:** Deep dive into how the system actually works.

**Required content:**
- Multiple sub-sections (numbered: 4.1, 4.2, etc.), one per key mechanism
- For each mechanism:
  - A card or paragraph explaining what and why
  - A code block with syntax highlighting (from repo or pseudocode)
  - A flow diagram showing decision logic
- At least 2–3 mechanisms covered

**Detail level:** Very high. This is the longest and most important section. Include real code (with file and line references) or detailed pseudocode.

### Section: Performance Results

**Purpose:** Present evaluation results with context.

**Required content:**
- Results table comparing proposed system against baselines
- Specific numbers from the paper (not vague claims like "faster")
- A note (`.note`) with caveats or observations

**Detail level:** Medium-high. Cite exact values (e.g., "2.16× improvement in average JCT").

### Section: Claims vs Implementation (if repo exists)

**Purpose:** Honest comparison of paper promises vs code reality.

**Required content:**
- Comparison table with `.check` / `.partial` / `.cross` status indicators
- Strengths/Limitations side-by-side (`.grid-2`)

**Detail level:** Very high. Reference exact class names, method names, and file locations.

### Section: How to Reproduce (if repo exists)

**Purpose:** Practical guide for reproducing results.

**Required content:**
- Step-by-step setup commands in code blocks
- Run / evaluation commands
- Hardware requirements (in a `.warn` callout)
- Key configuration parameters table

**Detail level:** Medium. Commands should be copy-pasteable.

---

## 11. Workflow Instructions

### For Papers WITH a Repository

1. **Explore the repo:** README → directory structure → key source files → core algorithms
2. **Read the paper:** claims, contributions, evaluation setup, results, specific numbers
3. **Compare:** For each major claim, check: YES / PARTIAL / NO in code
4. **Write the HTML:** Fill the skeleton from Section 3. Include all sections: Hero, Nav, Overview, Architecture, Repo Analysis, Core Mechanisms, Performance, Claims vs Implementation, Reproduce, Footer
5. **Review:** Verify code snippets are accurate, diagrams are colorful, page is self-contained, ≥800 lines

### For Papers WITHOUT a Repository

1. **Read the paper thoroughly:** every technical detail, evaluation methodology, positioning vs prior work
2. **Write the HTML:** Use the same skeleton but:
   - **Omit:** Repo Analysis, Claims vs Code, How to Reproduce
   - **Expand:** Architecture (multiple diagrams), Core Mechanisms (deeper analysis)
   - **Add:** Mathematical formulations, pseudocode, comparison with related work, significance/impact section
3. **Compensate** for missing repo content with more diagrams, deeper evaluation analysis, limitations discussion

---

## 12. Important Rules (Summary)

1. **No ASCII art** — all diagrams use HTML elements (`.vflow`, `.flow`, `.tbar`, `.diagram`, `.cards`)
2. **No external dependencies** — no Bootstrap, highlight.js, Tailwind, external fonts, images
3. **Full file paths** — write `vllm/v1/core/sched/scheduler.py` not `scheduler.py`
4. **All text bilingual** — every visible text must have `data-en` and `data-zh`
5. **Default English** — `<span>` innerHTML defaults to English
6. **Single-file self-contained** — CSS/JS all embedded, no external resources
7. **Responsive** — must include `@media(max-width:768px)` rules
8. **Nav back link** — first nav item is always `← Agentic Survey` linking to `../../index.html`
9. **Dark theme only** — use the canonical CSS from Section 4.3, no light themes

---

## 13. Example Prompt for LLM

### For Papers WITH a Repository

```
Create a paper analysis page for the Agentic AI survey project.

Paper: "[FULL PAPER TITLE]"
arXiv: [ARXIV_ID]
Venue: [VENUE] (e.g., "SOSP '23" or "Preprint")
Year: [YEAR]
Authors: [AUTHOR LIST]

Repository: [ABSOLUTE PATH TO LOCAL REPO CLONE]

Write the output to: papers/<slug>/index.html

Instructions:
1. FIRST explore the repository thoroughly (README → directory structure → key source files).
2. THEN read the paper PDF at: [PATH TO PDF or ARXIV URL].
3. Compare implementation against paper claims (YES / PARTIAL / NO).
4. Write a self-contained HTML page following PAPER_PAGE_GUIDE.md.
   Required sections: Hero, Nav, Overview, Architecture, Repo Analysis, Core Mechanisms,
   Performance Results, Claims vs Implementation, How to Reproduce, Footer.
5. Ensure:
   - At least 800 lines (target 1200+)
   - Dark theme, all CSS from Section 4.3
   - All text bilingual (i18n EN/ZH)
   - All diagrams are colorful HTML/CSS (NO ASCII art)
   - Code snippets have syntax highlighting (.kw, .fn, .cm, .st, .nu)
   - Claims vs Implementation table is thorough and honest
```

### For Papers WITHOUT a Repository

```
Create a paper analysis page for the Agentic AI survey project.

Paper: "[FULL PAPER TITLE]"
arXiv: [ARXIV_ID]
Venue: [VENUE]
Year: [YEAR]
Authors: [AUTHOR LIST]

Repository: None (paper-only analysis)

Write the output to: papers/<slug>/index.html

Instructions:
1. Read the paper PDF at: [PATH TO PDF or ARXIV URL].
2. Write a self-contained HTML page following PAPER_PAGE_GUIDE.md.
   Required sections: Hero, Nav, Overview, Architecture (expanded, multiple diagrams),
   Core Mechanisms (expanded), Performance Results, Significance/Impact, Footer.
   OMIT: Repo Analysis, Claims vs Code, How to Reproduce.
3. Compensate for missing repo by:
   - 2–3 architecture diagrams showing different aspects
   - Pseudocode or mathematical formulations
   - Deeper evaluation methodology analysis
   - Comparison with related work
4. Ensure:
   - At least 800 lines (target 1200+)
   - Dark theme, all CSS from Section 4.3
   - All text bilingual (i18n EN/ZH)
   - All diagrams are colorful HTML/CSS (NO ASCII art)
   - Performance numbers cited directly from paper with exact values
```

---

## 14. Quality Checklist

### Structure
- [ ] Page is ≥800 lines of HTML
- [ ] Single self-contained `.html` file (no external CSS/JS/images)
- [ ] All CSS in `<style>` block in `<head>`
- [ ] DOCTYPE, charset, viewport meta tags present
- [ ] All nav links have corresponding `<section id="...">` targets

### Theme & Style
- [ ] Uses canonical dark theme CSS from Section 4.3
- [ ] Background is `#0e0b12`, not light theme
- [ ] Code blocks use `#1e1e2e` background
- [ ] Tables use `rgba(233,69,96,0.1)` header background

### i18n
- [ ] Every user-visible text wrapped in `<span class="i18n" data-en="..." data-zh="...">`
- [ ] Default innerHTML is English
- [ ] File paths, code keywords, class names are NOT translated
- [ ] `<` and `>` in data attributes escaped as `&lt;` / `&gt;`
- [ ] Language switch (EN/ZH) present in nav
- [ ] i18n script present before `</body>`

### Navigation
- [ ] First item is `← Agentic Survey` → `../../index.html`
- [ ] Last item is `.lang-switch` with EN/ZH
- [ ] All section links work

### Content
- [ ] Overview has problem description and contributions
- [ ] Architecture has ≥1 colorful diagram
- [ ] Core Mechanisms has ≥2 detailed mechanism write-ups
- [ ] Performance has specific numbers (not vague claims)
- [ ] Code blocks have syntax highlighting (`.kw`, `.fn`, `.cm`, `.st`, `.nu`)

### Diagrams
- [ ] All diagrams built with HTML/CSS (`.vflow`, `.flow`, `.tbar`, `.diagram`)
- [ ] **No ASCII art** anywhere
- [ ] Each diagram uses ≥3 distinct colors

### Repo-Specific (if repo exists)
- [ ] File tree showing repo structure
- [ ] Key classes table
- [ ] Code snippets with file/line references
- [ ] Claims vs Implementation table with `.check` / `.partial` / `.cross`
- [ ] Strengths/Limitations side-by-side (`.grid-2`)
- [ ] Reproduction steps with copy-pasteable commands

### Paper-Only (if no repo)
- [ ] Expanded architecture with multiple diagrams
- [ ] Mathematical formulations or pseudocode
- [ ] Deeper evaluation analysis
- [ ] Significance or impact section

### Footer
- [ ] Paper citation with arXiv ID
- [ ] Generation date
- [ ] All text bilingual
