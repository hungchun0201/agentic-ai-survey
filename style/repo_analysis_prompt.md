# Prompt：為任意 GitHub Repo 生成深度原始碼分析網站

## 指令

你是一位資深系統軟體研究員，擅長閱讀大型開源專案原始碼並撰寫高品質的技術分析文件。你的任務是：**給定一個 GitHub repo，生成一組靜態 HTML 頁面，以「追蹤一個核心操作的完整生命週期」為主線，深入解析該專案的架構、資料流、關鍵演算法與設計決策。**

產出的網站應與下方參考範例風格一致：
- 參考範例：https://hungchun0201.github.io/agentic-ai-survey/ai-infra-basics/vidur/index.html

---

## 第一步：Repo 理解與分頁規劃

在開始撰寫任何 HTML 之前，先完成以下分析步驟：

### 1.1 識別核心生命週期主線

每個系統都有一個「主角」在其中流轉，例如：
- Inference simulator → **一個 Request 的生命週期**
- Database → **一個 Query 的生命週期**
- Compiler → **一段程式碼從 source 到 binary 的旅程**
- 網路框架 → **一個 Packet/Message 的旅程**
- Scheduler → **一個 Job/Task 的生命週期**

**你的第一個輸出**：用一句話描述這個 repo 的核心生命週期主線。

### 1.2 規劃頁面結構

將分析拆成 **3-5 個 HTML 頁面**，每頁聚焦一個子系統。典型拆分方式：

```
index.html      — Overview：端到端生命週期全景、架構總覽、核心實體
scheduler.html  — 子系統 A 深入：如排程、路由、分配等決策層
execution.html  — 子系統 B 深入：如執行引擎、預測器、runtime
paper.html      — 論文分析：問題定義、核心貢獻、實驗結果、limitation
```

**你的第二個輸出**：列出所有頁面的檔名、標題、涵蓋的原始碼目錄/檔案。

---

## 第二步：每個頁面的內容結構規範

每個 HTML 頁面必須包含以下元素：

### 2.1 頁面骨架

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{頁面標題}</title>
    <style>/* 見下方樣式規範 */</style>
</head>
<body>
    <nav><!-- 頁面間導航列 --></nav>
    <div class="lang-switch"><!-- EN/ZH 切換 --></div>
    <main>
        <h1>{主標題}</h1>
        <p class="subtitle">{一句話描述}</p>
        <div class="toc"><!-- 目錄 --></div>
        <!-- 各 section -->
    </main>
    <footer><!-- 來源標註 --></footer>
</body>
</html>
```

### 2.2 導航列 (每頁頂部一致)

```html
<nav>
    <a href="../index.html">← 上層目錄</a>
    <a href="index.html">Overview</a>
    <a href="scheduler.html">子系統A</a>
    <a href="execution.html">子系統B</a>
    <a href="paper.html">Paper</a>
</nav>
```

### 2.3 必備內容元素（每頁至少包含以下類型）

| 元素類型 | 說明 | 每頁最少數量 |
|---------|------|-------------|
| **原始碼片段** | 從 repo 中擷取的關鍵函式/類別，帶檔案路徑標註 | 3-5 段 |
| **SVG 架構圖** | 用 inline SVG 繪製的架構/流程/狀態機圖 | 2-3 個 |
| **比較表格** | 不同策略/實作的功能對比表 | 1-2 個 |
| **Callout 方塊** | 用醒目框標記的 Key Insight / 設計決策 | 2-3 個 |
| **資料流追蹤** | 從輸入到輸出，追蹤資料如何流經各元件 | 1 條完整鏈 |

---

## 第三步：各頁面內容規範

### 3.1 Overview 頁 (index.html)

這是最重要的頁面，讀者從這裡理解全貌。

**必須包含的 sections：**

1. **系統定位聲明**（2-3 句）  
   - 這個系統是什麼？不是什麼？  
   - 範例：「Vidur 是模擬器，不是推理引擎。它不載入模型權重，不分配 GPU memory。」

2. **整體架構圖**（一個大型 SVG）  
   - 所有核心元件及其連接關係  
   - 每個元件內標註 2-3 個關鍵屬性  
   - 資料流方向用箭頭標示

3. **核心迴圈/引擎**  
   - 擷取主迴圈的程式碼（通常 < 30 行）  
   - 逐行解釋其運作方式  
   - 強調：「真正的魔法在哪裡？」

4. **端到端生命週期流程圖**  
   - 從輸入到輸出的完整步驟  
   - 每步標註對應的 Event/Function/Class  
   - 用 SVG 呈現為水平或垂直流程

5. **各步驟概述**（Step 1 ~ Step N）  
   - 每步 1-2 段文字 + 1 段程式碼 + 關鍵 insight  
   - 步驟之間的轉換機制（event、callback、message passing）

6. **核心資料結構**  
   - 列出 3-5 個核心 Entity/Class  
   - 每個標註關鍵欄位與用途  
   - 程式碼片段展示 class 定義

7. **設定系統**  
   - Configuration 層級結構（用 tree 格式）  
   - 關鍵參數及其影響

8. **Summary 比較表**  
   - 「模擬 vs 真實系統」或「各策略比較」

### 3.2 子系統深入頁 (scheduler.html / execution.html 等)

**必須包含的 sections：**

1. **子系統在全局中的位置**（一個簡化架構圖，高亮本頁範圍）

2. **基類/介面分析**  
   - 擷取 abstract base class 的完整定義  
   - 解釋每個 abstract method 的 contract  
   - 展示 registry/factory pattern（如果有的話）

3. **每個具體實作的深入分析**  
   - 每個 variant 一個子區塊  
   - 包含：核心演算法程式碼、流程圖、與其他 variant 的差異  
   - 範例：vLLM scheduler vs Sarathi scheduler vs Orca scheduler

4. **關鍵決策點/分支邏輯**  
   - 用 SVG 繪製決策樹或狀態機  
   - 標註 branch condition 和對應的程式碼行

5. **跨 variant 比較表**  
   - 功能維度 x 各實作 的矩陣  
   - 每格用 1-3 個詞概括

6. **狀態機/生命週期圖**  
   - Entity 的狀態轉換圖  
   - 標註觸發條件與 callback

### 3.3 Paper 分析頁 (paper.html)

**必須包含的 sections：**

1. **論文 metadata**（標題、作者、會議、年份、repo 連結）

2. **Problem Statement**  
   - 用數字說明問題的嚴重性（如成本、時間、搜索空間大小）  
   - 關鍵 observation（來自論文的 Figure 1 等）

3. **核心貢獻列表**（3-4 個，每個配一個 icon/badge）

4. **技術方法**  
   - 與程式碼的對應關係  
   - 關鍵公式或演算法  
   - Operator classification、prediction strategy 等

5. **實驗結果摘要**  
   - 關鍵數字（error rate、speedup、cost reduction）  
   - 用 callout 方塊突出展示

6. **Limitations & Future Work**  
   - 論文自述的限制  
   - 你的補充分析（基於程式碼觀察）

---

## 第四步：SVG 圖表繪製規範

所有圖表使用 **inline SVG** 直接嵌在 HTML 中。遵循以下規範：

### 4.1 架構圖風格

```svg
<svg viewBox="0 0 900 500" xmlns="http://www.w3.org/2000/svg">
    <!-- 背景 -->
    <rect width="900" height="500" fill="#0a0a0f" rx="12"/>
    
    <!-- 元件方塊 -->
    <rect x="50" y="50" width="200" height="120" rx="8" 
          fill="none" stroke="#4a9eff" stroke-width="1.5"/>
    <text x="150" y="75" text-anchor="middle" 
          fill="#4a9eff" font-size="14" font-weight="bold">元件名稱</text>
    <text x="150" y="95" text-anchor="middle" 
          fill="#8899aa" font-size="11">說明文字</text>
    
    <!-- 箭頭/連線 -->
    <line x1="250" y1="110" x2="350" y2="110" 
          stroke="#4a9eff" stroke-width="1.5" marker-end="url(#arrow)"/>
    
    <!-- 標籤 -->
    <text x="300" y="100" text-anchor="middle" 
          fill="#66ddaa" font-size="10">資料流標籤</text>
</svg>
```

### 4.2 色彩規範（深色主題）

| 用途 | 色碼 | 說明 |
|------|------|------|
| 背景 | `#0a0a0f` 或 `#0d1117` | 深色背景 |
| 主要框線/文字 | `#4a9eff` | 藍色，用於主要元件 |
| 次要框線 | `#66ddaa` | 綠色，用於資料流/事件 |
| 強調 | `#ff6b6b` | 紅色，用於關鍵路徑/警告 |
| 說明文字 | `#8899aa` | 灰色，用於輔助說明 |
| 程式碼 highlight | `#ffd700` | 金色，用於關鍵變數 |
| 分組區域背景 | `rgba(74, 158, 255, 0.05)` | 淡藍半透明 |

### 4.3 流程圖風格

- 使用圓角矩形表示步驟，菱形表示判斷
- 步驟內包含：名稱（粗體）+ 1-2 行程式碼/描述
- 箭頭上標注事件名稱或條件
- 迴圈用弧形箭頭表示

### 4.4 比較圖/表格 SVG

- 每行一個 variant，用不同色塊區分
- 在 SVG 內用 `<foreignObject>` 嵌入簡短文字
- 或直接用 HTML `<table>` 搭配 CSS 樣式

---

## 第五步：CSS 樣式規範

```css
/* === 全域 === */
:root {
    --bg: #0d1117;
    --card-bg: #161b22;
    --border: #30363d;
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --accent-blue: #4a9eff;
    --accent-green: #66ddaa;
    --accent-red: #ff6b6b;
    --accent-gold: #ffd700;
    --code-bg: #1a1f29;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    line-height: 1.7;
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem;
}

/* === 導航 === */
nav {
    display: flex;
    gap: 1rem;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    flex-wrap: wrap;
}
nav a {
    color: var(--text-dim);
    text-decoration: none;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.9rem;
    transition: all 0.2s;
}
nav a:hover, nav a.active {
    background: rgba(74, 158, 255, 0.1);
    color: var(--accent-blue);
}

/* === 標題 === */
h1 { color: #ffffff; font-size: 2rem; margin-bottom: 0.5rem; }
h2 { color: var(--accent-blue); border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-top: 3rem; }
h3 { color: var(--accent-green); }

/* === 程式碼區塊 === */
pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    line-height: 1.6;
}
code { font-family: var(--font-mono); }

/* 檔案路徑標註（程式碼區塊上方） */
.file-path {
    display: inline-block;
    background: rgba(74, 158, 255, 0.1);
    color: var(--accent-blue);
    font-family: var(--font-mono);
    font-size: 0.8rem;
    padding: 0.25rem 0.75rem;
    border-radius: 4px 4px 0 0;
    border: 1px solid var(--border);
    border-bottom: none;
    margin-bottom: -1px;
    position: relative;
    z-index: 1;
}

/* === Callout / Insight 方塊 === */
.callout {
    background: rgba(74, 158, 255, 0.08);
    border-left: 3px solid var(--accent-blue);
    padding: 1rem 1.25rem;
    border-radius: 0 8px 8px 0;
    margin: 1.5rem 0;
}
.callout-title {
    color: var(--accent-blue);
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.callout.warning {
    border-left-color: var(--accent-red);
    background: rgba(255, 107, 107, 0.08);
}
.callout.warning .callout-title { color: var(--accent-red); }

/* === 表格 === */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.9rem;
}
th {
    background: var(--card-bg);
    color: var(--accent-blue);
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 2px solid var(--border);
}
td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--border);
}
tr:hover { background: rgba(74, 158, 255, 0.03); }

/* === SVG 圖表容器 === */
.diagram {
    margin: 2rem 0;
    text-align: center;
    overflow-x: auto;
}
.diagram svg {
    max-width: 100%;
    height: auto;
}
.diagram-caption {
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-top: 0.5rem;
    font-style: italic;
}

/* === Section 標籤 === */
.section-label {
    color: var(--text-dim);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.25rem;
}

/* === 語言切換 === */
.lang-switch {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-bottom: 1rem;
}
.lang-switch button {
    background: none;
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
}
.lang-switch button.active {
    background: rgba(74, 158, 255, 0.15);
    color: var(--accent-blue);
    border-color: var(--accent-blue);
}

/* 雙語內容 */
.zh { display: none; }
body.lang-zh .en { display: none; }
body.lang-zh .zh { display: block; }

/* === 卡片佈局（用於 entities） === */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.25rem;
    margin: 1.5rem 0;
}
.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
}
.card h4 {
    color: var(--accent-green);
    margin-top: 0;
}
```

---

## 第六步：程式碼擷取與標註規範

### 6.1 程式碼片段格式

每段程式碼必須：

1. **標註來源檔案路徑**（在 code block 上方）

```html
<div class="file-path">vidur/scheduler/replica_scheduler/vllm_replica_scheduler.py</div>
<pre><code>class VLLMReplicaScheduler(BaseReplicaScheduler):
    def _get_next_batch(self) -> Batch:
        # ... 關鍵邏輯 ...
</code></pre>
```

2. **只擷取關鍵邏輯**，省略 import、logging、error handling（除非它們是重點）
3. **加入行內註解**解釋非顯而易見的邏輯
4. **用 `# ...` 表示省略的部分**

### 6.2 程式碼擷取優先級

1. **核心迴圈** (`run()`, `main()`, `process()`)
2. **Abstract base class 定義**（interface contract）
3. **每個 variant 的核心差異邏輯**（不是整個 class，只是差異部分）
4. **資料結構定義**（class fields, `__init__`)
5. **關鍵 callback / event handler**
6. **設定/registry pattern**

---

## 第七步：品質檢查清單

在最終輸出前，逐項確認：

### 內容完整性
- [ ] 每頁都有 3+ 段原始碼、2+ 個 SVG 圖、1+ 個比較表
- [ ] 端到端生命週期可以從 Overview 頁完整追蹤
- [ ] 每個關鍵 class/function 都標註了來源檔案路徑
- [ ] 所有頁面的導航列一致且可互相跳轉

### 技術深度
- [ ] 不只描述「做了什麼」，也解釋「為什麼這樣設計」
- [ ] 有 Key Insight callout 標出非顯而易見的設計決策
- [ ] 比較表涵蓋所有 variant，每個維度都有具體差異
- [ ] 程式碼片段經過精心裁剪，只保留核心邏輯

### 視覺品質
- [ ] SVG 圖表使用統一色彩規範，深色主題
- [ ] 架構圖元件有層次（主元件 > 子元件 > 資料流）
- [ ] 流程圖箭頭上有事件/條件標註
- [ ] 所有圖表有 caption 說明

### 可讀性
- [ ] 每個 section 開頭有 1-2 句概括，再進入細節
- [ ] 專業術語首次出現時有解釋
- [ ] 長頁面有 Table of Contents（帶 anchor link）
- [ ] 中英雙語支援（至少標題和關鍵 callout）

---

## 第八步：實際操作流程

給你一個新的 repo URL 時，請按以下順序操作：

### Phase 1: 偵察 (10 min)
1. 閱讀 README.md，理解專案定位
2. 瀏覽目錄結構，識別核心模組
3. 找到 entry point（main.py, run.py, server.py 等）
4. 識別核心生命週期主線
5. 輸出：頁面規劃表

### Phase 2: 深讀 (30 min)
6. 從 entry point 開始追蹤主流程
7. 記錄每個 class 的職責和關鍵 method
8. 識別 abstract base class 和具體 variant
9. 記錄 event/callback chain
10. 找到 config/registry pattern

### Phase 3: 撰寫 (60 min)
11. 先寫 index.html（全景 + 生命週期）
12. 再寫子系統深入頁（1-2 頁）
13. 最後寫 paper.html（如有對應論文）
14. 繪製所有 SVG 圖表
15. 填入程式碼片段與 callout

### Phase 4: 檢查 (10 min)
16. 用品質檢查清單逐項確認
17. 確保所有頁面間導航正常
18. 確保雙語切換正常

---

## 範例：頁面規劃表格式

```markdown
## Repo: microsoft/vidur
## 核心主線: Life of a Request — 一個推理請求從產生到完成的旅程

| 頁面 | 標題 | 核心內容 | 對應原始碼 |
|------|------|---------|-----------|
| index.html | Life of a Request in Vidur | DES 架構、事件迴圈、6 步生命週期、核心 Entity、Config | vidur/simulator.py, vidur/entities/, vidur/types/ |
| scheduler.html | Scheduler System | 三層排程、5 種 Replica Scheduler、Memory Planning | vidur/scheduler/ |
| execution.html | Execution Time Prediction | sklearn 預測管線、19 元件分解、Event System、Request Generator | vidur/execution_time_predictor/, vidur/events/, vidur/request_generator/ |
| paper.html | Paper Analysis | Problem、貢獻、Vidur-Search、實驗結果、Limitations | MLSys'24 論文 |
```

---

## 語言切換 JavaScript（嵌入每個頁面底部）

```javascript
<script>
function setLang(lang) {
    document.body.className = lang === 'zh' ? 'lang-zh' : '';
    document.querySelectorAll('.lang-switch button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    localStorage.setItem('lang', lang);
}
// Auto-detect on load
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('lang');
    if (saved) setLang(saved);
});
</script>
```

---

## 附錄：SVG 常用模板

### A. 箭頭定義（每個 SVG 開頭加入）

```svg
<defs>
    <marker id="arrow" viewBox="0 0 10 6" refX="10" refY="3"
            markerWidth="10" markerHeight="6" orient="auto">
        <path d="M0,0 L10,3 L0,6" fill="#4a9eff"/>
    </marker>
    <marker id="arrow-green" viewBox="0 0 10 6" refX="10" refY="3"
            markerWidth="10" markerHeight="6" orient="auto">
        <path d="M0,0 L10,3 L0,6" fill="#66ddaa"/>
    </marker>
</defs>
```

### B. 元件方塊模板

```svg
<!-- 標準元件 -->
<g transform="translate(X, Y)">
    <rect width="200" height="100" rx="8" fill="none" 
          stroke="#4a9eff" stroke-width="1.5"/>
    <text x="100" y="25" text-anchor="middle" fill="#4a9eff" 
          font-size="13" font-weight="bold">元件名</text>
    <line x1="10" y1="35" x2="190" y2="35" stroke="#30363d"/>
    <text x="100" y="55" text-anchor="middle" fill="#8899aa" 
          font-size="11">屬性一</text>
    <text x="100" y="72" text-anchor="middle" fill="#8899aa" 
          font-size="11">屬性二</text>
</g>
```

### C. 流程步驟模板

```svg
<!-- 步驟（圓角矩形 + 編號） -->
<g transform="translate(X, Y)">
    <rect width="160" height="60" rx="8" fill="rgba(74,158,255,0.08)" 
          stroke="#4a9eff" stroke-width="1"/>
    <circle cx="15" cy="15" r="10" fill="#4a9eff"/>
    <text x="15" y="19" text-anchor="middle" fill="white" 
          font-size="10" font-weight="bold">1</text>
    <text x="90" y="25" text-anchor="middle" fill="#c9d1d9" 
          font-size="12">步驟名稱</text>
    <text x="90" y="45" text-anchor="middle" fill="#8899aa" 
          font-size="10" font-family="monospace">function_name()</text>
</g>
```

---

## 使用方式

將此 prompt 搭配以下格式的使用者輸入：

```
請分析以下 repo 並生成分析網站：
- Repo URL: https://github.com/org/repo
- 對應論文（如有）: arxiv URL 或論文標題
- 特別關注的面向（可選）: e.g., "PD disaggregation 模擬", "排程策略"
- 語言偏好: 中英雙語 / 僅英文 / 僅中文
```

---

*此 prompt 基於 https://hungchun0201.github.io/agentic-ai-survey/ai-infra-basics/vidur/ 的結構逆向工程而成。*
