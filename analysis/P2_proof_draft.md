# P2 證明草稿 v0.1 — One-bit 合約的 IC 與 Pareto 支配
(2026-07-06; 對照 PROPOSAL.md §4)

## 模型

**參與者**：provider（單一）、clients i = 1..n（session 擁有者）。
**Session 結構**（沿用 mainline reference class）：session i 有回合 t=0..T_i，回合 t 重讀
前綴 L_i(t)（單調成長），回合間空窗 g_i(t)；T_i 與 g_i 為 client 私有資訊（provider 不可觀測
——這是資訊結構的核心假設，由黑箱量測佐證：provider 只看得到請求到達）。
**技術參數**：provider 每 token-小時持有成本 c_s > 0；每請求服務成本 c_q > 0（與 token 數
無關的固定分量即可）；重算（prefill）成本 c_p per token，且 c_p ≫ c_s·(典型 gap)（由
量測支撐：重讀稅 11.3×）。
**Client 價值**：回合 t+1 若前綴 resident，client 省 v·L_i(t)（v = 重算價與快取讀價之差的
上界；以計價常數表出 v = (1 − 0.1)·P = 0.9P）。

## 現行合約族 M(w, r, τ)

寫入付 w·P·(新 tokens)，快取讀付 r·P·L，TTL τ，命中免費刷新。Client 策略空間：每個空窗
選 {ping^k 然後放棄, 直接放棄, 預先買更長 τ'}（若菜單有多檔）。

### 引理 1（現行均衡的浪費，兩種都存在）
對任何 M(w,r,τ)：
(a) 若 client 在空窗 g > τ 選擇 ping：provider 收入 r·P·L·⌊g/τ⌋，支出 c_q·⌊g/τ⌋ +
    c_s·L·g；client 支出 r·P·L·⌊g/τ⌋。**ping 流量是雙輸的死重**：同樣的持有若以顯式
    儲存價 p_s·L·g 交易，兩邊都省（provider 免 c_q，client 免 per-ping 溢價——只要
    p_s < r·P·⌊g/τ⌋/g，而右式 = ping 隱含時價）。
(b) 若 client 放棄：下一回合重寫 w·P·L + provider 重算 c_p·L —— 而持有成本僅 c_s·L·g。
    當 c_s·g < (w−r)·P + c_p 時（實測參數下對所有 g < 數小時都成立），放棄也是雙輸。
∎（(a)(b) 直接代數；實證上兩種行為都被觀測到 = 引理的現實性）

### 定理（P2）：one-bit 合約 M′ 弱 Pareto 支配 M
M′ = { 顯式儲存價 p_s ∈ (c_s, min(ping 隱含時價, 放棄隱含時價)); session 存活即持有、
無 TTL、無 ping；client 可隨時發 **done bit** → 即時回收、停止計費 }。

**(i) Client 端改善**：對每個空窗，M′ 成本 = p_s·L·g < min(ping 成本, 放棄成本)（p_s 的
選取區間非空由引理 1 保證）。對 g ≤ τ 的 client，M′ 與 M 同為零邊際成本 → 弱改善，
長空窗 client 嚴格改善。
**(ii) Provider 端改善**：收入從 {ping 收入 或 重寫收入} 變為 p_s·L·g > c_s·L·g（毛利為正）；
省去 c_q·⌊g/τ⌋ 與重算 c_p·L；死持有從 TTL 尾巴（實測 0.5–5.6% 持有質量）降為 0（bit 即時
回收）。需驗證：收入下降幅度 < 成本節省（p_s 區間的下端由 c_s 撐住、上端由 M 的隱含價撐住
→ 存在使雙方同時改善的 p_s；幅度用實測分佈算出——見 6c 計算計畫）。
**(iii) 誠實性（IC）**：
- 謊報 done（實際會回來）：失去 residency → 下回合付重寫 w·P·L（>省下的 p_s·L·g̃ 對任何
  g̃ < (w·P)/(p_s)……代數給出臨界值；實測 gap 分佈下 99%+ 空窗誠實佔優）。
- 不報 done（實際結束）：持續付 p_s·L·g 直到報告 → 純損失 → 立即報告佔優。
- **關鍵細節**：謊報 done 的臨界值給出一個「自然 TTL」——當 g̃ 極大時 client 本來就該放棄。
  即 M′ 的均衡行為內生地重現「短空窗持有、超長空窗放棄」，但由 client 用私有資訊自選，
  而非 provider 用盲 TTL 硬切 → 這正是效率增益的來源（資訊用在刀口上）。∎（草稿）

## 待補洞（誠實列出）
1. (ii) 的「provider 收入不降」需要對 client 群體分佈積分——用 TraceLab 分佈數值驗證 +
   給出充分條件（p_s 下界式）。
2. 多 client 容量競爭：M′ 下 provider 何時該拒收（連回 mainline 的 admission gate ——
   兩篇的理論在此接合）？初步：p_s 隨佔用率調整 = spot 價；或固定 p_s + admission。
3. 動態偏離：client 混合策略（部分 ping 部分買）在 M′ 下不存在對應物 → 需證明 M′ 的策略
   空間坍縮不傷 client（直覺：M′ 策略空間是 M 的投影）。
4. c_q, c_s 的實證校準來源標註（DRAM 價、GPU 服務成本公開估計）。

## 數值驗證計畫（6c）
用 TraceLab 546 sessions 的 (g, L) 分佈，對 p_s 掃描 [c_s, implied)：畫出兩邊 surplus 曲線，
展示非空的雙贏區間 + 在該區間內的分配（誰拿走多少）。輸出一張小表 + 一張圖，<5KB。

---
# v0.2 主定理改寫（2026-07-06，被數值三連打臉後的正確形狀）

數值事實：任何純定價的 M′（線性儲存價、兩部制 suspend/resume）都無法對 provider 構成
Pareto 改善——因為 **friction 是收入**：真實 trace 上，over-TTL 空窗給 provider 的
friction 收入（min(ping, 重寫溢價) 轉移）≈ 345M token-units，而 friction 的真實效率損失
（ping 服務 + 重算成本 + 死持有）≈ 13M。**浪費的 96% 是租金，不是無謂損失。**

## 定理 A（壟斷下 friction 是均衡）
單一 provider、client 無外部選項時，對任何 client 願意接受的儲存價 p_s，提供 one-bit/
suspend-resume 選項都嚴格降低 provider 利潤（失去 friction 租金 > 省下的效率成本）。
→ 現行合約的低效**對 provider 是激勵相容的**；「為什麼沒人修這個顯而易見的介面」
有了答案。（證明：上面的數值不等式 + 單調性論證。）

## 定理 B（競爭翻轉均衡）
兩個以上 provider、client 轉換成本 σ：挑戰者提供 suspend/resume 可奪取所有
friction 支出 > σ 的 client；當 agent 工作負載的 friction 支出中位數 > σ 時，
背叛是支配策略 → friction 合約在競爭下不可持續。
**野生驗證**：市場結構恰好如模型預測——在位者（Anthropic/OpenAI）維持 TTL+倍率菜單，
挑戰者 DeepSeek 用磁碟 cache 把 residency 近乎白送（98% off、無 TTL 遊戲）、
Gemini 走顯式儲存計價。合約形態 = 市場位置的函數，可用五家菜單實測對照檢驗。

## 論文的機制層最終形狀（Ostrovsky–Schwarz / Artola-Velasco 形）
1) 量測：合約 vs 行為的落差 + 各家 friction 收入份額（公開菜單 × 我們的 trace 分佈）。
2) 定理 A/B：低效的激勵解釋 + 競爭閾值。
3) 介入設計：對 client——最優 ski-rental/breakpoint 策略（把租金還給 client）；
   對市場——one-bit 合約作為競爭均衡的自然終點；預測可被後續市場演化檢驗（longitudinal）。

## Venue 註記（genre 調查結論）
外部審計類：IMC/SIGMETRICS/ATC 為正宗；經濟層 EC/TEAC/NetEcon；LLM 審計 ICML 亦收
（Artola-Velasco ICML'26 oral 即同形狀）。**ASPLOS 對此文體是弱配適**——V6 的冷審
venue 參數建議改 SIGMETRICS 或 IMC（待使用者確認,mainline 仍 ASPLOS）。
