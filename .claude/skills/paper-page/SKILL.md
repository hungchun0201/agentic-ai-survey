---
name: paper-page
description: Create or update paper analysis pages for the agentic-ai-survey project. Covers full page creation (HTML structure, CSS, i18n, diagrams, content methodology), embedding original paper figures from arXiv, and converting math to KaTeX LaTeX. TRIGGER when: user asks to create a paper page, add paper figures, embed figures from a paper, convert equations to LaTeX, fix paper page styling, or work on any file under papers/<slug>/index.html.
---

# Paper Analysis Page — Complete Skill

> Reference implementation: `papers/nimble/index.html` (figures + LaTeX), `papers/continuum/index.html` (canonical style)

---

## 1. Overview & Quality Expectations

- **Format:** Single self-contained `.html` file at `papers/<slug>/index.html`. All CSS in `<style>`, no external CSS/JS/images (except KaTeX CDN and arXiv figure URLs).
- **Length:** 800–2500 lines (target 1200+; every line carries information).
- **Theme:** Dark only (`background:#0e0b12`).
- **Bilingual:** All visible text uses `<span class="i18n" data-en="..." data-zh="...">English default</span>`.
- **Diagrams:** HTML/CSS only (`.vflow`, `.flow`, `.tbar`, `.diagram`, `.cards`). **No ASCII art.**
- **Paper figures:** Embed original figures from arXiv HTML version with white background.
- **Math:** All equations rendered via KaTeX LaTeX.

### Methodology

**With repo:** Explore repo first → read paper → compare claims vs code.
**Without repo:** Read paper → expand architecture/mechanisms/math → omit repo-specific sections.

---

## 2. File Structure

```
papers/<slug>/index.html       ← main page (self-contained)
papers/<slug>/other.html       ← optional supplementary pages
```

Folder name: kebab-case (e.g., `cold-rl`, `deepseek-mla`).

---

## 3. HTML Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paper Title</title>
<!-- KaTeX (if page has math) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});"></script>
<style>
  /* Full CSS here (see Section 4) */
</style>
</head>
<body>
  <nav>...</nav>
  <div class="hero">...</div>
  <div class="container">
    <section id="...">...</section>
  </div>
  <footer>...</footer>
  <script>
    function setLang(l){document.querySelectorAll('.i18n').forEach(function(e){if(e.dataset[l])e.innerHTML=e.dataset[l]});document.getElementById('lang-en').classList.toggle('active',l==='en');document.getElementById('lang-zh').classList.toggle('active',l==='zh');localStorage.setItem('lang',l)}
    (function(){var l=localStorage.getItem('lang');if(l)setLang(l)})();
  </script>
</body>
</html>
```

---

## 4. CSS Specification

### 4.1 Accent Color System

Each page has its own accent via 3 CSS variables:

```css
:root{--accent:#e94560;--accent-rgb:233,69,96;--nav-bg:rgba(45,12,22,0.95)}
```

All UI elements reference `var(--accent)` / `rgba(var(--accent-rgb), opacity)`.

#### Accent Palette

| Color | `--accent` | `--accent-rgb` | Suitable for |
|-------|-----------|----------------|-------------|
| Rose | `#e94560` | `233,69,96` | KV cache scheduling |
| Coral | `#e87461` | `232,116,97` | Performance optimization |
| Amber | `#e5a130` | `229,161,48` | Cost / resource |
| Lime | `#8bc34a` | `139,195,74` | Speculative / prediction |
| Emerald | `#2ecc71` | `46,204,113` | Cache strategies |
| Teal | `#26a69a` | `38,166,154` | Agent frameworks |
| Cyan | `#29b6f6` | `41,182,246` | Distributed systems |
| Blue | `#5c6bc0` | `92,107,192` | Attention mechanisms |
| Indigo | `#7e57c2` | `126,87,194` | Model architecture |
| Purple | `#ab47bc` | `171,71,188` | Scheduling / dispatch |
| Pink | `#ec407a` | `236,64,122` | Prefill-related |
| Sky | `#4fc3f7` | `79,195,247` | Infrastructure |

Selection criteria: OKLCH lightness ≈ 0.70–0.75, chroma ≈ 0.15–0.19, WCAG AA 4.5:1 contrast against `#0e0b12`.

#### Fixed Colors (never change)

| Purpose | Color |
|---------|-------|
| Page background | `#0e0b12` |
| Body text | `#d0d5e0` |
| Headings | `#fff` |
| Links / hover | `#6ec6ff` / `#ff9f43` |
| h4 titles | `#ffb74d` |
| Secondary text | `#8fa4c0` |
| Muted text | `#6c7086` |
| Code background | `#1e1e2e` |

### 4.2 Complete CSS

Copy this entire block into `<style>`. Only change the `:root` accent line.

```css
/* ===== ACCENT (change per paper) ===== */
:root{--accent:#e94560;--accent-rgb:233,69,96;--nav-bg:rgba(45,12,22,0.95)}

/* ===== RESET & BASE ===== */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;font-size:16px}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0e0b12;color:#d0d5e0;line-height:1.7}
a{color:#6ec6ff;text-decoration:none;transition:color .2s}
a:hover{color:#ff9f43}

/* ===== STICKY NAV ===== */
nav{position:sticky;top:0;z-index:1000;background:var(--nav-bg);backdrop-filter:blur(12px);border-bottom:1px solid rgba(var(--accent-rgb),0.25);padding:0 2rem}
nav ul{display:flex;list-style:none;max-width:1200px;margin:0 auto;gap:0.25rem;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none}
nav ul::-webkit-scrollbar{display:none}
nav ul li a{display:block;padding:0.85rem 1rem;color:#c0a0a8;text-decoration:none;font-size:0.85rem;font-weight:500;white-space:nowrap;transition:color 0.2s,border-bottom 0.2s;border-bottom:2px solid transparent}
nav ul li a:hover,nav ul li a.active{color:#fff;border-bottom:2px solid var(--accent)}
.lang-switch{margin-left:auto;display:flex;align-items:center;gap:6px;list-style:none}
.lang-switch a{color:rgba(255,255,255,.7);text-decoration:none;padding:4px 12px;border-radius:14px;font-size:.78rem;border:1px solid rgba(255,255,255,.3);transition:all .2s;cursor:pointer}
.lang-switch a:hover,.lang-switch a.active{color:#fff;background:rgba(255,255,255,.2);border-color:rgba(255,255,255,.5)}

/* ===== HERO ===== */
.hero{background:linear-gradient(135deg,#1e1020 0%,#1a1428 50%,#1a1030 100%);padding:4.5rem 2rem 3.5rem;text-align:center;position:relative;overflow:hidden;color:#fff}
.hero::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 40%,rgba(var(--accent-rgb),.06) 0%,transparent 50%),radial-gradient(circle at 70% 60%,rgba(255,159,67,.04) 0%,transparent 50%);animation:heroGlow 15s ease-in-out infinite alternate}
@keyframes heroGlow{0%{transform:translate(0,0)}100%{transform:translate(-2%,1%)}}
.hero h1{font-size:2.8rem;font-weight:800;color:#fff;margin-bottom:.6rem;position:relative}
.hero .sub{font-size:1.15rem;color:#8fa4c0;max-width:720px;margin:0 auto 1.5rem;position:relative}
.hero .badges{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;position:relative}
.hero .badge{display:inline-block;background:rgba(var(--accent-rgb),0.15);border:1px solid rgba(var(--accent-rgb),0.3);color:var(--accent);padding:.3rem .9rem;border-radius:20px;font-size:.82rem;font-weight:600;position:relative;text-transform:none}

/* ===== CONTAINER ===== */
.container{max-width:1100px;margin:0 auto;padding:2rem 1.5rem}

/* ===== SECTIONS ===== */
section{padding:2.5rem 0;border-bottom:1px solid rgba(110,198,255,.08)}
section:last-of-type{border-bottom:none}
h2{font-size:1.8rem;font-weight:700;color:#fff;margin:3rem 0 1.2rem;padding-bottom:.5rem;border-bottom:2px solid rgba(var(--accent-rgb),0.3);position:relative}
h2::before{content:'';position:absolute;bottom:-2px;left:0;width:60px;height:2px;background:linear-gradient(90deg,#6ec6ff,#ff9f43)}
h3{font-size:1.3rem;color:#e0e7f0;margin:1.8rem 0 .8rem;font-weight:600}
h4{font-size:1.05rem;color:#ffb74d;margin:1.2rem 0 .6rem;font-weight:600}
.container p,.container li{max-width:900px}

/* ===== CODE ===== */
pre{background:#1e1e2e;border:1px solid #2d2d44;border-radius:8px;padding:1rem 1.2rem;overflow-x:auto;font-size:.82rem;line-height:1.6;margin:.8rem 0}
pre code{font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;color:#cdd6f4}
code{font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:.85em}
p code,li code,td code{background:rgba(var(--accent-rgb),0.08);padding:.1em .4em;border-radius:4px;color:var(--accent);font-size:.85em}
.kw{color:#cba6f7}.fn{color:#89b4fa}.cm{color:#6c7086;font-style:italic}.st{color:#a6e3a1}.nu{color:#fab387}

/* ===== TABLES ===== */
table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}
th{background:rgba(var(--accent-rgb),0.1);color:var(--accent);padding:.6rem .8rem;text-align:left;font-weight:600;border-bottom:2px solid rgba(var(--accent-rgb),0.3)}
td{padding:.55rem .8rem;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}
tr:hover td{background:rgba(110,198,255,.03)}

/* ===== CARDS ===== */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin:1.5rem 0}
.card{background:rgba(30,30,46,.7);border:1px solid rgba(var(--accent-rgb),0.1);border-radius:12px;padding:1.5rem 1.8rem;transition:border-color .3s,box-shadow .3s}
.card:hover{border-color:rgba(var(--accent-rgb),0.3);box-shadow:0 4px 24px rgba(0,0,0,.3)}
.card.hl{border-left:4px solid var(--accent)}
.card h4{margin-top:0;color:#ffb74d}

/* ===== FLOW (horizontal steps) ===== */
.flow{display:flex;gap:0;margin:1.5rem 0;overflow-x:auto;padding-bottom:8px}
.flow .step{flex:1;min-width:170px;text-align:center;position:relative}
.flow .step .c{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-weight:700;font-size:1rem;color:#fff}
.flow .step:nth-child(1) .c{background:#0f3460}
.flow .step:nth-child(2) .c{background:var(--accent)}
.flow .step:nth-child(3) .c{background:#f5a623;color:#1a1030}
.flow .step:nth-child(4) .c{background:#2ecc71}
.flow .step .lbl{font-weight:600;font-size:.9rem;color:#e0e7f0}
.flow .step .desc{font-size:.8rem;color:#8fa4c0;margin-top:3px}
.flow .step::after{content:'';position:absolute;top:24px;right:-16px;width:32px;height:2px;background:rgba(255,255,255,.15)}
.flow .step:last-child::after{display:none}

/* ===== VERTICAL FLOW ===== */
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
.tbar .seg.tool{background:rgba(var(--accent-rgb),.2);color:var(--accent);flex:1;min-width:120px}
.tbar .seg.llm2{background:rgba(110,198,255,.25);color:#6ec6ff;border-radius:0 6px 6px 0}
.tbar .seg .marker{position:absolute;bottom:-18px;font-size:.7rem;color:#8fa4c0}

/* ===== DIAGRAM ===== */
.diagram{background:#1e1e2e;border:1px solid #2d2d44;border-radius:12px;padding:1.5rem;margin:1.5rem 0;overflow-x:auto}

/* ===== NOTES & WARNINGS ===== */
.note{background:rgba(255,159,67,.06);border-left:4px solid #ffb74d;padding:1rem 1.4rem;border-radius:0 8px 8px 0;margin:1rem 0;font-size:.88rem}
.note strong{color:#fff}
.warn{background:rgba(var(--accent-rgb),.06);border-left:4px solid var(--accent);padding:1rem 1.4rem;border-radius:0 8px 8px 0;margin:1rem 0;font-size:.88rem}
.warn strong{color:#fff}

/* ===== LISTS ===== */
ul,ol{margin:8px 0 8px 22px}
li{margin-bottom:5px}

/* ===== METRIC BOXES ===== */
.metric-boxes{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin:1.5rem 0}
.metric-box{background:rgba(30,30,46,.7);border:1px solid rgba(var(--accent-rgb),0.2);border-radius:10px;padding:1.2rem;text-align:center}
.metric-box .value{font-size:2rem;font-weight:700;color:var(--accent);line-height:1.1}
.metric-box .label{font-size:.82rem;color:#8fa4c0;margin-top:4px}

/* ===== INDICATORS ===== */
.check{color:#2ecc71;font-weight:bold}
.cross{color:#e94560;font-weight:bold}
.partial{color:#ffb74d;font-weight:bold}

/* ===== GRID-2 ===== */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}

/* ===== PAPER FIGURES ===== */
.paper-fig{margin:1.8rem 0;text-align:center}
.paper-fig img{max-width:100%;border-radius:8px;border:1px solid rgba(var(--accent-rgb),0.2);background:#fff;padding:12px}
.paper-fig.fig-sm img{max-width:620px}
.paper-fig .fig-cap{font-size:.82rem;color:#8fa4c0;margin-top:.5rem;max-width:800px;display:inline-block;text-align:left;line-height:1.5}
.paper-fig .fig-cap strong{color:var(--accent)}
.paper-fig-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:1.5rem 0}
.paper-fig-row .paper-fig{margin:0}
.paper-fig-row .paper-fig img{max-width:100%}

/* ===== LATEX ===== */
.math-block{background:rgba(30,30,46,.8);border:1px solid rgba(var(--accent-rgb),0.15);border-radius:8px;padding:1.2rem 1.5rem;margin:1rem 0;overflow-x:auto;text-align:center}
.math-block .eq-label{float:right;color:#8fa4c0;font-size:.85rem}

/* ===== FOOTER ===== */
footer{text-align:center;padding:3rem 2rem;color:#8fa4c0;font-size:.82rem;border-top:1px solid rgba(110,198,255,.12)}
footer a{color:#6ec6ff}

/* ===== RESPONSIVE ===== */
@media(max-width:768px){
  .hero h1{font-size:1.8rem}
  .container{padding:1rem}
  .cards{grid-template-columns:1fr}
  .grid-2{grid-template-columns:1fr}
  .paper-fig-row{grid-template-columns:1fr}
  pre{font-size:.75rem;padding:.7rem}
  nav ul{gap:0}
  nav ul li a{padding:.7rem .6rem;font-size:.78rem}
}
```

---

## 5. Page Components

### 5.1 Nav

```html
<nav>
  <ul>
    <li><a href="../../index.html">&larr; Agentic Survey</a></li>
    <li><a href="#section1">Section 1</a></li>
    <li class="lang-switch">
      <a onclick="setLang('en')" id="lang-en" class="active">EN</a>
      <a onclick="setLang('zh')" id="lang-zh">ZH</a>
    </li>
  </ul>
</nav>
```

Rules:
- First item **always** `← Agentic Survey` → `../../index.html`
- Last item **always** `.lang-switch` EN/ZH
- **NEVER** add `display:flex` on `nav` itself — only on `nav ul`

### 5.2 Hero

```html
<div class="hero">
  <h1>Paper Title</h1>
  <p class="sub"><span class="i18n" data-en="..." data-zh="...">Subtitle</span></p>
  <div class="badges">
    <span class="badge">arXiv:XXXX.XXXXX</span>
    <span class="badge">Venue Year</span>
    <span class="badge">Keyword</span>
  </div>
  <p style="color:#8fa4c0;font-size:.92rem;margin-top:1.2rem;position:relative;max-width:none">Authors</p>
  <p style="color:#6a7a94;font-size:.85rem;position:relative;max-width:none">Affiliations</p>
</div>
```

**CRITICAL rules:**
- `<h1>` NEVER inside badges div
- Institution names → affiliation `<p>`, NOT badges
- Standalone years → include in venue badge (e.g., "SOSP 2025")
- Only ONE `<div class="badges">`

### 5.3 Sections

```html
<section id="unique-id">
  <h2><span class="i18n" data-en="1. Title" data-zh="1. 標題">1. Title</span></h2>
  <p><span class="i18n" data-en="..." data-zh="...">Content</span></p>
</section>
```

- h2 numbered: `1.`, `2.`, ...
- h3 sub-numbered: `1.1`, `1.2`, ...

### 5.4 Footer

```html
<footer>
  <p><span class="i18n" data-en="Paper Title (arXiv:ID)" data-zh="...">...</span></p>
  <p><span class="i18n" data-en="Generated YYYY-MM-DD" data-zh="產生日期：YYYY-MM-DD">Generated YYYY-MM-DD</span></p>
</footer>
```

---

## 6. i18n Rules

- All visible text: `<span class="i18n" data-en="..." data-zh="...">English default</span>`
- `data-en`/`data-zh` values are set via `innerHTML` — can contain HTML (escape `<`/`>` as `&lt;`/`&gt;`)
- **Do NOT translate:** file paths, code identifiers, class/function names, command names, math formulas

---

## 7. Code Syntax Highlighting

No JS library. Use manual `<span>` classes:

| Class | Purpose | Color |
|-------|---------|-------|
| `.kw` | Keywords | `#cba6f7` purple |
| `.fn` | Function names | `#89b4fa` blue |
| `.cm` | Comments | `#6c7086` gray italic |
| `.st` | Strings | `#a6e3a1` green |
| `.nu` | Numbers | `#fab387` orange |

File path inline code:
- **Modified by paper** (red): `<code style="background:rgba(233,69,96,.12);border:1px solid rgba(233,69,96,.3);color:#e94560;padding:2px 8px;border-radius:4px">path</code>`
- **External** (green): `<code style="background:rgba(166,227,161,.1);border:1px solid rgba(166,227,161,.3);color:#a6e3a1;padding:2px 8px;border-radius:4px">path</code>`

---

## 8. Embedding Paper Figures

### 8.1 Sourcing from arXiv

Use the arXiv HTML version: `https://arxiv.org/html/{arxiv_id}v1/figures/{filename}.png`

**Workflow:**
1. `WebFetch` the arXiv HTML page → extract all `<img>` `src` URLs and captions
2. Select important figures: system architecture, key results, novel mechanisms
3. Skip trivial figures (simple notation tables, redundant diagrams)

### 8.2 CRITICAL: White Background

All paper figure images **MUST** have `background:#fff; padding:12px`. Original figures have dark text on light/transparent backgrounds — unreadable without white background on our dark theme.

### 8.3 Size Control

| Scenario | Class | Max width |
|----------|-------|-----------|
| Full-width (wide charts) | `paper-fig` | 100% of container |
| Too large / excess whitespace | `paper-fig fig-sm` | 620px |
| Two related figures side-by-side | Wrap in `paper-fig-row` | 50% each |

**Rule:** Architecture/overview/pipeline diagrams → `fig-sm`. Result charts → full width or `paper-fig-row` pairs.

### 8.4 Single Figure Template

```html
<div class="paper-fig fig-sm">
  <img src="https://arxiv.org/html/{id}v1/figures/{file}.png"
       alt="Figure N: description">
  <div class="fig-cap"><strong>Figure N (from paper):</strong>
    <span class="i18n" data-en="Caption EN" data-zh="Caption ZH">Caption EN</span>
  </div>
</div>
```

### 8.5 Side-by-Side Template

```html
<div class="paper-fig-row">
  <div class="paper-fig">
    <img src="..." alt="Figure Na: ...">
    <div class="fig-cap"><strong>Figure Na:</strong> <span class="i18n" data-en="..." data-zh="...">...</span></div>
  </div>
  <div class="paper-fig">
    <img src="..." alt="Figure Nb: ...">
    <div class="fig-cap"><strong>Figure Nb:</strong> <span class="i18n" data-en="..." data-zh="...">...</span></div>
  </div>
</div>
```

### 8.6 Placement Rules

- Architecture/design figures → Architecture section
- Result figures → Results section, before corresponding subsection
- Place **immediately before** the text that discusses the figure
- Thematically related figures go in the same `paper-fig-row`

---

## 9. KaTeX LaTeX Math

### 9.1 Inline Math

Use single `$` delimiters:

```html
the cost function $c_e = F(L_e)$ grows as $L_e$ rises
```

### 9.2 Display Equations

Use `$$` inside `.math-block` with optional equation label:

```html
<div class="math-block">
  <span class="eq-label">(1)</span>
  $$\min \; Z$$
</div>
```

Multi-line:
```html
<div class="math-block">
  <span class="eq-label">(2)</span>
  $$\sum_{e \in \text{out}(v)} x_{k,e} = \begin{cases} d_k & \text{if } v = s_k \\ 0 & \text{otherwise} \end{cases}$$
</div>
```

### 9.3 i18n Escaping for LaTeX

Inside `data-en`/`data-zh` attributes, **double-escape** backslashes:

```html
<span class="i18n"
  data-en="complexity $O(|K| \\cdot |N|)$"
  data-zh="複雜度 $O(|K| \\cdot |N|)$">
  complexity $O(|K| \cdot |N|)$
</span>
```

- Inner text (default): single `\` → `\cdot`
- `data-*` attributes: double `\\` → `\\cdot`

Reason: `setLang()` uses `innerHTML`, which interprets `\\` → `\`.

### 9.4 What to Convert vs Keep

**Convert to LaTeX ($):**
- Variables, symbols: `Z` → `$Z$`, `λ` → `$\lambda$`
- Functions: `F(L_e)` → `$F(L_e)$`, `O(|K|)` → `$O(|K|)$`
- Set notation: `∈`, `∀`, `ℤ≥0` → `$\in$`, `$\forall$`, `$\mathbb{Z}_{\geq 0}$`
- Subscripts: `x[k,e]` → `$x_{k,e}$`

**Keep as `<code>` (NOT LaTeX):**
- Code identifiers: `ncclSend`, `libnccl.so`
- Units: `55.4 GB/s`, `0.02 ms`
- CLI flags: `--nimble`, `-DNIMBLE`

---

## 10. Content Guide by Section

### Overview / Problem
- Problem description (2–4 sentences)
- Core contributions (numbered, bolded)
- Key insight (`.note` callout)
- Use `.card.hl` for contributions

### Architecture
- ≥1 colorful HTML/CSS diagram (`.vflow` or `.diagram`)
- Paper figures (architecture diagram, system design)
- Architectural insight in `.note`

### Repo Analysis (if repo exists)
- File tree (`.diagram`)
- Class → file → purpose table
- Red/green inline code for modified/external files

### Core Mechanisms
- Multiple sub-sections (4.1, 4.2, ...)
- Code blocks with syntax highlighting
- Flow diagrams for decision logic
- Mathematical formulations in KaTeX
- Paper figures for novel mechanisms

### Performance Results
- Results table with exact numbers
- Paper figures (bar charts, performance plots)
- `.metric-boxes` for headline numbers
- Caveats in `.note`

### Claims vs Implementation (if repo exists)
- Table with `.check` / `.partial` / `.cross`
- `.grid-2` for Strengths / Limitations

### How to Reproduce (if repo exists)
- Copy-pasteable setup commands
- Hardware requirements in `.warn`
- Key parameters table

---

## 11. Hard Lessons (Do NOT Repeat)

### Hero
- **NEVER** wrap `<h1>` inside `<div class="badges">`
- **NEVER** put institution names as badges
- **NEVER** put standalone years as badges

### Nav CSS
- **NEVER** add `display:flex` to `nav{}` — only to `nav ul{}`
- **NEVER** create malformed CSS selectors when editing

### Accent Colors
- **NEVER** use text colors (`#e2e8f0`, `#d0d5e0`) as accents
- Fallback by topic: cache→rose, distributed→cyan, attention→indigo, agent→teal

### Visual Verification (MANDATORY)
1. Make changes
2. Screenshot with Chrome headless:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --headless --disable-gpu --screenshot=/tmp/check.png \
     --window-size=1440,700 "file:///path/to/page.html" 2>/dev/null
   ```
3. Read screenshot, verify against continuum standard
4. Only then commit

---

## 12. Quality Checklist

### Structure
- [ ] ≥800 lines, single `.html`, all CSS in `<style>`
- [ ] Nav links match `<section id="...">`

### Theme
- [ ] Background `#0e0b12`, code bg `#1e1e2e`
- [ ] Accent uses `var(--accent)` not hardcoded

### Hero
- [ ] `<h1>` → `<p class="sub">` → `<div class="badges">` → authors → affiliation
- [ ] `.badge` has `text-transform:none`

### i18n
- [ ] All text bilingual, default English
- [ ] File paths / code not translated
- [ ] `<`/`>` escaped in `data-*` attributes

### Diagrams
- [ ] HTML/CSS only, no ASCII art
- [ ] ≥3 colors per diagram

### Paper Figures
- [ ] All `<img>` have `alt` with figure number
- [ ] White background (`background:#fff; padding:12px`)
- [ ] Oversized standalone figures use `fig-sm`
- [ ] Related pairs use `paper-fig-row`
- [ ] Bilingual captions

### LaTeX
- [ ] KaTeX CDN in `<head>` (3 tags)
- [ ] Display equations in `.math-block` with `.eq-label`
- [ ] Inline math uses `$...$`
- [ ] Double-escaped `\\` in `data-en`/`data-zh`

### Repo-Specific (if applicable)
- [ ] File tree, key classes table
- [ ] Claims vs Implementation with `.check`/`.partial`/`.cross`
- [ ] Reproduction steps

### Paper-Only (if no repo)
- [ ] Expanded architecture (multiple diagrams)
- [ ] Math formulations / pseudocode
- [ ] Deeper evaluation analysis

---

## 13. Commit & Push (MANDATORY final step)

After completing all changes and passing the checklist, **always** commit and push:

1. `git add papers/<slug>/index.html` (and any other changed files)
2. Commit with a descriptive message:
   ```bash
   git commit -m "$(cat <<'EOF'
   <slug>: <short description of what was done>

   Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```
3. `git push`

### Commit message conventions

| Action | Prefix example |
|--------|---------------|
| New page | `<slug>: add paper analysis page` |
| Add figures | `<slug>: embed paper figures (Fig 1-N) from arXiv` |
| Add LaTeX | `<slug>: convert math to KaTeX LaTeX` |
| Fix styling | `<slug>: fix hero/nav/accent styling` |
| Mixed | `<slug>: add figures and convert math to LaTeX` |

**Do NOT** forget to push — the site is deployed via GitHub Pages on every push to `master`.
