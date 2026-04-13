---
name: embed-paper-figures
description: Embed original figures from academic papers into paper analysis pages, and convert all mathematical formulas to KaTeX LaTeX. TRIGGER when: user asks to add paper figures, extract figures from a paper, add images to a paper page, or convert math/equations to LaTeX in a paper analysis page.
---

# Embed Paper Figures & LaTeX Math

This skill adds **original figures from the paper** and **KaTeX-rendered LaTeX equations** to paper analysis pages in the agentic-ai-survey project.

> **Prerequisite**: Read `PAPER_PAGE_GUIDE.md` first — this skill extends (not replaces) those conventions.

---

## 1. Sourcing Figures

### 1.1 Where to Get Figures

Use the **arXiv HTML version** of the paper as the image source:

```
https://arxiv.org/html/{arxiv_id}v1/figures/{filename}.png
```

**Workflow:**
1. Fetch `https://arxiv.org/html/{arxiv_id}v1` with `WebFetch`
2. Extract all `<img>` tag `src` attributes and their associated figure captions
3. Select the most important figures — prioritize:
   - **System architecture / design diagrams** (readers need these most)
   - **Key result figures** (performance comparisons, speedup charts)
   - **Algorithm / pipeline illustrations**
   - Skip trivial figures (e.g., simple notation tables, logos)

### 1.2 Which Figures to Include

Not every figure belongs. Select figures that:
- Show **system design** or **architecture** — these are hard to recreate in HTML/CSS and most valuable as original images
- Present **experimental results** (bar charts, line plots, heatmaps) — exact data matters
- Illustrate **novel mechanisms** specific to the paper

Skip figures that are:
- Simple text tables (recreate as HTML `<table>` instead)
- Generic background/related-work diagrams
- Redundant with HTML diagrams already on the page

---

## 2. CSS Requirements

Add the following CSS block inside the page's `<style>` tag, before the responsive media query section:

```css
/* ===== PAPER FIGURES ===== */
.paper-fig{margin:1.8rem 0;text-align:center}
.paper-fig img{max-width:100%;border-radius:8px;border:1px solid rgba(var(--accent-rgb),0.2);background:#fff;padding:12px}
.paper-fig.fig-sm img{max-width:620px}
.paper-fig .fig-cap{font-size:.82rem;color:#8fa4c0;margin-top:.5rem;max-width:800px;display:inline-block;text-align:left;line-height:1.5}
.paper-fig .fig-cap strong{color:var(--accent)}
.paper-fig-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:1.5rem 0}
.paper-fig-row .paper-fig{margin:0}
.paper-fig-row .paper-fig img{max-width:100%}
@media(max-width:768px){.paper-fig-row{grid-template-columns:1fr}}
```

### 2.1 Critical: White Background

All paper figures **MUST** have `background:#fff` and `padding:12px`. Original paper figures have dark text on light/transparent backgrounds — without the white background they are unreadable on our dark theme (`#0e0b12`).

### 2.2 Size Control

| Scenario | Class | Effect |
|----------|-------|--------|
| Standalone full-width figure (wide charts, results) | `paper-fig` | `max-width:100%` — fills container |
| Standalone figure that is too large or has excessive whitespace | `paper-fig fig-sm` | `max-width:620px` — compact |
| Two related figures side-by-side | Wrap in `paper-fig-row` | 2-column grid, auto 1-col on mobile |

**Rule of thumb:** Architecture diagrams, overview figures, and pipeline diagrams usually need `fig-sm`. Result charts (bar/line plots) are fine at full width, especially in `paper-fig-row` pairs.

---

## 3. HTML Templates

### 3.1 Single Figure

```html
<div class="paper-fig fig-sm">
  <img src="https://arxiv.org/html/{arxiv_id}v1/figures/{file}.png"
       alt="Figure N: short description">
  <div class="fig-cap"><strong>Figure N (from paper):</strong>
    <span class="i18n"
      data-en="English caption describing the figure."
      data-zh="中文圖說。">English caption describing the figure.</span>
  </div>
</div>
```

### 3.2 Side-by-Side Figures

```html
<div class="paper-fig-row">
  <div class="paper-fig">
    <img src="https://arxiv.org/html/{arxiv_id}v1/figures/{file_a}.png"
         alt="Figure Na: description">
    <div class="fig-cap"><strong>Figure Na:</strong>
      <span class="i18n" data-en="..." data-zh="...">...</span>
    </div>
  </div>
  <div class="paper-fig">
    <img src="https://arxiv.org/html/{arxiv_id}v1/figures/{file_b}.png"
         alt="Figure Nb: description">
    <div class="fig-cap"><strong>Figure Nb:</strong>
      <span class="i18n" data-en="..." data-zh="...">...</span>
    </div>
  </div>
</div>
```

### 3.3 Placement Rules

- Place figures **immediately before** the section that discusses them, or right after the section heading
- Architecture/system design figures go in the Architecture section
- Result figures go in the Results section, before the corresponding subsection
- Figures inside `paper-fig-row` should be thematically related (e.g., intra-node + inter-node, or two hotspot ratios)

---

## 4. KaTeX LaTeX Math

### 4.1 Setup

Add these three lines in `<head>`, before the `<style>` tag:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});"></script>
```

### 4.2 CSS for Display Math

Add to the `<style>` block:

```css
/* ===== LATEX ===== */
.math-block{background:rgba(30,30,46,.8);border:1px solid rgba(var(--accent-rgb),0.15);border-radius:8px;padding:1.2rem 1.5rem;margin:1rem 0;overflow-x:auto;text-align:center}
.math-block .eq-label{float:right;color:#8fa4c0;font-size:.85rem}
```

### 4.3 Usage Patterns

**Inline math** — use single `$`:
```html
the cost function $c_e = F(L_e)$ grows sharply as $L_e$ rises
```

**Display equations** — use `$$` inside a `.math-block` div:
```html
<div class="math-block">
  <span class="eq-label">(1)</span>
  $$\min \; Z$$
</div>
```

**Multi-line equations** (use `\begin{cases}` or `\begin{aligned}`):
```html
<div class="math-block">
  <span class="eq-label">(2)</span>
  $$\sum_{e \in \text{out}(v)} x_{k,e} - \sum_{e \in \text{in}(v)} x_{k,e} =
    \begin{cases} d_k & \text{if } v = s_k \\ -d_k & \text{if } v = t_k \\ 0 & \text{otherwise} \end{cases}$$
</div>
```

### 4.4 i18n Escaping

Inside `data-en` / `data-zh` attributes, LaTeX backslashes must be **double-escaped**:

```html
<span class="i18n"
  data-en="complexity is $O(|K| \\cdot |N|)$"
  data-zh="複雜度為 $O(|K| \\cdot |N|)$">
  complexity is $O(|K| \cdot |N|)$
</span>
```

- Inner text (default display): single backslash `\cdot`
- `data-en` / `data-zh` attributes: double backslash `\\cdot`

This is because `setLang()` uses `innerHTML` assignment, which interprets the attribute value as HTML, so the escaped backslash `\\` becomes `\` when rendered.

### 4.5 What to Convert

Convert **all** mathematical notation to LaTeX. This includes:
- Variables, symbols: `Z` → `$Z$`, `λ` → `$\lambda$`
- Functions, operators: `F(L_e)` → `$F(L_e)$`, `O(|K|)` → `$O(|K|)$`
- Set notation: `∈`, `∀`, `ℤ≥0` → `$\in$`, `$\forall$`, `$\mathbb{Z}_{\geq 0}$`
- Subscripts/superscripts: `x[k,e]` → `$x_{k,e}$`
- Formal equations from the paper → display math in `.math-block`

Do **NOT** convert:
- Code identifiers: `ncclSend`, `libnccl.so`, `benchmark.cc` — keep as `<code>`
- Units and measurements: `55.4 GB/s`, `0.02 ms` — keep as plain text
- Parameter flags: `--nimble`, `-DNIMBLE` — keep as `<code>`

---

## 5. Checklist

Before committing, verify:

- [ ] All `<img>` tags have `alt` attributes with figure number and brief description
- [ ] All figure captions use bilingual `<span class="i18n" data-en="..." data-zh="...">`
- [ ] All paper images display on white background (`background:#fff; padding:12px`)
- [ ] Large standalone figures use `fig-sm` class
- [ ] Related figure pairs use `paper-fig-row` for side-by-side layout
- [ ] KaTeX CDN is loaded in `<head>` (3 tags: CSS + JS + auto-render)
- [ ] All formal equations use `$$...$$` inside `.math-block` divs with `eq-label`
- [ ] All inline math uses `$...$` (not `<code>` or Unicode symbols)
- [ ] LaTeX in `data-en`/`data-zh` attributes uses double-escaped backslashes
- [ ] Page renders correctly on dark theme — no unreadable text on dark backgrounds

---

## 6. Reference Implementation

See `papers/nimble/index.html` for a complete working example with:
- 14 embedded arXiv figures (Fig 1–8, including sub-figures)
- MCF equations (1)–(5) in KaTeX display math
- Inline LaTeX for cost functions, complexity bounds, and symbols
- Mixed `fig-sm` and `paper-fig-row` layouts
