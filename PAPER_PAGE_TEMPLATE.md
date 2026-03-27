# Paper Analysis Page Template for the Agentic AI Survey

---

## 1. Overview

### What This Template Is For

This document provides a comprehensive, self-contained guide for any LLM to create a high-quality paper analysis page (`index.html`) for the Agentic AI KV Cache Management Survey. Each paper in the survey gets its own sub-directory under `papers/` with a single HTML file that provides an in-depth technical analysis.

### Quality Expectations

- **Minimum length:** 800 lines of HTML
- **Target length:** 1000-2000 lines (higher for papers with repos)
- **Maximum length:** ~2500 lines (avoid padding; every line should carry information)
- **Self-contained:** The entire page is a single `.html` file with all CSS inlined in a `<style>` block. No external CSS, no JavaScript, no images.
- **Colorful diagrams:** All architecture and flow diagrams must be built with HTML/CSS using colored `<div>` elements, flexbox, and grid. Absolutely no ASCII art.
- **Technical depth:** The page should be useful to a researcher trying to understand or reproduce the paper's contributions.

### The "Repo First, Paper Second" Methodology

When a paper has an open-source implementation:

1. **Explore the repo first.** Read the README, understand the directory structure, identify key source files, and trace the main algorithms through the code.
2. **Read the paper second.** Understand the claims, contributions, evaluation setup, and theoretical framework.
3. **Compare.** Identify where the implementation matches, simplifies, or diverges from the paper's claims. This comparison is one of the most valuable parts of the analysis.

When a paper does NOT have a repo:

1. **Read the paper thoroughly.** Extract architecture details, algorithms, evaluation methodology, and results.
2. **Focus on technical depth.** Since there is no code to compare against, go deeper on the paper's theoretical contributions, mathematical formulations, and evaluation analysis.
3. **Skip repo-specific sections.** Omit the "Repo Analysis" and "Paper vs Implementation" sections. Expand the architecture, mechanisms, and performance sections instead.

---

## 2. Complete CSS Template

Below is the canonical CSS to use. This is based on the light-background theme (used by the `continuum` page). You may adapt colors for variety, but keep the same structural classes.

```html
<style>
:root {
  --dark: #16213e;
  --mid: #0f3460;
  --primary: #e94560;
  --accent: #533483;
  --light: #f8f9fa;
  --text: #e0e0e0;
  --text-dark: #2d2d2d;
  --card-bg: #ffffff;
  --code-bg: #1e1e2e;
  --border: #e0e0e0;
  --success: #27ae60;
  --warn: #f39c12;
  --info: #3498db;
  --danger: #e74c3c;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #f4f5f7;
  color: var(--text-dark);
  line-height: 1.7;
}

/* ================================================
   HERO SECTION
   ================================================ */
.hero {
  background: linear-gradient(135deg, var(--dark) 0%, var(--mid) 50%, var(--accent) 100%);
  color: var(--text);
  padding: 80px 40px 60px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 70%, rgba(233,69,96,0.08) 0%, transparent 50%),
              radial-gradient(circle at 70% 30%, rgba(83,52,131,0.08) 0%, transparent 50%);
  animation: drift 20s linear infinite;
}
@keyframes drift { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.hero h1 {
  font-size: 2.4em;
  font-weight: 700;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
}
.hero .subtitle {
  font-size: 1.15em;
  opacity: 0.85;
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}
.badge-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}
.badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.badge-arxiv { background: var(--primary); color: #fff; }
.badge-venue { background: var(--accent); color: #fff; }
.badge-year { background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.badge-impl { background: var(--success); color: #fff; }
.badge a { color: #fff; text-decoration: none; }

/* ================================================
   STICKY NAVIGATION
   ================================================ */
.nav-sticky {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--dark);
  padding: 0 20px;
  display: flex;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.nav-sticky a {
  color: #ccc;
  text-decoration: none;
  padding: 14px 18px;
  font-size: 0.88em;
  font-weight: 500;
  transition: color 0.2s, border-bottom 0.2s;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
}
.nav-sticky a:hover {
  color: #fff;
  border-bottom: 2px solid var(--primary);
}

/* ================================================
   MAIN CONTENT LAYOUT
   ================================================ */
.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 30px 20px;
}

section {
  margin-bottom: 48px;
}

h2 {
  font-size: 1.7em;
  color: var(--dark);
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 3px solid var(--primary);
  display: inline-block;
}

h3 {
  font-size: 1.25em;
  color: var(--mid);
  margin: 24px 0 12px;
}

p { margin-bottom: 14px; }

/* ================================================
   CARDS
   ================================================ */
.card {
  background: var(--card-bg);
  border-radius: 10px;
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border-left: 5px solid var(--info);
}
.card.primary { border-left-color: var(--primary); }
.card.success { border-left-color: var(--success); }
.card.warn { border-left-color: var(--warn); }
.card.accent { border-left-color: var(--accent); }
.card.danger { border-left-color: var(--danger); }

.card h3 { margin-top: 0; }

/* ================================================
   CALLOUTS
   ================================================ */
.callout {
  padding: 16px 20px;
  border-radius: 8px;
  margin: 18px 0;
  font-size: 0.95em;
}
.callout-note {
  background: #e8f4fd;
  border-left: 4px solid var(--info);
  color: #1a5276;
}
.callout-warn {
  background: #fef9e7;
  border-left: 4px solid var(--warn);
  color: #7d6608;
}
.callout-info {
  background: #eaf7ef;
  border-left: 4px solid var(--success);
  color: #1e6b3e;
}
.callout-danger {
  background: #fdedec;
  border-left: 4px solid var(--danger);
  color: #922b21;
}

/* ================================================
   CODE BLOCKS
   ================================================ */
pre {
  background: var(--code-bg);
  color: #cdd6f4;
  padding: 20px 24px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.88em;
  line-height: 1.6;
  margin: 14px 0 18px;
}
code {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.9em;
}
p code, li code, td code {
  background: #eef1f7;
  padding: 2px 7px;
  border-radius: 4px;
  color: var(--mid);
}

/* Syntax highlighting classes */
.kw { color: #cba6f7; }  /* keywords - purple */
.fn { color: #89b4fa; }  /* functions - blue */
.cm { color: #6c7086; }  /* comments - gray */
.st { color: #a6e3a1; }  /* strings - green */
.nu { color: #fab387; }  /* numbers - orange */
.op { color: #89dceb; }  /* operators - cyan */
.ty { color: #f9e2af; }  /* types - yellow */
.bi { color: #f38ba8; }  /* builtins - pink */

/* ================================================
   TABLES
   ================================================ */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 24px;
  font-size: 0.92em;
}
th {
  background: var(--dark);
  color: #fff;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
}
td {
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}
tr:nth-child(even) { background: #f8f9fa; }
tr:hover { background: #eef1f7; }

/* ================================================
   DIAGRAM STYLES
   ================================================ */
.diagram-container {
  background: #f8f9fb;
  border-radius: 12px;
  padding: 32px 24px;
  margin: 20px 0 28px;
  border: 1px solid #e0e4eb;
  overflow-x: auto;
}
.diagram-title {
  text-align: center;
  font-weight: 700;
  font-size: 1.05em;
  color: var(--dark);
  margin-bottom: 24px;
}

/* Block Diagram Shared Styles */
.block {
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 0.85em;
  font-weight: 600;
  text-align: center;
  color: #fff;
  position: relative;
}
.block-dark { background: var(--dark); }
.block-mid { background: var(--mid); }
.block-primary { background: var(--primary); }
.block-accent { background: var(--accent); }
.block-success { background: var(--success); }
.block-info { background: var(--info); }
.block-warn { background: var(--warn); color: var(--text-dark); }
.block-light {
  background: #fff;
  color: var(--text-dark);
  border: 2px solid #d0d5dd;
}

.block-sm {
  padding: 8px 12px;
  font-size: 0.78em;
  border-radius: 6px;
}

/* Arrows */
.arrow-down {
  text-align: center;
  font-size: 1.6em;
  color: #888;
  line-height: 1.2;
  margin: 6px 0;
}
.arrow-right {
  display: flex;
  align-items: center;
  color: #888;
  font-size: 1.6em;
  margin: 0 8px;
}
.arrow-label {
  font-size: 0.7em;
  color: #666;
  text-align: center;
  font-weight: 500;
  margin: 2px 0;
}

/* Flow Layouts */
.flow-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 10px 0;
}
.flow-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

/* Architecture Diagram Styles */
.arch-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  max-width: 880px;
  margin: 0 auto;
}
.arch-layer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
}
.arch-box {
  border-radius: 10px;
  padding: 16px 22px;
  font-size: 0.88em;
  text-align: center;
  min-width: 140px;
}
.arch-box .sub {
  font-size: 0.8em;
  opacity: 0.8;
  font-weight: 400;
  display: block;
  margin-top: 4px;
}

/* File tree (for repo analysis) */
.file-tree {
  background: var(--code-bg);
  color: #cdd6f4;
  padding: 20px 24px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.84em;
  line-height: 1.9;
}
.file-tree .dir { color: #89b4fa; }
.file-tree .file { color: #a6e3a1; }
.file-tree .note { color: #6c7086; font-style: italic; }

/* Comparison checkmarks */
.check { color: var(--success); font-weight: bold; }
.cross { color: var(--danger); font-weight: bold; }
.partial { color: var(--warn); font-weight: bold; }

/* Grid layout for side-by-side */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 768px) {
  .grid-2 { grid-template-columns: 1fr; }
  .hero h1 { font-size: 1.6em; }
  .nav-sticky { flex-wrap: wrap; }
  .nav-sticky a { padding: 10px 12px; font-size: 0.82em; }
}

/* Metric boxes for key numbers */
.metric-box {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.metric-box .value {
  font-size: 2em;
  font-weight: 700;
  color: var(--primary);
}
.metric-box .label {
  font-size: 0.88em;
  color: #666;
  margin-top: 4px;
}
</style>
```

### Alternative: Dark Theme CSS

If you prefer a dark-themed page (used by the `vllm` and `dualpath` pages), change the `:root` variables and body styles:

```css
:root {
  --dark: #16213e;
  --mid: #0f3460;
  --primary: #e94560;
  --green: #2ecc71;
  --amber: #f5a623;
  --purple: #9b59b6;
  --code-bg: #1e1e2e;
  --card-bg: #1a2744;
  --text: #e0e0e0;
  --text-muted: #a0aec0;
  --border: #2d3e5e;
  --surface: #1e2d4a;
}

body {
  background: var(--dark);
  color: var(--text);
}

/* Adjust table for dark theme */
th { background: var(--mid); }
td { border-bottom-color: var(--border); }
tr:nth-child(even) { background: rgba(255,255,255,0.03); }
tr:hover { background: rgba(233, 69, 96, 0.04); }

/* Adjust cards for dark theme */
.card { background: var(--card-bg); border-left-color: var(--primary); }
.card.green { border-left-color: var(--green); }
.card.amber { border-left-color: var(--amber); }
.card.purple { border-left-color: var(--purple); }

/* Adjust inline code for dark theme */
p code, li code, td code {
  background: var(--code-bg);
  color: #cba6f7;
  padding: 2px 7px;
  border-radius: 4px;
}

/* Adjust diagram container for dark theme */
.diagram-container {
  background: var(--surface);
  border-color: var(--border);
}
.diagram-title { color: var(--amber); }
```

---

## 3. HTML Structure Template

Below is the complete skeleton. Every section is annotated with comments explaining its purpose.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[PAPER SHORT NAME] - Technical Analysis</title>
<style>
  /* === PASTE THE FULL CSS FROM SECTION 2 HERE === */
</style>
</head>
<body>

<!-- ============================================ -->
<!-- HERO SECTION                                 -->
<!-- ============================================ -->
<div class="hero">
  <h1>[Full Paper Title]</h1>
  <p class="subtitle">[One-sentence summary of the paper's core contribution]</p>
  <div class="badge-row">
    <span class="badge badge-arxiv"><a href="https://arxiv.org/abs/[ARXIV_ID]" target="_blank">arXiv:[ARXIV_ID]</a></span>
    <span class="badge badge-venue">[Venue Name, e.g. "SOSP '23" or "Systems / ML Serving"]</span>
    <span class="badge badge-year">[Year]</span>
    <!-- Include one of these if applicable: -->
    <span class="badge badge-impl">[Implementation note, e.g. "Built on vLLM" or "Open Source"]</span>
  </div>
</div>

<!-- ============================================ -->
<!-- STICKY NAVIGATION                            -->
<!-- ============================================ -->
<nav class="nav-sticky">
  <a href="#overview">Overview</a>
  <a href="#architecture">Architecture</a>
  <!-- Include if paper has a repo: -->
  <a href="#repo">Repo Analysis</a>
  <a href="#mechanisms">Core Mechanisms</a>
  <a href="#performance">Results</a>
  <!-- Include if paper has a repo: -->
  <a href="#claims">Claims vs Code</a>
  <a href="#reproduce">Reproduce</a>
</nav>

<div class="container">

<!-- ============================================ -->
<!-- SECTION 1: OVERVIEW                          -->
<!-- ============================================ -->
<section id="overview">
  <h2>Paper Overview</h2>

  <div class="card primary">
    <h3>The Problem</h3>
    <p>[2-4 sentences describing the problem this paper addresses. Be specific about
    what limitation or bottleneck exists in current systems.]</p>
  </div>

  <div class="card success">
    <h3>Key Contributions</h3>
    <ol>
      <li><strong>[Contribution 1 name]:</strong> [Description]</li>
      <li><strong>[Contribution 2 name]:</strong> [Description]</li>
      <li><strong>[Contribution 3 name]:</strong> [Description]</li>
    </ol>
  </div>

  <div class="card accent">
    <h3>Evaluation Summary</h3>
    <p>[Summary of evaluation setup: models used, hardware, benchmarks, and headline
    result number. Include the specific claim, e.g. "achieves 2.16x improvement..."]</p>
  </div>
</section>

<!-- ============================================ -->
<!-- SECTION 2: SYSTEM ARCHITECTURE               -->
<!-- ============================================ -->
<section id="architecture">
  <h2>System Architecture</h2>

  <p>[1-2 sentences introducing the architecture and its key components.]</p>

  <!-- ARCHITECTURE DIAGRAM (see Section 4 for diagram guidelines) -->
  <div class="diagram-container">
    <div class="diagram-title">[System Name] Architecture</div>
    <div class="arch-grid">

      <!-- Layer 1: Top-level component -->
      <div class="arch-layer">
        <div class="arch-box block-dark" style="min-width:340px;">
          [Component Name]
          <span class="sub">[Brief description of what this component does]</span>
        </div>
      </div>

      <div class="arrow-down">&#9660;</div>
      <div class="arrow-label">[Label describing the data/control flow]</div>

      <!-- Layer 2: Middle components -->
      <div class="arch-layer">
        <div class="arch-box block-primary" style="min-width:200px;">
          [Component A]
          <span class="sub">[Description]</span>
        </div>
        <div class="arch-box block-accent" style="min-width:200px;">
          [Component B]
          <span class="sub">[Description]</span>
        </div>
        <div class="arch-box block-success" style="min-width:200px;">
          [Component C]
          <span class="sub">[Description]</span>
        </div>
      </div>

      <div class="arrow-down">&#9660;</div>

      <!-- Layer 3: Bottom component -->
      <div class="arch-layer">
        <div class="arch-box block-primary" style="min-width:420px; background: linear-gradient(90deg, var(--primary), var(--accent));">
          [Hardware / Execution Layer]
          <span class="sub">[Description]</span>
        </div>
      </div>

    </div>
  </div>

  <div class="callout callout-note">
    <strong>Key insight:</strong> [One important architectural insight from the paper.]
  </div>
</section>

<!-- ============================================ -->
<!-- SECTION 3: REPO ANALYSIS (if repo exists)    -->
<!-- ============================================ -->
<section id="repo">
  <h2>Repo Implementation Analysis</h2>

  <h3>Repository Structure</h3>
  <p>[Brief description of the repo and how it is organized.]</p>

  <div class="file-tree">
    <span class="dir">[repo-name]/</span><br>
    &nbsp;&nbsp;<span class="dir">[subdir]/</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="file">[file.py]</span> <span class="note"># [Description of this file's purpose]</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="file">[file2.py]</span> <span class="note"># [Description]</span><br>
    &nbsp;&nbsp;<span class="dir">[subdir2]/</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="file">[file3.py]</span> <span class="note"># [Description]</span><br>
  </div>

  <h3>Key Classes and Their Roles</h3>

  <table>
    <thead>
      <tr>
        <th>Class</th>
        <th>File</th>
        <th>Purpose</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>[ClassName]</code></td>
        <td>[filename.py]</td>
        <td>[What this class does and its key methods]</td>
      </tr>
      <!-- Add more rows as needed -->
    </tbody>
  </table>
</section>

<!-- ============================================ -->
<!-- SECTION 4: CORE MECHANISMS                   -->
<!-- ============================================ -->
<section id="mechanisms">
  <h2>Core Mechanisms</h2>

  <!-- Mechanism 1 -->
  <h3>[4.1 Mechanism Name]</h3>

  <div class="card primary">
    <h3>[How This Mechanism Works]</h3>
    <p>[2-3 sentences explaining the mechanism at a high level.]</p>
  </div>

  <!-- Code snippet from the repo or pseudocode from the paper -->
  <pre><span class="cm"># [file reference, e.g. scheduler.py -- method_name() [lines X-Y]]</span>
<span class="kw">def</span> <span class="fn">method_name</span>(<span class="ty">self</span>, param: <span class="ty">Type</span>):
    <span class="cm"># [Comment explaining key logic]</span>
    <span class="kw">if</span> condition:
        <span class="kw">return</span> result
    <span class="ty">self</span>.something.<span class="fn">do_work</span>(param)</pre>

  <!-- Flow diagram for the mechanism -->
  <div class="diagram-container">
    <div class="diagram-title">[Mechanism Name] Decision Flow</div>
    <div class="flow-col">
      <div class="block block-mid" style="min-width:280px;">[Starting state]</div>
      <div class="arrow-down">&#9660;</div>
      <div class="block block-warn block-sm" style="min-width:180px; padding:12px;">[Decision point?]</div>
      <div style="display:flex; gap:40px;">
        <div class="flow-col">
          <div class="arrow-label">Yes</div>
          <div class="arrow-down" style="font-size:1.2em;">&#9660;</div>
          <div class="block block-success block-sm">[Action A]</div>
        </div>
        <div class="flow-col">
          <div class="arrow-label">No</div>
          <div class="arrow-down" style="font-size:1.2em;">&#9660;</div>
          <div class="block block-danger block-sm">[Action B]</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Add more mechanisms (4.2, 4.3, etc.) following the same pattern -->
</section>

<!-- ============================================ -->
<!-- SECTION 5: PERFORMANCE RESULTS               -->
<!-- ============================================ -->
<section id="performance">
  <h2>Performance Results</h2>

  <h3>[Benchmark Name] ([Setup details])</h3>

  <!-- Key metrics as metric boxes -->
  <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:16px; margin:20px 0;">
    <div class="metric-box">
      <div class="value">[X.Xx]</div>
      <div class="label">[Metric Name]</div>
    </div>
    <div class="metric-box">
      <div class="value">[Y.Ys]</div>
      <div class="label">[Metric Name]</div>
    </div>
    <div class="metric-box">
      <div class="value">[Z%]</div>
      <div class="label">[Metric Name]</div>
    </div>
  </div>

  <!-- Results table -->
  <table>
    <thead>
      <tr>
        <th>Metric</th>
        <th>Baseline</th>
        <th>[System Name]</th>
        <th>Improvement</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>[Metric 1]</td>
        <td>[Baseline value]</td>
        <td>[System value]</td>
        <td><strong>[Improvement]</strong></td>
      </tr>
      <!-- Add more rows -->
    </tbody>
  </table>

  <div class="callout callout-note">
    <strong>Note:</strong> [Any caveats, observations, or context about the results.]
  </div>
</section>

<!-- ============================================ -->
<!-- SECTION 6: CLAIMS VS IMPLEMENTATION          -->
<!-- (Only include if paper has a repo)           -->
<!-- ============================================ -->
<section id="claims">
  <h2>Paper Claims vs Implementation</h2>

  <table>
    <thead>
      <tr>
        <th>Paper Claim</th>
        <th>Status</th>
        <th>Code Evidence</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>[Claim from the paper]</td>
        <td><span class="check">YES</span></td>
        <td>[Reference to specific code that implements this claim]</td>
      </tr>
      <tr>
        <td>[Another claim]</td>
        <td><span class="partial">PARTIAL</span></td>
        <td>[Explanation of how the implementation simplifies or diverges from the claim]</td>
      </tr>
      <tr>
        <td>[Another claim]</td>
        <td><span class="cross">NO</span></td>
        <td>[Explanation of what is missing]</td>
      </tr>
    </tbody>
  </table>

  <!-- Strengths and Limitations side-by-side -->
  <h3>Implementation Maturity Assessment</h3>
  <div class="grid-2">
    <div class="card success">
      <h3>Strengths</h3>
      <ul>
        <li>[Strength 1]</li>
        <li>[Strength 2]</li>
      </ul>
    </div>
    <div class="card warn">
      <h3>Limitations</h3>
      <ul>
        <li>[Limitation 1]</li>
        <li>[Limitation 2]</li>
      </ul>
    </div>
  </div>
</section>

<!-- ============================================ -->
<!-- SECTION 7: HOW TO REPRODUCE                  -->
<!-- ============================================ -->
<section id="reproduce">
  <h2>How to Reproduce</h2>

  <h3>Step 1: Environment Setup</h3>
  <pre><span class="cm"># Clone the repository</span>
git clone &lt;repo-url&gt;
<span class="kw">cd</span> [repo-name]

<span class="cm"># Install dependencies</span>
pip install -e .</pre>

  <h3>Step 2: Run the System</h3>
  <pre><span class="cm"># [Command description]</span>
[command] --arg1 value1 --arg2 value2</pre>

  <h3>Step 3: Evaluate</h3>
  <pre><span class="cm"># [Run evaluation]</span>
[evaluation command]</pre>

  <div class="callout callout-warn">
    <strong>Hardware Requirements:</strong> [List required GPUs, memory, etc.]
  </div>

  <h3>Key Configuration Parameters</h3>
  <table>
    <thead>
      <tr>
        <th>Parameter</th>
        <th>Description</th>
        <th>Default</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>[--param]</code></td>
        <td>[What this parameter controls]</td>
        <td><code>[default value]</code></td>
      </tr>
    </tbody>
  </table>
</section>

</div> <!-- /container -->

<!-- ============================================ -->
<!-- FOOTER                                       -->
<!-- ============================================ -->
<div style="background:var(--dark); color:#888; text-align:center; padding:24px; font-size:0.85em;">
  Technical analysis of arXiv:[ARXIV_ID]. [Additional context about the paper.]
  <br>Analysis based on source code inspection and paper review.
</div>

</body>
</html>
```

---

## 4. Diagram Guidelines

### CRITICAL RULE: No ASCII Art

Never use ASCII art for diagrams. All diagrams must be built with HTML elements and CSS. Use colored `<div>` blocks, flexbox for layout, and Unicode arrows (&#9660; for down, &#9654; for right, &#8594; for arrow) for flow.

### Pattern 1: Architecture Diagram (Layered, Top-to-Bottom)

Use the `.arch-grid` + `.arch-layer` + `.arch-box` pattern. Each layer is a horizontal row of colored boxes connected by downward arrows.

```html
<div class="diagram-container">
  <div class="diagram-title">System Architecture</div>
  <div class="arch-grid">

    <!-- Layer 1 -->
    <div class="arch-layer">
      <div class="arch-box block-dark" style="min-width:340px;">
        Client Layer
        <span class="sub">Sends requests to the server</span>
      </div>
    </div>

    <div class="arrow-down">&#9660;</div>
    <div class="arrow-label">REST API / gRPC</div>

    <!-- Layer 2: Multiple components side by side -->
    <div class="arch-layer">
      <div class="arch-box block-primary" style="min-width:200px;">
        Scheduler
        <span class="sub">Request ordering and batching</span>
      </div>
      <div class="arch-box block-accent" style="min-width:200px;">
        Cache Manager
        <span class="sub">KV block allocation</span>
      </div>
    </div>

    <div class="arrow-down">&#9660;</div>

    <!-- Layer 3: Wide component with gradient -->
    <div class="arch-layer">
      <div class="arch-box block-primary" style="min-width:420px; background: linear-gradient(90deg, var(--primary), var(--accent));">
        GPU Execution Engine
        <span class="sub">Model forward pass with tensor parallelism</span>
      </div>
    </div>

  </div>
</div>
```

### Pattern 2: Flow Diagram (Decision Tree)

Use `.flow-col` for vertical flow and nested `<div style="display:flex; gap:40px;">` for branching.

```html
<div class="diagram-container">
  <div class="diagram-title">Decision Flow</div>
  <div class="flow-col">
    <div class="block block-mid" style="min-width:280px;">Request arrives</div>
    <div class="arrow-down">&#9660;</div>

    <div class="block block-warn block-sm" style="min-width:180px; padding:12px;">Cache hit?</div>

    <div style="display:flex; gap:40px;">
      <div class="flow-col">
        <div class="arrow-label">Yes</div>
        <div class="arrow-down" style="font-size:1.2em;">&#9660;</div>
        <div class="block block-success block-sm">Load from cache</div>
      </div>
      <div class="flow-col">
        <div class="arrow-label">No</div>
        <div class="arrow-down" style="font-size:1.2em;">&#9660;</div>
        <div class="block block-danger block-sm">Full recomputation</div>
      </div>
    </div>
  </div>
</div>
```

### Pattern 3: Comparison Diagram (Side-by-Side)

Use `.grid-2` or inline flex to show before/after or two approaches side by side.

```html
<div class="diagram-container">
  <div class="diagram-title">Before vs After Comparison</div>
  <div class="grid-2" style="gap:2rem;">

    <!-- Left: Before -->
    <div style="text-align:center;">
      <div style="font-weight:700; color:var(--danger); margin-bottom:1rem;">Before: Baseline System</div>
      <div style="display:flex; flex-direction:column; gap:0.5rem; align-items:center;">
        <div class="block block-danger block-sm" style="width:80%;">Contiguous allocation</div>
        <div style="font-size:0.75em; color:#666;">wastes memory</div>
        <div class="block block-danger block-sm" style="width:80%;">Internal fragmentation</div>
      </div>
    </div>

    <!-- Right: After -->
    <div style="text-align:center;">
      <div style="font-weight:700; color:var(--success); margin-bottom:1rem;">After: Proposed System</div>
      <div style="display:flex; flex-direction:column; gap:0.5rem; align-items:center;">
        <div class="block block-success block-sm" style="width:80%;">Block-level allocation</div>
        <div style="font-size:0.75em; color:#666;">near-zero waste</div>
        <div class="block block-success block-sm" style="width:80%;">Dynamic growth</div>
      </div>
    </div>

  </div>
</div>
```

### Pattern 4: Timeline / Pipeline Diagram

Use a horizontal flex with colored segments to show temporal or pipeline stages.

```html
<div class="diagram-container">
  <div class="diagram-title">Request Lifecycle Timeline</div>
  <div style="display:flex; align-items:stretch; border-radius:8px; overflow:hidden; height:52px; border:2px solid #d0d5dd;">
    <div style="flex:2; background:var(--info); display:flex; align-items:center; justify-content:center; font-size:0.78em; font-weight:600; color:#fff; padding:0 12px; white-space:nowrap;">
      Phase 1: Prefill
    </div>
    <div style="flex:1.5; background:var(--success); display:flex; align-items:center; justify-content:center; font-size:0.78em; font-weight:600; color:#fff; padding:0 12px; white-space:nowrap;">
      Phase 2: Decode
    </div>
    <div style="flex:0.5; background:var(--warn); display:flex; align-items:center; justify-content:center; font-size:0.78em; font-weight:600; color:var(--text-dark); padding:0 12px; white-space:nowrap;">
      Tool Call
    </div>
    <div style="flex:2; background:var(--info); display:flex; align-items:center; justify-content:center; font-size:0.78em; font-weight:600; color:#fff; padding:0 12px; white-space:nowrap;">
      Phase 3: Resume
    </div>
  </div>
  <div style="display:flex; justify-content:space-between; font-size:0.78em; color:#666; padding:0 4px; margin-top:4px;">
    <span>t=0</span>
    <span>Prefill complete</span>
    <span>Pause</span>
    <span>Resume decode</span>
  </div>
</div>
```

### Pattern 5: Inline Component Boxes (for hardware or node layouts)

Use inline styles with flexbox for hardware/topology diagrams.

```html
<div class="diagram-container">
  <div class="diagram-title">Hardware Configuration</div>
  <div style="display:flex; gap:1.5rem; justify-content:center; flex-wrap:wrap;">

    <div style="display:flex; flex-direction:column; gap:0.5rem; align-items:center;">
      <div style="font-size:0.85em; font-weight:700; color:var(--primary);">Node 1</div>
      <div style="display:flex; gap:6px;">
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:6px; padding:8px 12px; color:#fff; font-size:0.75em; font-weight:700;">GPU 0</div>
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:6px; padding:8px 12px; color:#fff; font-size:0.75em; font-weight:700;">GPU 1</div>
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:6px; padding:8px 12px; color:#fff; font-size:0.75em; font-weight:700;">GPU 2</div>
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:6px; padding:8px 12px; color:#fff; font-size:0.75em; font-weight:700;">GPU 3</div>
      </div>
      <div style="font-size:0.72em; color:#888;">NVLink interconnect</div>
    </div>

  </div>
</div>
```

### Color Usage Rules

- **Use background colors from CSS variables** (`var(--primary)`, `var(--success)`, etc.) or inline gradients.
- **Make sure every diagram has at least 3 distinct colors.** Monochrome diagrams look dull.
- **Use gradients** (`linear-gradient(135deg, color1, color2)`) for important or highlighted components.
- **Decision nodes** should use `block-warn` (yellow/orange) to visually stand out.
- **Positive outcomes** should use `block-success` (green).
- **Negative outcomes** should use `block-danger` (red).

---

## 5. Workflow Instructions

### For Papers WITH a Repository

Follow these steps in order:

**Step 1: Explore the Repository**

- Read the `README.md` for installation, usage, and architecture overview.
- Use `find` or `ls -R` to understand the directory structure.
- Identify the key source files (the main algorithm implementation, not utilities or tests).
- Read the core source files thoroughly. Understand:
  - What data structures are used?
  - What is the main algorithm loop?
  - How is the system configured?
  - What are the entry points?

**Step 2: Read the Paper PDF**

- Extract the paper's claims, contributions, and evaluation methodology.
- Note specific numbers (throughput improvements, latency reductions, etc.).
- Understand the theoretical framework or model.
- Identify the evaluation benchmarks and hardware.

**Step 3: Compare Paper Claims vs Code**

For each major claim in the paper, check:
- Is it implemented in the code? (YES / PARTIAL / NO)
- If partially implemented, what is simplified?
- If not implemented, what is the gap?

**Step 4: Write the HTML File**

- Start with the complete HTML skeleton from Section 3.
- Fill in each section with the information gathered.
- Create colorful diagrams for the architecture and key mechanisms.
- Include code snippets from the repo with syntax highlighting.
- Build the claims-vs-implementation comparison table.
- Write reproduction instructions based on the README and your analysis.

**Step 5: Review and Polish**

- Verify all code snippets are accurate (file names, line numbers, method names).
- Make sure diagrams are colorful and informative.
- Check that the page is self-contained (no external dependencies).
- Confirm the page is at least 800 lines long.

### For Papers WITHOUT a Repository

Follow these steps:

**Step 1: Read the Paper PDF Thoroughly**

- Extract every technical detail: architecture, algorithms, mathematical formulations.
- Note all evaluation details: benchmarks, hardware, baselines, metrics.
- Understand the paper's positioning relative to prior work.

**Step 2: Write the HTML File**

- Use the same HTML skeleton from Section 3, but:
  - **Omit** the `#repo` (Repo Analysis) section.
  - **Omit** the `#claims` (Claims vs Code) section.
  - **Omit** the `#reproduce` section (or replace it with a "Theoretical Reproducibility" section if the paper provides enough detail for someone to re-implement).
  - **Expand** the `#architecture` section with more detailed diagrams.
  - **Expand** the `#mechanisms` section with deeper technical analysis.
  - Add a `#significance` or `#impact` section discussing the paper's importance to the field.

**Step 3: Compensate for Missing Repo Content**

Since repo-based pages naturally have more content (file trees, code snippets, comparison tables), paper-only pages need to compensate with:
- More detailed architecture diagrams (multiple diagrams showing different aspects).
- Mathematical formulation sections with pseudocode.
- Deeper analysis of evaluation methodology.
- Comparison with related work.
- Discussion of limitations and future directions.

---

## 6. Section-by-Section Content Guide

### Section: Hero

**Purpose:** Immediate visual identity and key metadata for the paper.

**Required content:**
- Paper title (full, as it appears on arXiv)
- One-sentence subtitle summarizing the contribution
- Badge for arXiv link (clickable)
- Badge for venue (conference/workshop name with year)
- Badge for year
- Optional badge for implementation status ("Built on vLLM", "Open Source", "Foundational Paper")

**Detail level:** Minimal text -- badges and title only. The hero should be scannable in 3 seconds.

**Example:**
```html
<div class="hero">
  <h1>Efficient Memory Management for Large Language Model Serving with PagedAttention</h1>
  <p class="subtitle">Foundation of modern LLM serving through OS-inspired virtual memory management for KV cache</p>
  <div class="badge-row">
    <span class="badge badge-arxiv"><a href="https://arxiv.org/abs/2309.06180" target="_blank">arXiv:2309.06180</a></span>
    <span class="badge badge-venue">SOSP '23</span>
    <span class="badge badge-year">2023</span>
    <span class="badge badge-impl">Foundational Paper</span>
  </div>
</div>
```

### Section: Overview

**Purpose:** Establish context -- what problem exists, what the paper does about it, and what the results show.

**Required content:**
- **Problem card** (`.card.primary`): 2-4 sentences describing the problem. Be specific about metrics or examples.
- **Contributions card** (`.card.success`): Numbered list of 3-5 contributions. Each should be a bolded name + description.
- **Evaluation summary card** (`.card.accent`): Setup (models, GPUs, benchmarks) and headline result.

**Detail level:** Medium. Each card should be 3-6 sentences. Use `<code>` for system names and technical terms.

### Section: Architecture

**Purpose:** Show how the system is structured. This is where the most important diagram goes.

**Required content:**
- 1-2 introductory sentences.
- **At least one colorful architecture diagram** showing the main components and data flow.
- A callout highlighting a key architectural insight.
- Optional: a second diagram showing a specific sub-component in more detail.

**Detail level:** High. The architecture diagram should show every major component mentioned in the paper. Use `.arch-box` with different colors for different types of components (e.g., blue for scheduler, green for cache, red for execution).

### Section: Repo Analysis (if repo exists)

**Purpose:** Map the paper's abstract concepts to concrete code.

**Required content:**
- **File tree** showing the repo structure with annotations for key files.
- **Table** mapping class names to files and purposes.
- Brief description of the implementation approach.

**Detail level:** High. Include file paths, class names, and method names. A reader should be able to navigate the codebase after reading this section.

### Section: Core Mechanisms

**Purpose:** Deep dive into how the system actually works.

**Required content:**
- **Multiple sub-sections** (4.1, 4.2, etc.), one per key mechanism.
- For each mechanism:
  - A card explaining what it does and why.
  - A code block showing the actual implementation (with syntax highlighting) or pseudocode.
  - A flow diagram showing the decision logic.
- At least 2-3 mechanisms should be covered.

**Detail level:** Very high. This is the longest and most important section. Include real code from the repo (with file and line number references) or detailed pseudocode from the paper. Every mechanism should have both a textual explanation and a visual diagram.

### Section: Performance Results

**Purpose:** Present the paper's evaluation results with context.

**Required content:**
- **Metric boxes** showing 3-4 headline numbers.
- **Results table** comparing the proposed system against baselines.
- **Callout** with caveats, observations, or context.

**Detail level:** Medium-high. Include specific numbers from the paper. Do not just state "faster" -- give exact numbers (e.g., "2.16x improvement in average job completion time").

### Section: Claims vs Code (if repo exists)

**Purpose:** The most valuable part of the analysis -- honest comparison of paper promises vs code reality.

**Required content:**
- **Comparison table** with columns: Paper Claim, Status (YES/PARTIAL/NO), Code Evidence.
- Use `.check` (green), `.partial` (yellow), `.cross` (red) for status indicators.
- **Strengths/Limitations grid** using `.grid-2` with two cards.
- A callout discussing the most significant gap or simplification.

**Detail level:** Very high. Be specific about code evidence -- reference exact class names, method names, and file locations. This section distinguishes a thorough analysis from a superficial one.

### Section: How to Reproduce (if repo exists)

**Purpose:** A practical guide for reproducing the paper's results.

**Required content:**
- Step-by-step setup commands in code blocks.
- Server launch commands.
- Evaluation commands.
- Hardware requirements callout.
- Configuration parameters table.

**Detail level:** Medium. Commands should be copy-pasteable. Include the most important configuration parameters and their defaults.

### Section: Footer

**Purpose:** Attribution and context.

**Required content:**
- Paper citation (arXiv ID, authors, venue).
- Statement that this is part of the Agentic AI survey.

**Detail level:** Low. 2-3 lines is sufficient.

---

## 7. Quality Checklist

Before finalizing any paper analysis page, verify ALL of the following:

### Structure
- [ ] Page is at least 800 lines of HTML
- [ ] Page is self-contained (single `.html` file, no external CSS/JS/images)
- [ ] All CSS is in a `<style>` block in `<head>`
- [ ] DOCTYPE, charset, and viewport meta tags are present
- [ ] All sections listed in the nav bar have corresponding `id` attributes

### Hero Section
- [ ] Full paper title in `<h1>`
- [ ] One-sentence subtitle describing the contribution
- [ ] arXiv badge with clickable link
- [ ] Venue badge (conference name)
- [ ] Year badge
- [ ] Optional implementation badge

### Navigation
- [ ] Sticky nav bar with links to all sections
- [ ] Nav links match the actual section IDs in the page
- [ ] Nav uses the `.nav-sticky` class

### Content Quality
- [ ] Overview section has Problem, Contributions, and Evaluation Summary cards
- [ ] Architecture section has at least one colorful diagram
- [ ] Core Mechanisms section has at least 2-3 detailed mechanism write-ups
- [ ] Performance section has specific numbers from the paper (not vague claims)
- [ ] Code blocks have syntax highlighting using `.kw`, `.fn`, `.cm`, `.st`, `.nu`, `.ty` classes

### Diagrams
- [ ] All diagrams are built with HTML/CSS (colored divs, flexbox, grid)
- [ ] No ASCII art anywhere in the page
- [ ] Each diagram has a `.diagram-title`
- [ ] Diagrams use at least 3 distinct colors
- [ ] Architecture diagram uses `.arch-grid` / `.arch-layer` / `.arch-box` pattern

### Repo-Specific (only if repo exists)
- [ ] File tree showing repository structure
- [ ] Key classes table mapping code to paper concepts
- [ ] Code snippets with file/line references
- [ ] Claims vs Implementation comparison table with YES/PARTIAL/NO status indicators
- [ ] Strengths and Limitations side-by-side cards
- [ ] Reproduction steps with copy-pasteable commands
- [ ] Hardware requirements documented

### Paper-Only (if no repo)
- [ ] Expanded architecture section with multiple diagrams
- [ ] Mathematical formulations or pseudocode
- [ ] Deeper evaluation analysis
- [ ] Significance or impact section

### Technical Accuracy
- [ ] All arXiv IDs are correct
- [ ] All venue names and years are correct
- [ ] Performance numbers match the paper
- [ ] Code snippets are accurate (if from repo)
- [ ] Class and method names are spelled correctly

### Polish
- [ ] No broken HTML tags
- [ ] No placeholder text remaining (no `[PLACEHOLDER]` strings)
- [ ] Footer has paper citation
- [ ] Page renders correctly as a standalone HTML file

---

## 8. Example Prompt

Use the following prompt template when asking an LLM to create a paper analysis page. Fill in the placeholders.

### For Papers WITH a Repository

```
Create a paper analysis page for the Agentic AI survey project.

Paper: "[FULL PAPER TITLE]"
arXiv: [ARXIV_ID] (e.g., 2511.02230)
Venue: [VENUE] (e.g., SOSP '23, OSDI '24, or "Preprint")
Year: [YEAR]
Authors: [AUTHOR LIST]

Repository: [ABSOLUTE PATH TO LOCAL REPO CLONE]

Write the output to: [OUTPUT PATH, e.g., papers/continuum/index.html]

Instructions:
1. FIRST explore the repository thoroughly:
   - Read the README for setup and architecture overview
   - Examine the directory structure
   - Read the key source files implementing the main algorithm
   - Identify the core classes, data structures, and algorithms

2. THEN read the paper PDF at: [PATH TO PDF] or [ARXIV URL]
   - Extract claims, contributions, evaluation setup, and results
   - Note specific performance numbers

3. Compare the implementation against the paper's claims.
   For each claim, determine: YES (implemented), PARTIAL (simplified), or NO (missing).

4. Write a self-contained HTML page following the template in PAPER_PAGE_TEMPLATE.md.
   Required sections: Hero, Nav, Overview, Architecture, Repo Analysis, Core Mechanisms,
   Performance Results, Claims vs Implementation, How to Reproduce, Footer.

5. Ensure:
   - At least 800 lines (target 1200+)
   - All diagrams are colorful HTML/CSS blocks (NO ASCII art)
   - All code snippets have syntax highlighting
   - The Claims vs Implementation table is thorough and honest
   - Reproduction commands are copy-pasteable
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

Write the output to: [OUTPUT PATH, e.g., papers/dualpath/index.html]

Instructions:
1. Read the paper PDF at: [PATH TO PDF] or [ARXIV URL]
   - Extract every technical detail: architecture, algorithms, mathematical formulations
   - Note all evaluation details: benchmarks, hardware, baselines, metrics
   - Understand the paper's positioning relative to prior work

2. Write a self-contained HTML page following the template in PAPER_PAGE_TEMPLATE.md.
   Required sections: Hero, Nav, Overview, Architecture (expanded with multiple diagrams),
   Core Mechanisms (expanded), Performance Results, Significance/Impact, Footer.

   OMIT these sections: Repo Analysis, Claims vs Code, How to Reproduce.

3. Since there is no repo to analyze, compensate by:
   - Creating more detailed architecture diagrams (2-3 diagrams showing different aspects)
   - Including pseudocode or mathematical formulations from the paper
   - Providing deeper analysis of the evaluation methodology
   - Adding a comparison with related work
   - Discussing limitations and future directions

4. Ensure:
   - At least 800 lines (target 1200+)
   - All diagrams are colorful HTML/CSS blocks (NO ASCII art)
   - Performance numbers are cited directly from the paper with exact values
```

### Quick Reference: Badge Types

| Badge Class | Use For | Example |
|---|---|---|
| `badge-arxiv` | arXiv ID (always include) | `arXiv:2309.06180` |
| `badge-venue` | Conference/workshop | `SOSP '23`, `OSDI '24` |
| `badge-year` | Publication year | `2023`, `2025` |
| `badge-impl` | Implementation note | `Built on vLLM`, `Open Source`, `Foundational Paper` |

### Quick Reference: Card Types

| Card Class | Use For | Color |
|---|---|---|
| `.card.primary` | Problem statements, key claims | Red left border |
| `.card.success` | Contributions, strengths | Green left border |
| `.card.warn` | Limitations, caveats | Yellow left border |
| `.card.accent` | Evaluation summaries, context | Purple left border |
| `.card.danger` | Critical issues, failures | Red left border |
| `.card` (no modifier) | General information | Blue left border |

### Quick Reference: Status Indicators

| Class | Display | Use For |
|---|---|---|
| `.check` | Green "YES" | Claim fully implemented |
| `.partial` | Yellow "PARTIAL" | Claim simplified or partially implemented |
| `.cross` | Red "NO" or "SIMPLIFIED" | Claim not implemented or significantly divergent |

### Quick Reference: Syntax Highlighting

| Class | Color | Use For | Example |
|---|---|---|---|
| `.kw` | Purple | Keywords | `def`, `if`, `return`, `class`, `import` |
| `.fn` | Blue | Function/method names | `schedule()`, `allocate()` |
| `.cm` | Gray | Comments | `# This is a comment` |
| `.st` | Green | String literals | `"hello"`, `'world'` |
| `.nu` | Orange | Numbers | `42`, `3.14`, `0.001` |
| `.op` | Cyan | Operators | `==`, `+=`, `->` |
| `.ty` | Yellow | Type names | `self`, `int`, `float`, `List` |
| `.bi` | Pink | Built-in functions | `len()`, `sum()`, `print()` |
