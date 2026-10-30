# RunGuard：專案管理與 Agent 工作指南

適用於整個 repository。最近盤點：2026-10-22。

本文件提供開發入口、目前進度與必須遵守的契約。詳細設計與歷史決策留在
milestone 規格及 ADR；功能或進度改變時，請同步更新本文件。

## 1. 專案定位與當前焦點

RunGuard 比較機器學習實驗的 baseline 與 candidate，透過多個 seed 的配對分析，
提供可重現、可追溯的回歸測試證據。長期目標是將證據轉為可配置的 release decision。

產品方向：資料載入 → canonical model → 可比較性驗證 → seed 配對 → 統計證據
→ findings → policy → Pass / Warn / Fail。此流程尚未全部實作。

**目前焦點：M3 — Statistical Evidence Engine，目標版本 `v0.0.4`。**
M2 規格標示 Completed；M3 已改為 Active，已有 bootstrap、effect size、
leave-one-pair-out sensitivity 與 evidence object，但不能據此認定 M3 已完成。

| 階段 | 已有能力 | 邊界與剩餘工作 |
| --- | --- | --- |
| M0 基礎設施 | Python package、CLI、pytest、Ruff、mypy、pre-commit、GitHub Actions CI | `minimal.py` 為早期流程，新能力沿 canonical 路徑開發 |
| M1 Canonical model | Pydantic v2 strict models、三種本機 JSON 格式、驗證與 round-trip 測試；changelog 有 `0.0.2` 條目 | 不包含遠端來源、schema migration 或 artifact storage |
| M2 本機配對比較 | seed 配對、metric direction、平均、中位數、positive-pair rate、run provenance；changelog 有 `0.0.3` 條目 | 只讀 summary；CLI 為文字輸出 |
| M3 統計證據 | bootstrap 參數／結果模型、`bootstrap_mean`、paired `d_z`、positive-pair evidence、mean-vs-median、leave-one-pair-out sensitivity、`build_paired_evidence` 與單元測試 | 尚缺 checkpoint、multi-metric、benchmark fixtures 與 CLI 整合 |
| 後續里程碑 | 規劃記於 `ROADMAP.md` | findings、release policies、W&B／MLflow adapters 尚未實作 |

## 2. 開工與交付流程

1. 查看 `git status`，保留既有未提交變更。
2. 閱讀本次工作對應的 milestone、ADR、程式與測試，確認範圍及驗收條件。
3. 聚焦當前 milestone；超出 non-goals 的構想記入後續規劃。
4. 依下方模組邊界與資料契約實作，執行適當檢查。
5. 同步相關規格、進度與 release notes，回報變更、實際驗證和剩餘限制。

非瑣碎工作依 milestone → issue → branch → PR → tests → release notes 追溯。
Agent 新建分支預設使用 `codex/<change>`；commit 採 Conventional Commits，
例如 `feat(statistics): ...` 或 `docs: ...`。完整協作規則見 `CONTRIBUTING.md`。

高成本或跨模組的設計決策記錄於 ADR；局部且容易反轉的選擇不必新增 ADR。
`main` 必須保持可安裝並通過必要檢查。里程碑完成與發布須滿足對應 release gate，
不能只因 planned issues 已做完就標記完成。

## 3. 文件導航

| 要確認的內容 | 文件 |
| --- | --- |
| M3 契約、驗收與未決問題 | [M3 規格](docs/milestones/M3-statistical-evidence-engine.md) |
| Canonical model 的設計與回顧 | [M1 規格](docs/milestones/M1-canonical-experiment-model.md) |
| 本機配對比較的交付範圍 | [M2 規格](docs/milestones/M2-local-paired-comparison.md) |
| 待決 trade-off 與已定技術選型 | [Trade-off 紀錄](docs/architecture/tradeoffs-and-tech-choices.md) |
| Summary、方向與 pairing 語意 | [ADR-0004](docs/adr/ADR-0004-comparison-value-semantics.md) |
| 架構與依賴邊界 | [ADR-0001](docs/adr/ADR-0001-modular-monolith.md) |
| 開發及 PR 流程 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 里程碑管理與長期方向 | [Milestone 管理](docs/milestones/README.md)、[ROADMAP.md](ROADMAP.md) |
| 產品介紹與版本紀錄 | [README.md](README.md)、[CHANGELOG.md](CHANGELOG.md) |

現有能力以程式和測試確認；預期行為依相關 ADR 與詳細 milestone 規格判讀。
遇到衝突應記錄並同步修正，不能將規劃描述當成已實作功能。

## 4. 程式結構與依賴邊界

```text
src/runguard/
  domain/models.py          canonical experiment、run、metric models
  sources/local_json.py     本機 JSON 載入與格式轉換
  comparison/models.py      metric direction、pair、comparison result
  comparison/paired.py      canonical seed 配對與 summary 比較
  comparison/minimal.py     M0 早期最小比較流程
  statistics/models.py      bootstrap、effect size 與 evidence models
  statistics/bootstrap.py   percentile bootstrap 實作
  statistics/effect_size.py paired Cohen's d_z
  statistics/sensitivity.py leave-one-pair-out sensitivity
  statistics/evidence.py    由 ComparisonResult 建立 PairedEvidence
  cli/main.py               argparse 入口與模組組合
tests/
  unit/                     模組與契約測試
  integration/              compare CLI 端到端測試
  fixtures/                 有效、無效與合成實驗資料
docs/
  milestones/               詳細範圍、驗收、決策與回顧
  adr/                      架構決策
```

採 modular monolith，一個可安裝的 Python package：

- `domain` 不依賴其他內部模組，也不依賴 tracking SDK 或來源 JSON 格式。
- `sources` 將外部資料轉成 domain objects，分析模組不直接讀取來源格式。
- `comparison` 與 `statistics` 不直接依賴 source adapter、W&B 或 MLflow SDK。
- CLI 負責組合資料來源與分析；計算邏輯留在分析模組。
- 新功能優先擴充 canonical 路徑，避免回頭擴充 `comparison/minimal.py`。
- `findings/`、`policies/` 目前只有空目錄，遠端 adapters 尚未建立，不能假定相關 API 已存在。

## 5. 已交付能力與資料契約

### M1：Canonical experiment model

`domain/models.py` 使用 Pydantic v2 的 `strict=True, extra="forbid"`，
避免不透明的型別轉換與額外欄位被靜默忽略。

| Model | 責任與驗證 |
| --- | --- |
| `MetricPoint` | 保存 step 與 value；value 可為 `None` |
| `MetricSeries` | 保存 points，拒絕重複 step，依 step 遞增排序 |
| `RunConfig` | 保存 run 設定 |
| `ArtifactReference` | 保存 URI、可選類型與 digest；不下載或驗證 artifact |
| `Run` | 保存 run ID、可選 variant／seed、config、history、summary、artifacts 與 source metadata |
| `ExperimentGroup` | 保存 group ID 與 runs；要求 group 內 run ID 唯一 |

必須保留以下語意：

- Run ID 的唯一性限於同一 group；沒有 seed 的 run 可以保存，但不能參與 seed 配對。
- History 使用 point list，保留 step 語意並能檢查重複值。
- Missing value 明確保留；ingestion 不擅自刪除，下游依明確契約處理。
- Summary 與 history 分開保存，不推定 summary 等於 best 或 final checkpoint。
- 來源特有 metadata 與 artifact 資訊透過對應欄位保留。

`load_local_json()` 由呼叫端明確指定格式，不自動猜測：

| 格式 | 轉換方式 |
| --- | --- |
| `canonical` | 直接驗證 `ExperimentGroup` |
| `nested` | 驗證來源格式，將 history dictionary 轉為 `MetricSeries` |
| `m0` | 驗證 flat scalar metrics，轉為 summary；必須提供 group ID，不虛構 history |

M1 測試涵蓋 serialization、round-trip、missing value、duplicate step 與 duplicate
run ID。Timestamp normalization、public schema compatibility、自動 migration、
artifact storage 與遠端 API 不在已交付範圍。

### M2：本機 canonical paired comparison

`compare_group()` 接收 `ExperimentGroup`、兩個 variant、metric 與 direction，
回傳 `ComparisonResult`。目前只讀 `Run.summary_metrics[metric]`，
`value_source` 固定為 `summary`，缺值時不可自動改讀 history。

| 數值 | 定義 |
| --- | --- |
| `raw_difference` | candidate − baseline |
| `improvement_difference`，higher-is-better | candidate − baseline |
| `improvement_difference`，lower-is-better | baseline − candidate |
| Positive pair | `improvement_difference > 0`；平手不算 |
| Positive-pair rate | positive pair 數 ÷ 有效 paired observations 數 |

每個 pair 保留 seed、兩個 run ID、原始值與兩種 difference，並依 seed 排序。
Aggregate 保留 group、variants、metric、direction、value source，以及 raw／improvement
的平均、中位數、positive pair 數與比例。

以下情況必須以 `ComparisonError` 明確失敗：

- Baseline 與 candidate variant 相同，或 direction 不受支援。
- 選取的 run 缺 seed，或同一 `(variant, seed)` 出現多筆 run。
- 指定 summary metric 不存在或值為 `None`。
- 兩邊 seed 集合不同，或沒有可配對的 run。

不可默默丟棄 unpaired runs、補零、覆蓋重複資料或改變分母。
Seed 配對不代表已驗證 dataset、code revision 與 config 的可比較性。

CLI 支援 `--input-format {m0,nested,canonical}`、`--group-id`、兩個 variant、
metric、`--pair-by seed` 與兩種 direction。文字輸出包含 value source、direction、
pair 數、raw difference 的平均／中位數與 positive-pair rate；尚無 JSON 輸出。
Checkpoint selection、統計 evidence、incomplete-pair 模式與 release policies 均未包含於 M2。

## 6. M3 實作契約與待辦

M3 輸出統計證據及限制，不產生 severity、因果結論或 Pass / Warn / Fail。
下列是目標契約；bootstrap、effect size、positive-pair、leave-one-pair-out 與 evidence object 已實作，
其餘仍需分段實作與驗收。

| 能力 | 契約 |
| --- | --- |
| Bootstrap | 對已配對的 direction-aware improvement 抽樣，不獨立抽 baseline／candidate |
| 預設參數 | Mean 的 95% percentile interval、10,000 resamples，明確記錄 random seed |
| 樣本不足 | 少於兩個 pair 時，`PairedEvidence` 以 `InsufficientEvidence` 表達；底層 `bootstrap_mean` 仍以 `BootstrapError` 拒絕 |
| Effect size | Paired Cohen's `d_z`，sample standard deviation 使用 `n - 1`；零變異回報 `zero-variance` insufficient evidence |
| Leave-one-pair-out | 只對 mean；保留移除的 seed／run IDs、完整與移除後平均、signed（`loo - full`）／absolute change；最大影響完全平手時取最小 seed |
| Final checkpoint | 選最大 step；末點 missing 必須回報 missing evidence |
| Best checkpoint | 依 direction 選最佳值，平手選最早 step；無有效值時回報 missing evidence |
| Provenance | 保留輸入 pairs、來源 run IDs、方法參數、checkpoint policy／step、假設與限制 |

不自動刪除 outlier，也不將 influence 數字直接轉成「被單一 seed 主導」的結論。
主要 benchmark 目標約十組 paired seeds，與 bootstrap resamples 數量分開記錄。

接手順序：依 M3 planned issues 接續 checkpoint、multi-metric、benchmark 與
CLI 整合；開工前先查看 trade-off 紀錄中對應的待決項目（例如 checkpoint 選值的 D1）。配置相容欄位、額外 incomplete-pair 模式及 multi-metric CLI 仍有未決問題，
請查閱 M3 規格，不自行視為已定案。

## 7. 開發環境與驗證

Python 需求為 `>=3.11`，`.python-version` 與 CI 使用 3.11；runtime dependency
為 Pydantic v2。優先使用既有 `.venv`；新環境設定如下：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

本機 smoke example：

```bash
.venv/bin/runguard compare \
  --input tests/fixtures/stable-improvement.json \
  --baseline baseline --candidate candidate \
  --metric val_f1 --pair-by seed
```

程式變更提交前執行：

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/pre-commit run --all-files
```

Integration test 會從 PATH 呼叫 `runguard`；未 activate venv 時請先
`export PATH="$PWD/.venv/bin:$PATH"`，否則該測試會以 `FileNotFoundError` 失敗。

Ruff 設定為 Python 3.11、88 字元、`E/F/I`；mypy 採 strict。
CI 執行 pytest、Ruff 與 mypy；pre-commit 包含 Ruff lint 與 format。

測試須涵蓋變更涉及的方向語意、缺值、重複配對、可重現性與 provenance；
統計計算需有獨立 reference expectation。純文件變更檢查內容、連結與範例即可。
只回報實際執行的檢查結果。

## 8. 已知落差與管理待辦

以下為 2026-10-22 本機盤點，尚未修復。修改相關區域時重新確認並更新此清單。

| 項目 | 待處理內容 |
| --- | --- |
| Milestone 狀態 | M1 仍為 Active、M2 為 Completed、M3 為 Active；M1 狀態需對齊實際交付 |
| 版本 | 已對齊：`pyproject.toml` 與 changelog 皆為 `0.0.3`；M3 發布時同步改為 `0.0.4`（trade-off D9） |
| README | 架構樹與功能敘述包含規劃；範例的 confidence interval、finding 與建議尚非 CLI 現有輸出 |

M3 只有在規格的 success criteria、驗證、文件、回顧及 release gate 全部滿足後，
才可標記完成。
