# SimAI Inference 分析專用補丁

> **用途**：將此文件附加在 `repo_analysis_prompt.md` 之後，覆蓋/補充原始 prompt 中不適用於 SimAI 的部分。
> 原始 prompt 針對「單一 codebase、單一生命週期」設計，SimAI 是多元件全棧系統，需要以下四項關鍵修改。

---

## 修改 1：生命週期主線 — 從「單 repo 內」改為「跨元件」

### 問題
原始 prompt 假設一個 request 在同一個 codebase 內流轉（如 Vidur 的 `Request → Event Queue → Scheduler → Predictor → Metrics`）。但 SimAI inference 的一個 request 橫跨 **5 個獨立元件**，每個元件有自己的 repo、語言（Python + C++）、抽象層級。

### 修改
將核心主線定義為：

**「Life of an Inference Request Across SimAI's Full Stack」**
— 一個推理請求如何從 vidur-alibabacloud 的 scheduling 層，經過 AICB 的 workload 描述生成與計算 profiling，透過 SimCCL 的 collective communication 分解，最終在 astra-sim + NS-3 的網路模擬中完成端到端模擬。

### 跨元件資料流（覆蓋原 prompt 的「端到端生命週期流程圖」）

繪製 SVG 時，必須明確標示 **元件邊界**（用虛線框 + 不同底色區分），資料流箭頭跨越邊界時標註 **傳遞的資料格式**（workload file、CSV profiling data、communication pattern）。

```
┌─────────────────────────────────────────────────────────────┐
│                    vidur-alibabacloud                         │
│  Request Generator → Global Scheduler → Replica Scheduler    │
│  → Batch 構建 → Execution Time 查詢                          │
│                          │                                    │
│                          │ (1) 需要計算時間預測                │
│                          ▼                                    │
│  ┌──────────────── AICB (Python + CUDA) ──────────────────┐  │
│  │  AIOB Profiler: 在真實 GPU 上 profiling                  │  │
│  │  → DeepGEMM (FlashMLA/GDN kernels)                      │  │
│  │  → 產生 compute_time per operator                        │  │
│  │  → 輸出 workload description file                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│                          │ (2) workload file (txt/csv)        │
│                          ▼                                    │
│  ┌──────────── SimCCL (C++) ────────────────────────────┐    │
│  │  將 collective ops (AllReduce, AllGather, ReduceScatter)  │
│  │  分解為 point-to-point 通訊操作集合                       │
│  │  按 NCCL Ring/Tree/NVLS 算法                             │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│                          │ (3) p2p communication pattern      │
│                          ▼                                    │
│  ┌──── astra-sim-alibabacloud (C++) ──────────────────────┐  │
│  │  Analytical mode: busbw 估算通訊時間                      │
│  │  Simulation mode: 呼叫 NS-3 精確模擬                     │
│  │  ┌──── ns-3-alibabacloud (C++) ────────────────────┐    │
│  │  │  Packet-level 網路模擬                            │    │
│  │  │  擁塞控制、adaptive routing、拓撲建模              │    │
│  │  │  → KV cache 傳輸延遲建模                          │    │
│  │  └────────────────────────────────────────────────┘    │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│                          │ (4) communication time             │
│                          ▼                                    │
│  vidur-alibabacloud: 合併 compute_time + comm_time            │
│  → BatchStageEndEvent at (now + total_time)                   │
│  → Metrics: TTFT, TBT, E2E latency                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 修改 2：頁面結構 — 從「子系統深入」改為「Delta 分析 + 跨元件整合」

### 問題
原始 prompt 的分頁假設你在分析一個從零開始的系統。但 SimAI 的 inference 部分是 **在 Vidur 之上的擴展**，讀者很可能已經讀過 Vidur 的分析。重複解釋 Vidur 的 event loop、replica scheduler 既浪費篇幅又缺乏新意。

### 修改後的頁面規劃

```markdown
## Repo: aliyun/SimAI (inference 部分)
## 核心主線: Life of an Inference Request Across SimAI's Full Stack
## 前置知識: 讀者已理解 Vidur 的基本架構（可連結到 Vidur 分析頁）

| 頁面 | 標題 | 核心內容 | 對應原始碼 |
|------|------|---------|-----------|
| index.html | SimAI Inference: Full-Stack Overview | 五元件架構、跨元件資料流、vs Vidur 差異總覽、Scenario 7 端到端 | SimAI/README.md, vidur-alibabacloud/, aicb/ |
| pd-disagg.html | Prefill/Decode Disaggregation Simulation | PD 分離的模擬機制、KV cache 傳輸建模、Prefill/Decode worker 調度、vs co-located 的差異 | vidur-alibabacloud/ (核心新增程式碼) |
| workload.html | Inference Workload Generation & Compute Profiling | AICB inference workload 生成、DeepSeek/Qwen3-MoE 模型建模、AIOB GPU profiling、DeepGEMM/FlashMLA 依賴 | aicb/workload_generator/mocked_model/inference/ |
| network.html | Communication Simulation: SimCCL + astra-sim + NS-3 | Collective op 分解、NCCL 算法模擬、NS-3 網路拓撲、KV cache 跨節點傳輸的網路成本 | SimCCL/, astra-sim-alibabacloud/, ns-3-alibabacloud/ |
| paper.html | Paper & Positioning | NSDI'25 論文核心、vs Vidur/TokenSim/Frontier 定位比較、Limitations | NSDI'25 paper |
```

### 每頁的寫作策略

**index.html** 的 Section 1 必須是「Vidur → SimAI：What Changed and Why」，用一個對照表快速讓讀者理解 delta：

```markdown
| 維度 | 原始 Vidur | SimAI vidur-alibabacloud |
|------|-----------|------------------------|
| 部署架構 | Co-located (prefill+decode 同 replica) | 支援 PD disaggregation |
| 計算時間預測 | sklearn RandomForest on profiled CSV | AICB AIOB 真實 GPU profiling (DeepGEMM/FlashMLA) |
| 通訊模擬 | 無（假設 replica 內通訊忽略不計） | SimCCL + astra-sim + NS-3 全棧網路模擬 |
| 支援模型 | LLaMA2-7B/13B/70B | + DeepSeek, Qwen3-MoE, Qwen3-Next |
| 硬體需求 | 純 CPU 模擬 | Profiling 需 Hopper/Blackwell GPU (SM90+) |
| 多請求 | 支援（DES 模擬） | 支援（繼承 + 擴展） |
```

**pd-disagg.html** 是最關鍵的新增頁面，原始 prompt 完全沒有對應結構。需要覆蓋：
1. PD disaggregation 的概念（簡述，不需太長，可連結外部資源）
2. **SimAI 如何在模擬中實現 PD 分離**（這是核心）
   - Prefill instance 和 Decode instance 的模擬表示
   - KV cache 傳輸的通訊建模（走 SimCCL + astra-sim 路徑）
   - Request 在 prefill 完成後如何「遷移」到 decode instance
   - Backpressure 機制（如果有的話）
3. 與 co-located 模式的效能比較（如果 repo 中有 example/benchmark）

---

## 修改 3：程式碼擷取策略 — 從「單語言深讀」改為「跨語言 + 跨 repo 的接口追蹤」

### 問題
原始 prompt 的程式碼擷取策略假設你在讀一個 Python codebase，重點放在 class hierarchy 和 event handler。但 SimAI 是：
- **vidur-alibabacloud**: Python（Vidur fork，修改的 scheduler + predictor）
- **AICB**: Python + CUDA（workload generation + GPU profiling）
- **SimCCL**: C++（collective communication 分解）
- **astra-sim-alibabacloud**: C++（模擬引擎核心）
- **ns-3-alibabacloud**: C++（網路模擬）

你不可能（也不應該）深讀所有五個 codebase。

### 修改後的擷取策略

**優先級重排為：**

1. **跨元件接口**（最重要！）
   - vidur-alibabacloud 如何呼叫 AICB 的 profiling 結果？（file format? API call?）
   - AICB 輸出的 workload description file 格式是什麼？
   - astra-sim 如何接收 workload 並回傳 communication time？
   - 這些是理解整個系統最關鍵的「膠水」，但往往藏在 shell script 和 config file 中

2. **vidur-alibabacloud 的 diff**（核心新增邏輯）
   - 不要貼 Vidur 原有的程式碼（讀者已知）
   - 只擷取 SimAI 新增/修改的部分
   - 用 `git diff` 或手動標記 `// NEW IN SIMAI` 的方式標示

3. **AICB inference workload 生成**（新增模型的關鍵邏輯）
   - DeepSeek 的 MLA (Multi-head Latent Attention) 如何建模
   - Qwen3-MoE 的 expert routing 如何建模
   - prefill vs decode 的 workload 差異如何表達

4. **SimCCL + astra-sim 的集成點**（而非其內部實作細節）
   - NCCL 算法選擇邏輯
   - NS-3 拓撲生成腳本

5. **C++ 程式碼只在必要時擷取**
   - astra-sim 的 MockNcclGroup 相關邏輯
   - NS-3 的拓撲生成 Python script（gen_Topo_Template.py）

### 程式碼標註格式修改

原始 prompt 的 file-path 標註只有一層。SimAI 需要兩層：

```html
<div class="component-badge">vidur-alibabacloud</div>
<div class="file-path">vidur-alibabacloud/vidur/scheduler/replica_scheduler/new_scheduler.py</div>
<pre><code>...</code></pre>
```

新增 CSS：
```css
.component-badge {
    display: inline-block;
    background: rgba(102, 221, 170, 0.15);
    color: var(--accent-green);
    font-size: 0.7rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    margin-bottom: 0.25rem;
}
/* 不同元件用不同色系 */
.component-badge.aicb { background: rgba(255, 215, 0, 0.12); color: #ffd700; }
.component-badge.simccl { background: rgba(255, 107, 107, 0.12); color: #ff6b6b; }
.component-badge.astrasim { background: rgba(180, 130, 255, 0.12); color: #b482ff; }
.component-badge.ns3 { background: rgba(255, 165, 0, 0.12); color: #ffa500; }
```

---

## 修改 4：SVG 架構圖 — 新增「元件邊界」和「接口層」視覺語言

### 問題
原始 prompt 的 SVG 規範是平面的——所有方塊在同一個邏輯層級。SimAI 需要表達 **嵌套元件** 和 **跨元件資料傳遞**。

### 新增 SVG 視覺語言

#### 元件邊界（虛線大框）
```svg
<!-- 元件邊界 -->
<rect x="20" y="20" width="400" height="300" rx="12"
      fill="rgba(74, 158, 255, 0.03)"
      stroke="#4a9eff" stroke-width="1" stroke-dasharray="8,4"/>
<text x="40" y="45" fill="#4a9eff" font-size="12"
      font-weight="bold" opacity="0.7">vidur-alibabacloud</text>
```

#### 跨元件箭頭（粗、帶標籤）
```svg
<!-- 跨元件資料傳遞 -->
<line x1="420" y1="170" x2="480" y2="170"
      stroke="#ffd700" stroke-width="2.5"
      stroke-dasharray="6,3" marker-end="url(#arrow-gold)"/>
<rect x="425" y="155" width="50" height="16" rx="3"
      fill="rgba(255, 215, 0, 0.15)"/>
<text x="450" y="166" text-anchor="middle"
      fill="#ffd700" font-size="9" font-weight="bold">workload.txt</text>
```

#### 語言標記（元件框角落）
```svg
<!-- 語言標記 -->
<rect x="380" y="22" width="35" height="16" rx="3" fill="rgba(255,255,255,0.08)"/>
<text x="397" y="34" text-anchor="middle" fill="#8899aa" font-size="9">C++</text>
```

#### 五元件色彩分配
| 元件 | 邊框色 | 背景色 | 用途 |
|------|--------|--------|------|
| vidur-alibabacloud | `#4a9eff` (藍) | `rgba(74,158,255,0.03)` | Scheduling + orchestration |
| AICB | `#ffd700` (金) | `rgba(255,215,0,0.03)` | Workload generation + profiling |
| SimCCL | `#ff6b6b` (紅) | `rgba(255,107,107,0.03)` | Collective comm decomposition |
| astra-sim | `#b482ff` (紫) | `rgba(180,130,255,0.03)` | Simulation engine |
| ns-3 | `#ffa500` (橙) | `rgba(255,165,0,0.03)` | Network simulation |

---

## 新增 Section：SimAI-specific 的必備分析點

以下是原始 prompt 的品質檢查清單中 **沒有但 SimAI 必須覆蓋** 的分析點：

### Inference-specific 檢查項
- [ ] Prefill 和 Decode 階段在模擬中如何被區分（不同 instance? 不同 event type? 不同 scheduler path?）
- [ ] KV cache 大小如何計算，傳輸成本如何進入 execution time
- [ ] DeepSeek MLA 的 attention 建模與標準 MHA/GQA 的差異
- [ ] Qwen3-MoE 的 expert parallel 如何影響 communication pattern
- [ ] AIOB profiling 的流程：需要什麼硬體、profiling 什麼 kernel、輸出什麼格式

### Cross-component 檢查項
- [ ] 明確標出每個「跨元件接口」的資料格式和呼叫方式
- [ ] Analytical mode vs Simulation mode 的差異在每個元件中如何體現
- [ ] 有沒有 end-to-end example script 可以追蹤（通常在 `scripts/` 或 `example/` 目錄）
- [ ] Dockerfile 的建構流程（因為 SM90+ 依賴，這很重要）

### Delta-vs-Vidur 檢查項
- [ ] 明確列出 vidur-alibabacloud 相對於原始 Vidur 新增了哪些檔案
- [ ] 修改了哪些已有檔案（scheduler? predictor? config?）
- [ ] 新增了哪些 Event Type（如果有的話）
- [ ] Execution time predictor 是用 AICB 的 profiling 替代了 sklearn 嗎？還是並存？

---

## 新增 Section：操作流程修改

### Phase 1 偵察（修改版）

SimAI 是 git submodule 結構，偵察需要特殊處理：

```bash
# 1. Clone 主 repo
git clone https://github.com/aliyun/SimAI.git
cd SimAI
git submodule update --init --recursive

# 2. 確認 inference 相關目錄
ls vidur-alibabacloud/        # Vidur fork，inference scheduling
ls aicb/                       # Workload generation（注意 inference/ 子目錄）

# 3. 找到 Scenario 7 的 entry point
cat vidur-alibabacloud/README.md
cat example/                   # 看有沒有 inference example

# 4. 比對 vidur-alibabacloud vs 原始 Vidur
# 這一步非常關鍵：找出 delta
git clone https://github.com/microsoft/vidur.git /tmp/vidur-original
diff -rq vidur-alibabacloud/vidur/ /tmp/vidur-original/vidur/ | head -50

# 5. 找到 AICB 的 inference workload 生成入口
ls aicb/workload_generator/mocked_model/inference/
cat aicb/aicb_configs/  # inference 相關 config

# 6. 找到跨元件接口
grep -r "workload" scripts/ | head -20    # 看 workload file 如何傳遞
grep -r "busbw" vidur-alibabacloud/       # 看 analytical mode 的接口
```

### Phase 2 深讀（修改版，時間分配）

| 元件 | 時間佔比 | 重點 |
|------|---------|------|
| vidur-alibabacloud | 40% | Delta vs Vidur、PD disagg 邏輯、新增 scheduler/predictor |
| AICB inference | 25% | DeepSeek/Qwen3 模型定義、AIOB profiling 流程、workload file 格式 |
| 跨元件接口 | 20% | shell scripts、config files、file format specs |
| SimCCL + astra-sim + NS-3 | 15% | 只看接口層，不深入內部實作（除非 PD disagg 有特殊通訊模式） |

---

## 新增 Section：pd-disagg.html 的詳細結構規範

這是 SimAI 分析中 **最重要的新增頁面**，原始 prompt 沒有對應範本。

### 必備 Sections

```
1. What is PD Disaggregation?（簡述，2-3 段 + 1 個簡單 SVG）
   - Co-located 的問題：prefill 搶占 decode 資源
   - Disaggregation 的解法：分開到不同 GPU instance
   - 關鍵取捨：增加 KV cache 傳輸成本，換取更好的 TTFT/TBT 控制

2. How SimAI Models PD Disaggregation（核心，最長 section）
   - Prefill Instance 和 Decode Instance 在模擬中的表示方式
   - Request 的生命週期變化：
     * Co-located: Request → Batch(prefill) → Batch(decode) → Done（同一 replica）
     * Disaggregated: Request → Prefill Worker → [KV Transfer] → Decode Worker → Done
   - KV cache 傳輸如何被建模：
     * 傳輸量計算：2 * 2 * num_layers * head_dim * kv_heads * seq_len bytes
     * 傳輸時間：走 astra-sim analytical (busbw) 或 simulation (NS-3) 路徑
   - Event chain 的變化（如果新增了 event type）
   - **SVG 圖**：Co-located vs Disaggregated 的 event chain 對比

3. Scheduling in a Disaggregated System
   - Global scheduler 如何區分 prefill/decode replica？
   - Request routing: prefill-first → transfer → decode-first？
   - P:D ratio（prefill worker 數 : decode worker 數）如何配置

4. Network Cost of KV Cache Transfer
   - 不同模型的 KV cache size 比較（LLaMA vs DeepSeek MLA vs Qwen3-MoE）
   - 網路頻寬需求估算
   - Analytical mode vs NS-3 Simulation mode 的精度差異

5. Co-located vs Disaggregated: Simulation Comparison（如果 repo 有 example）
   - 同一 workload 下兩種模式的 TTFT、TBT 差異
   - P:D ratio 的敏感度分析
```

### pd-disagg.html 的 Key Insight Callout 建議

```html
<div class="callout">
    <div class="callout-title">Key Insight: SimAI 的 PD Disagg 模擬能力來自跨元件整合</div>
    <p>原始 Vidur 無法模擬 PD disaggregation，因為它的 replica 抽象把 prefill 和 decode
    綁定在同一個 scheduler 迴圈中。SimAI 透過 vidur-alibabacloud 擴展 scheduling 層，
    並將 KV cache 傳輸的通訊成本導入 astra-sim/NS-3，才實現了這一能力。
    這不是 Vidur 的小修改，而是架構層級的擴展。</p>
</div>

<div class="callout warning">
    <div class="callout-title">硬體限制：Profiling 需要 SM90+ GPU</div>
    <p>SimAI 1.5 的 inference 模擬依賴 AICB 的 AIOB profiler，而 AIOB 使用
    DeepGEMM 和 FlashMLA 等僅支援 Hopper/Blackwell 架構的庫。
    這意味著你不能在 A100 (SM80) 上完成 profiling 階段，
    但 profiling 完成後的模擬可以在任何 CPU 上執行。</p>
</div>
```

---

## Summary：四項修改的核心邏輯

| # | 原始假設 | SimAI 現實 | 修改方向 |
|---|---------|-----------|---------|
| 1 | 單 repo、單一生命週期 | 5 元件、跨 repo 資料流 | 主線改為跨元件追蹤，SVG 需標示元件邊界 |
| 2 | 從零解釋一個系統 | 基於 Vidur 的擴展 | 改為 Delta 分析，新增 PD disagg 專頁 |
| 3 | 單語言(Python) 深讀 | Python + C++ + CUDA，跨 repo | 改為「接口優先」策略，C++ 只看接口 |
| 4 | 平面 SVG 元件圖 | 嵌套元件 + 跨元件箭頭 | 新增元件邊界虛線框、語言標記、五色分配 |

---

## 使用方式

將此文件與 `repo_analysis_prompt.md` 一起提供給 LLM，輸入格式：

```
請分析以下 repo 並生成分析網站：
- 基礎 Prompt: [附上 repo_analysis_prompt.md]
- 專案補丁: [附上此文件]
- Repo URL: https://github.com/aliyun/SimAI
- 聚焦範圍: inference 部分（SimAI 1.5 新增功能）
- 對應論文: NSDI'25 SimAI paper (https://ennanzhai.github.io/pub/nsdi25spring-simai.pdf)
- 前置知識連結: Vidur 分析 → https://hungchun0201.github.io/agentic-ai-survey/ai-infra-basics/vidur/
- 特別關注: PD disaggregation 模擬機制、DeepSeek/Qwen3-MoE 模型建模、跨元件資料流
- 語言: 中英雙語
```
