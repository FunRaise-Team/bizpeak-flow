# BizPeak Flow — Task Plan
**Created**: 2026-07-02
**Status**: in_progress
**Goal**: 完成 BizPeak Flow 立項規劃 — 完整規格 + Notion 視覺化提案 + HTML 一頁式互動提案、並定義「主幹道 + 卡帶」擴充規範。

---

## Tasks

### Phase 0: 環境與研究
- [x] 專案資料夾 `~/work/bizpeak-flow/`（git init、公司身份 nelsen.chen@funraise.com.tw 驗證通過）
- [x] Clone `FunRaise-Team/AI-raiser-planning` → `~/work/AI-raiser-planning`（憑證路由自動用 Nelsen-funraise）
- [x] 抓取 Notion 會議記錄頁（391b2192...）— 立項決策、分工、開放問題全數落檔 findings.md
- [x] 研究工作流 `wf_3e35494e-76a`（5 路平行、sonnet、約 41 萬詞元隔離在子代理）— 5 份檔案落 docs/research/、共 610 行

### Phase 1: 規格文件（研究回來後、Q 主筆）
- [x] `docs/SPEC.md` — 產品規格（狀態機 C0-C7、款項 P0-P4、催收梯級、三入口、通知矩陣、簽署分級）
- [x] `docs/ARCHITECTURE.md` — 三選項各列炸點、拍板選項 B（獨立平台、沿用儀表板已驗證組合）
- [x] `docs/CARTRIDGE-SPEC.md` — 四件套契約 + L0/L1/L2 三級接入制
- [x] `CONSTITUTION.md` — 憲法七條草案（待 Nelsen 批准）

### Phase 2: 提案交付
- [x] `proposal/index.html` — 一頁式互動提案（FUNRAISE 品牌、互動狀態機、體驗分頁、路線圖）
- [x] Notion 提案頁寫入 — 66 區塊、13 章節（scripts/publish_notion_proposal.py、冪等）
- [x] 對話內白話執行摘要給 Nelsen

### Phase 3: 驗證與收尾（Rule 7 三證據）
- [x] Notion fetch-back 驗證 — 13 個 H1 全數確認、標記存在 True
- [x] HTML 實測 — preview 伺服器 :8774、點 C5 狀態明細正確、1.5 分頁切換正確、零 console 錯誤、截圖存證
- [x] git 初始 commit（本地、不推遠端 — 遠端歸屬待 Nelsen 四問拍板）
- [x] 決策回寫 `~/Brain/decisions/log.md` + `~/Brain/companies/funraise/products/bizpeak-flow.md`

### Phase 3.5: v0.2 修正輪（2026-07-02 傍晚、Nelsen 60 分回饋後）
- [x] 去 AI 味研究（3 路工作流）→ 全域規則落地（feedback_de_ai_design_taste.md + design-taste 武器三 + MEMORY.md 🔴）
- [x] 提案頁重製：文件體裁（章節編號 / 目錄 scrollspy / hairline / 等寬元資料）、量化驗證有色邊條 0、常駐陰影 0
- [x] Codex Image-2 四張配圖（主機卡帶 / 生命週期閉環 / 三入口 / 互動情境）、generation-log 驗證無後製
- [x] 高擬真示意畫面（收款佇列 / 1.5 續約草稿對話 / 2.0 MCP 對話、全虛構資料）
- [x] BizPeak 正名 + 品牌座標（依品牌架構頁、Teams 命名模式）
- [x] SPEC v0.2：自建簽核引擎（NuEIP 降可選 adapter）+ §7.5 五個代理能力
- [x] GitHub：FunRaise-Team/bizpeak-flow（private）已推
- [x] Vercel：https://bizpeak-flow-proposal.vercel.app 上線、外部可達驗證 200
- [x] Notion v0.2 換版（舊 66 塊封存、新 49 塊、fetch-back 驗證）

### Phase 3.6: v0.3 修正輪（2026-07-02 晚、Nelsen 六條回饋後）
- [x] 版面修正：版心 1240、正文 720px（中文 45 字/行、修「換行窄」根因）、來源引用移右欄
- [x] 內部語境清洗：底稿 / Raiser / 九步流程字樣 0 殘留（量化驗證）；「不是 X 而是 Y」句型 0
- [x] 三階段定義修正：1.5＝既有介面長出聊天框（含 JS 時序動畫演示：聊天 → 導航 → 表單帶入 → 人審）；2.0＝外部 AI 應用 × MCP（個人信箱檔案 × 合約系統、工具呼叫卡）
- [x] Codex 重畫 piece-4（介面＋聊天框）＋ 新增 piece-5（AI 應用中樞）— 同主題 resume、無後製
- [x] 1.0 新增完整合約總覽 mock（含生命週期進度軌道）
- [x] 技術架構：CSS 結構圖＋「技術棧與 RD 定案」旗標＋兩路建議（GCP 主線 / 原型先行）、Supabase 從拍板降為原型選項
- [x] 路線圖壓縮：本週定稿 → 下週 1.0 上線 → 7 月中 dogfooding → 8 月 MCP 化＋商轉評估 → 9 月產品化
- [x] SPEC §8/§11、ARCHITECTURE §2 同步；Notion v0.3 換版（舊 49 塊封存、新 51 塊）；Vercel 重部署外部驗證 200

### Phase 3.7: v0.4 輪（2026-07-02 深夜、公開＋轉移＋泳道＋POC）
- [x] 研究檔清洗：內部盤點三份分流 docs/research-internal/（gitignore）、`ARCHITECTURE.md` 認證細節中性化、全庫敏感詞複掃 0
- [x] git 歷史重建（單一乾淨提交）→ repo 轉 public、匿名可讀驗證
- [x] 提案 §7 轉移與嵌入：雙態滑動圖（13 節點、借鏡尊鴻 blueprint）＋去留表＋三步導入；docs/MIGRATION.md
- [x] 提案 §8 Agentic 作業泳道：6 泳道 × 6 階段、可播放閉環、資料落庫標示 — 互動全數實測
- [x] POC：poc/（狀態機＋Notion 層＋四庫建置＋MCP 六工具）、驗收 PASS、已掛 Claude Code（✓ Connected）
- [x] Notion v0.4（14 章節、59 塊）＋ Vercel 部署外部驗證 v0.4

### Phase 4: 拍板後才動（不在本次範圍）
- [ ] 使用者訪談（Ting / Glendy / Carol）→ 規格細化
- [ ] 體驗 1.0 開發（Allen 主導搭建、Jaric 技術、拉兩位 RD）
- [ ] 提案頁搬公司 Vercel 帳號（需 Nelsen 登入）

---

## Decisions Made

| Decision | Rationale | Date |
|----------|-----------|------|
| 專案放 `~/work/bizpeak-flow/` | FUNRAISE 公司資產、includeIf 自動套公司 email（Rule 2） | 2026-07-02 |
| 先不建 GitHub 遠端 | 歸屬四問（org / visibility）屬 Nelsen 拍板事項、local git 先跑 | 2026-07-02 |
| Notion 讀寫全走 integration token 直打 API | feedback_notion_mcp_migration.md v2 規則 | 2026-07-02 |
| 研究派 5 路 sonnet 子代理、只回摘要 | Nelsen 詞元節約指示 + Rule 14 噪音隔離 | 2026-07-02 |

---

## Blocked On
- Phase 4 全數卡在 Nelsen 拍板（七題、見 SPEC.md §10 / Notion 提案 ⑪）

---

## Next Action
本週：Carol 排訪談（Ting / Glendy、用 docs/MIGRATION.md §4 清單）＋ Jaric × RD 技術棧定案 → 下週體驗 1.0 上線（概念驗證的能力層與狀態機直接沿用）。
