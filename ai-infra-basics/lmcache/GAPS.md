# bottleneck-analysis.html — Known Gaps (2026-04-11)

> 這份文件記錄目前 HTML 裡**已知但未解決**的問題、**hand-wave 的段落**、以及**缺少的量測**。
> 每個 item 標上優先度。作為 follow-up 工作清單，也作為給 reviewer / 未來 session 的誠實聲明。

---

## 當前狀態快照

- **§2 Three-way JPS sweep**：L40S Continuum column 已補完（job 6428519 fill）
- **§9.2.1 Empirical NVTX re-measurement**：已加入，3 findings + data provenance callout
- **Working tree**：`ai-infra-basics/lmcache/bottleneck-analysis.html` 已修改 +144/-13，**尚未 commit**
- **A100 資料**：job 6428521（fill）+ 6430915（nsys-bn）4+ 小時仍在 PD，partition queue 卡住

## 已紮實解決的

1. **核心問題**：LMCache 慢的瓶頸是 `wait_for_save` barrier，不是 PCIe 頻寬
2. **硬體下限**：9 次跨 GPU 跨負載量測，DMA `from_gpu` 穩定在 0.67 ms (Gen5) / 1.35 ms (Gen4)，2.03× 比例精準對應 PCIe 世代
3. **Fixed-cost barrier signature**：負載 10× 擴張時 per-call 成本 9× 擴張，但 overhead 比例保持 ~75% 常數
4. **Throughput plateau**：JPS≥6 時 wait_for_save 總時長停在 73–77 秒不動，被 barrier 本身卡住
5. **§2 L40S Continuum 領先幅度**：乾淨資料，0 errors，領先 LMCache 3.6–5.9× 橫跨所有 JPS

---

## ✅ P0：已於 2026-04-11 晚間解決

### P0a. 那 77% blocking overhead 實際上是什麼？ **[RESOLVED]**
**答案**：`cudaStreamSynchronize` 佔 prefill-step wait_for_save 時間的 **96.6%**。

查了 `/storage/project/r-rs275-0/hlin464/h200_lmc_jps1.sqlite` 的 `CUPTI_ACTIVITY_KIND_RUNTIME` 表（866k 個事件），過濾到 159 個 prefill-step wait_for_save 時間窗內的 events：

| API | Calls | Total | % of prefill-wfs wallclock |
|---|---|---|---|
| cudaStreamSynchronize_v3020 | 3,744 | **17,764 ms** | **96.6%** |
| cudaMemcpyAsync_v3020 (launch) | 2,996 | 24.5 ms | 0.1% |
| cudaLaunchKernel_v7000 | 2,961 | 22.2 ms | 0.1% |
| (GPU MEMCPY activity, reference) | 2,604 | 1,631 ms | 8.9% |

**機制**：每個 prefill step 平均 ~19 次 `cudaMemcpyAsync` launch + **~24 次 `cudaStreamSynchronize`**。每次 sync 付 ~3-4 ms 固定成本（driver wake-up、Python-C FFI、GIL re-acquire）就算背後 DMA 已經結束。23.5 sync × 4.74 ms avg = 111.4 ms predicted per prefill step — 跟實測 115.71 ms/step 誤差 3%。

**硬體無辜**：GPU-side MEMCPY activity 87.38 GB / 1,631 ms = **53.59 GB/s** aggregate，精準對上 §9.2 列的 PCIe Gen5 x16 有效頻寬 54 GB/s。硬體在做它該做的事。

**優化路徑**：把 ~24 次 sync 降到每 step 1 次 → 每 step 省 ~100 ms → jps=1 benchmark 從 18.4s 拿回 ~16s wait_for_save 時間。

**寫進 HTML**：§9.2.1 Finding 4 完整呈現這個資料表 + 機制解釋 + coalesce 優化建議。

---

### P0b. 10.4 ms (新) vs 224 ms (舊) wait_for_save 的數字對不上 **[RESOLVED]**
**答案**：新舊數據完全一致，10.4 ms 是「全部 wait_for_save call 的平均」被 91% 的 decode-only 廉價呼叫稀釋了。

用 NVTX nested containment 判斷（每個 wfs range 是否包含至少一個 `LMCacheEngine.store` nested range），wfs call 乾淨分兩群：

| Bucket | Count | % | Mean | Median | p95 |
|---|---|---|---|---|---|
| Prefill-step (has store) | 159 | 9% | **115.71 ms** | 73.00 ms | 253 ms |
| Decode-only (no store) | 1,610 | 91% | 0.01 ms | 0.00 ms | 0.01 ms |

**真正該引用的數字是 prefill-step mean 115.71 ms**。跟 2026-04-07 資料的「224 ms median」在同一個 order of magnitude，差距是負載差異（2026-04-07 在更高 concurrent block 的 regime 量的）。

**寫進 HTML**：§9.2.1 Finding 2 替換了整個段落和表格 — 從「10.4 ms / 2.39 productive / 8.01 overhead」的誤導性框架，改成 bimodal split + prefill-only 正確數字。舊的 hand-wave 段落（"different max_model_len"）已刪除。

---

## 🟡 P1：次要但應該回答的問題

### P1a. H100 飽和時比 H200 慢 ~33% 沒有根因
- jps=6: H100 125.2 ms vs H200 93.8 ms (+33%)
- jps=10: H100 137.3 ms vs H200 108.0 ms (+27%)
- jps=1 時兩者幾乎一樣（9.38 vs 10.40 ms）

HTML §9.2.1 備註但沒深入。可能原因：
- HBM 頻寬差（H100 3.35 TB/s vs H200 4.8 TB/s），scheduler drain queue 速度
- `LMCACHE_MAX_LOCAL_CPU_SIZE` 不同（sbatch 按 GPU 類別設定）
- Node DRAM / CPU 不同（PACE 不同 chassis）

**可做**：查兩邊 sqlite 的 store + from_gpu 裡面的 kernel / memcpy activity，看是 HBM-related 還是 CPU-related。

---

### P1b. Continuum 在 L40S 上贏得比 H200 更多 沒有量化佐證
§2 寫「small HBM = 更多 eviction churn = LMCache 被懲罰更重」，但這是合理 narrative 不是實測。

**可做**：從 `lmcache.server.log` 撈 LMCache 的 cache hit/miss 率。各 GPU 的 log 都在 `20260411_*` 目錄或 `20260407_controlled-sweep/*/L40S/lmcache.server.log` 之類。

---

### P1c. 2.39 ms「productive」拆分假設沒被 nested-ness 驗證
§9.2.1 Finding 2 假設 from_gpu + store 都**發生在** wait_for_save 的時間窗內。但：
- `store` 可能是 save_kv_layer 路徑進來的，不一定 nested
- 需要用 NVTX start_ns/end_ns 做 overlap check

**可做**：一段 Python，對每個 store range 檢查它是否 `start >= wfs.start AND end <= wfs.end` 的 wfs range 之一。

---

## 🟢 P2：資料缺口，低影響

### P2a. A100 沒資料
- 6430915 A100 nsys-bn：PD 4+ 小時
- 6428521 A100 fill：PD 4+ 小時
- Gen4 DMA baseline 已經由 L40S 覆蓋了（1.35 ms 穩定）
- A100 是第 4 個 cross-check，跑完會更完整但不影響結論

### P2b. L40S wait_for_save 被 co-tenant 污染
- 6428519 fill job 跟 6430916 L40S nsys-bn 整個 overlap 在同一個 L40S 節點
- `from_gpu` 乾淨（per-call 不受外部影響），但 wait_for_save 的 91/144/154 ms 被 inflation
- HTML §9.2.1 已經 disclaim 這件事，但如果要乾淨 L40S wfs baseline，必須在獨立節點重跑

### P2c. §9.5 mitigation 估計是 proposal 不是 measurement
「async save pipeline 可以省 150+ ms」這類句子是假設，不是實驗。應該標註為 proposal。不是 bug 只是應該標明。

---

## 剩下的 follow-up 清單

**P0 全部完成** ✅  
**還在 P1/P2**：

1. **P1a — H100 飽和時比 H200 慢 ~33%**：沒做，需要對比兩邊 sqlite 的 kernel/memcpy 分布
2. **P1b — Continuum L40S 領先幅度的 eviction 證據**：沒做，可從 lmcache.server.log 撈 cache hit/miss
3. **P1c — nested-ness 驗證**：現在已經改用 nested containment 判斷（Finding 2/4），P1c 自動解決 ✅
4. **P2a — A100 資料**：job 6430915/6428521 還在 PD
5. **P2b — 乾淨 L40S wait_for_save baseline**：需要在獨立節點重跑
6. **P2c — §9.5 mitigation 標為 proposal**：未改

---

## P0 完成後狀態

- §9.2.1 Finding 2：從「10.4 ms 平均 + 77% 殘差 overhead」改寫成 bimodal split（prefill 115.7 ms / decode 0.01 ms），跟 §9.2 的 224 ms 舊數字完美對上
- §9.2.1 Finding 3：簡化表格，移除 Productive/Overhead 誤導性欄位，保留 load scaling 敘事，加上 footnote 導向 Finding 2
- §9.2.1 Finding 4（新）：`cudaStreamSynchronize` 96.6% 的具體歸因、GPU-side 53.59 GB/s 對上 PCIe Gen5 spec、coalesce 優化建議
- HTML 總計：L40S §2 Continuum column 補完 + §9.2.1 三個 Finding 完整重寫 = 目前最紮實的版本

**Working tree**：`ai-infra-basics/lmcache/bottleneck-analysis.html` 修改量約 +250 行，尚未 commit。  
**相關檔案**：這份 `GAPS.md` 也未 commit。

---

_Last updated: 2026-04-11 ~21:40_
_P0 work completed: 2026-04-11 (resolved P0a cudaStreamSynchronize attribution + P0b prefill-only reconciliation)_
