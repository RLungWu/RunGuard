# 技術選型與 Trade-off 紀錄

最近更新：2026-10-30（M3 進行中，目標 `v0.0.4`）

本文件是輕量的決策登記簿：記錄**需要拍板的 trade-off**、最後的決議與落實位置，
以及**已定案的技術選型**與其代價。它不取代 ADR 與 milestone 規格：

- 高成本、跨模組或難以反轉的決策 → 定案後升格為 ADR（`docs/adr/`）。
- 只影響單一 milestone 的決策 → 定案後寫入該 milestone 的「Decisions Made During
  Implementation」。
- 新的待決項目以「待決」狀態加入第 1 節；定案後更新狀態與落實位置。

每個條目格式：背景 → 選項與 trade-off → 決議 → 落實位置。

---

## 1. 決策紀錄

D1–D10 於 2026-10-30 依建議定案。

| ID | 主題 | 狀態 | 落實位置 |
| --- | --- | --- | --- |
| D1 | Checkpoint 值如何進入比較流程 | 已定案，API 已實作（CLI 待 D7） | ADR-0004、`comparison/selection.py` |
| D2 | Bootstrap 亂數跨版本可重現性 | 已定案 | `statistics/bootstrap.py` |
| D3 | 純標準庫 vs NumPy／SciPy | 已定案，已實作 | runtime 維持標準庫；NumPy／SciPy 為 dev-only reference（`tests/unit/test_scipy_reference.py`） |
| D4 | Incomplete-pair 模式 | 已定案 | M3 規格 Open Questions |
| D5 | 可容許差異的 config 欄位 | 已定案，已實作 | `comparison/config.py`；benchmark fixtures |
| D6 | Multi-metric 衝突定義與 CLI | 已定案，API 已實作 | `statistics/multi_metric.py`；CLI 依決議不暴露 |
| D7 | CLI evidence 輸出格式 | 已定案，待實作 | CLI 整合 slice |
| D8 | Median CI 與 BCa | 已定案 | M3 規格 Open Questions；已知限制 |
| D9 | 版本號對齊 | 已定案 | `pyproject.toml` |
| D10 | ADR 編號漂移 | 已定案 | `ROADMAP.md`；ADR-0002／0003 待補寫 |

### D1. Checkpoint 值如何進入比較流程

- **背景**：M2 的 `ComparisonResult.value_source` 固定為 `Literal["summary"]`，
  `ComparisonPair` 沒有 step 或 policy 欄位。M3 要求 best／final checkpoint，
  且 provenance 必須保留 policy 與 selected step（ADR-0004 已規定不可 fallback）。
- **選項**：
  - A. 在 `ComparisonPair` 加 optional `baseline_step`／`candidate_step`，
    `value_source` 擴成 enum（`summary`／`history-final`／`history-best`）。
    改動小，但 summary 情境下會出現一堆 `None` 欄位。
  - B. 在 `comparison` 新增獨立的 value-selection 步驟，產出
    `SelectedValue(value, source, policy, step)`，`compare_group` 接收 value policy
    參數，pair 保存 `SelectedValue`。語意最清楚，但會改動 M2 的 pair schema。
  - C. 只在 `statistics` 層處理 checkpoint，`comparison` 不知道。違反
    「統計模組不重做配對」的 M3 context。
- **決議**：B。checkpoint 是「選值」而非「統計」，放在 `comparison` 符合 ADR-0004；
  schema 改動趁 `v0.0.4` 前（尚無 public schema 承諾）做最便宜。
- **實作細化（2026-10-30）**：同一個 comparison 只套用一種 value source／policy，
  所以 source 與 policy 記在 `ComparisonResult` 一次；每個 pair 只記
  `baseline_step`／`candidate_step`，避免在 pair 裡重複存 run ID 與 value。
  選值邏輯仍是 `comparison` 內的獨立步驟（`comparison/selection.py`），
  result 驗證 step 與 value source 一致。
- **落實**：[ADR-0004 Value selection](../adr/ADR-0004-comparison-value-semantics.md#value-selection)；
  `comparison/selection.py`、`compare_group(value_source=..., checkpoint_policy=...)`。
  CLI 尚未暴露，併入 CLI 整合 slice。

### D2. Bootstrap 亂數的跨版本可重現性

- **背景**：`bootstrap_mean` 原本使用 `random.Random(seed).choices(...)`。Python 文件
  只保證 seeding 與 `random()` 序列跨版本穩定，`choices()` 等高階方法的演算法
  **不保證**。CI 與 `.python-version` 固定 3.11，但 `requires-python = ">=3.11"`。
- **選項**：
  - A. 維持現狀，在 evidence provenance 記錄 Python 版本。成本最低，但「同 seed
    同結果」只在同版本成立。
  - B. 自行用 `floor(rng.random() * n)` 抽 index（與 3.11 `choices` 無權重時的行為
    相同，現有結果不變），只依賴有保證的 `random()`。
  - C. 改用 NumPy `Generator`。效能好，但新增 runtime dependency，且 NumPy 也不保證
    `Generator` 方法的 stream 跨版本相容（NEP 19）。
- **決議**：B，並加「固定 seed → 固定 interval」的 golden test 防回歸。
- **落實**：`statistics/bootstrap.py` 與 `tests/unit/test_bootstrap.py`。

### D3. 數值計算依賴：純標準庫 vs NumPy／SciPy

- **背景**：目前 runtime 只有 Pydantic；統計全用 `random`／`statistics`。
- **Trade-off**：純 Python 安裝輕、行為透明、容易手算驗證；10 pairs × 10,000
  resamples 只約 10 萬次抽樣，速度沒問題。但 multi-metric × 多組比較、或 M9 的
  10,000 runs 規模下可能變慢；BCa 等方法自己實作的正確性風險較高。
- **決議**：M3 維持 runtime 純標準庫。SciPy 可加入 **dev-only** 依賴，作為
  bootstrap／`d_z` 的獨立 reference（只用於測試，不進 runtime）。效能問題等 M9
  benchmark 有數據再談。
- **落實**：`pyproject.toml` 的 dev extra 加入 NumPy／SciPy；`tests/unit/test_scipy_reference.py`
  以 NumPy 檢查 `d_z`、以 `scipy.stats.bootstrap` 檢查 percentile interval。SciPy 使用不同
  RNG，容許誤差定為 0.25 個 mean standard error（實測最大約 0.16）。點統計另以
  `Fraction` 精確 reference 檢查（benchmark tests）。

### D4. Incomplete-pair 模式是否在 M3 實作

- **選項**：A. M3 只支援 strict；B. M3 加 opt-in 模式並記錄 denominator 與缺漏 runs。
- **Trade-off**：B 讓探索性分析更方便，但等於提前做「missing data 該如何處置」的
  policy 決策，而 ROADMAP 的 M5 policy 範例已有 `missing_data.action`。
- **決議**：A。M3 只保證 strict 模式下缺漏 seed 被**完整列出**；寬鬆模式留給 M5 policy。
- **落實**：M3 規格 Open Questions；benchmark「missing paired runs」情境以完整列出
  缺漏 seed 為預期 evidence。

### D5. 可容許差異的 config 欄位

- **Trade-off**：寫死允許清單太僵；完全不檢查又違反「可比較性驗證」。哪些差異是
  treatment、哪些是混淆，本質上是使用者政策。
- **決議**：M3 只產出**描述性 evidence**（兩邊 config 的差異鍵與值），不判斷相容與否；
  允許清單交給 M5 policy。
- **落實**：`comparison/config.py` 的 `compare_run_configs`，使用既有 `ComparisonResult`
  的 pairs，只比較 top-level `RunConfig.values`，型別敏感（`1`、`1.0`、`True` 視為不同），
  缺 key 與明確 `None` 分開記錄。benchmark 的 incompatible／confounded 情境以
  「差異被如實列出、沒有相容或因果欄位」作為預期 evidence。

### D6. Multi-metric 衝突的定義與 CLI 曝光

- **背景**：要「識別 primary 與 secondary 的方向衝突」但不能產生結論。
- **選項**：
  - A. `direction_conflict` 僅以兩個 metric 的 mean improvement 正負號定義，無門檻。
  - B. 以 CI 是否跨 0 定義。更有統計意義，但已接近 M5 的 CI policy。
- **決議**：A 放在 API，並同時保留兩個 metric 的完整 `PairedEvidence`，讓 B 之後由
  policy 層自行計算。CLI 在 M3 只暴露單一 metric evidence，multi-metric CLI 等 M4
  report 模型。
- **落實**：`statistics/multi_metric.py` 的 `build_multi_metric_evidence`。另加一個不影響
  旗標的描述性欄位 `opposing_pair_count`（兩個 metric 在同一 pair 方向相反的數量），
  讓 policy 層能區分「平均相反」與「逐 seed 相反」。

### D7. CLI evidence 輸出格式

- **選項**：A. 只有文字；B. 文字預設 + `--format json` 輸出 `PairedEvidence`。
- **Trade-off**：JSON 對 CI 與測試最實用，但一旦有人依賴就等於 public schema，而
  schema versioning 是 M4 的範圍。
- **決議**：B，但在 help 與 README 明確標示 JSON 為 experimental、不承諾相容性，
  直到 M4 加 schema version。
- **落實**：CLI 整合 slice（M3 最後一個實作 slice）。

### D8. Median CI 與 BCa

- **Trade-off**：約 10 個 pairs 時，percentile interval 的 coverage 可能偏低；BCa
  修正較好但需要 jackknife，實作與驗證成本高。Median 的 bootstrap 在小樣本下
  分佈非常離散。
- **決議**：`v0.0.4` 只做 mean 的 percentile CI；mean-vs-median 差值與 leave-one-out
  已能描述穩健性。若 benchmark 顯示 coverage 明顯不足，再開 issue 評估 BCa。
- **落實**：M3 規格 Open Questions；release notes 列為已知限制。

### D9. 版本號對齊

- **背景**：`pyproject.toml` 曾是 `0.1.0`，但 ROADMAP 把 `v0.1.0` 定義為第一個 stable
  release；changelog 最新是 `0.0.3`。
- **決議**：`pyproject.toml` 改為 `0.0.3`（反映已發布狀態），M3 發布時改 `0.0.4`。
- **落實**：`pyproject.toml`。

### D10. ADR 編號漂移

- **背景**：ROADMAP 規劃 ADR-0002（canonical domain model）、ADR-0003（分析與自然語言
  解釋分離），但兩者尚未撰寫；同時 ROADMAP 在 M4 規劃的 ADR-0004（findings）與
  實際的 ADR-0004（comparison value semantics）撞號。
- **決議**：保留實際 ADR-0004；補寫 ADR-0002／0003（內容大致已在 M1 規格與
  AGENTS.md）；ROADMAP 中 M4 之後的 ADR 改為「待編號」，撰寫時再依序取號。
- **落實**：`ROADMAP.md` 已改為待編號；ADR-0002／0003 尚待補寫。

---

## 2. 已定案的技術選型

| 領域 | 選擇 | 主要代價 | 紀錄 |
| --- | --- | --- | --- |
| 架構 | Modular monolith，單一 Python package，模組邊界靠慣例與 review | 邊界沒有 runtime 強制，需靠 review（之後可加 import lint） | [ADR-0001](../adr/ADR-0001-modular-monolith.md) |
| 語言與工具 | Python ≥ 3.11、hatchling、argparse、pytest、Ruff（E/F/I）、mypy strict、pre-commit | argparse 對複雜子命令較囉嗦，但零依賴 | `pyproject.toml` |
| Domain model | Pydantic v2 `strict=True, extra="forbid"` | 輸入必須型別精確，來源轉換工作落在 adapter | [M1](../milestones/M1-canonical-experiment-model.md) |
| 比較值語意 | 只讀 summary、無 fallback；保留 raw 與 direction-aware 兩種差值 | 會拒絕可能有用的資料；checkpoint 另立選值步驟（D1） | [ADR-0004](../adr/ADR-0004-comparison-value-semantics.md) |
| 配對 | 依 seed 嚴格配對，缺漏、重複、缺值皆明確失敗；M3 不提供寬鬆模式（D4） | 探索性分析不便 | [ADR-0004](../adr/ADR-0004-comparison-value-semantics.md) |
| Bootstrap | 對 paired improvement 抽樣；mean、95%、percentile、10,000 次、明確 seed；依 seed 順序輸入；index 由 `random()` 推導（D2） | 小樣本 coverage 可能不足（D8） | [M3](../milestones/M3-statistical-evidence-engine.md) |
| Effect size | Paired Cohen's `d_z`，`n - 1` 標準差；零變異回報 `zero-variance` | 不提供 small／medium／large 標籤 | [M3](../milestones/M3-statistical-evidence-engine.md) |
| Positive pair | `improvement > 0`，平手不算 | 對極小差異敏感，但定義單純且方向一致 | [ADR-0004](../adr/ADR-0004-comparison-value-semantics.md) |
| 統計數值依賴 | Runtime 純標準庫（`random`、`statistics`）；NumPy／SciPy 只作 dev-only reference（D3） | 大規模時效能未知；dev 環境安裝較重 | 本文件 D3 |
| Evidence 原則 | Evidence 由 pairs 重算、不信任上游 aggregate；只描述不下結論；不足時用 `InsufficientEvidence` 而非數字 | 物件欄位較多 | [M3](../milestones/M3-statistical-evidence-engine.md) |
| Leave-one-pair-out | 只對 mean 做；`signed_change = loo_mean - full_mean`；最大影響以浮點數完全相等判斷平手，平手取最小 seed；保留每個 pair 的完整數值 | 浮點誤差可能讓「幾乎平手」的兩個 seed 之一被選中；因每個 pair 數值都保留，資訊不會遺失 | [M3](../milestones/M3-statistical-evidence-engine.md) |
| Mean vs median | 以 `mean_minus_median_improvement`（帶正負號）表達，不設門檻 | 是否「偏態嚴重」留給 policy 層 | [M3](../milestones/M3-statistical-evidence-engine.md) |
