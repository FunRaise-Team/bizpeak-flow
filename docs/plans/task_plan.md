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

### Phase 3.8: POC 升級 1.0＋1.5（2026-07-03 上午、Nelsen 指示「分享時要有雛形」）
- [x] capabilities.py 能力層抽出 — 網頁 / 聊天 / MCP 三入口共用（能力先於介面的實作證明）
- [x] app.py 網頁應用（四頁籤真資料、推進與收款按鈕實寫 Notion）＋ /api/chat（Gemini 函式呼叫）
- [x] web/index.html 前端（原生零建構鏈）；launch.json 加 bizpeak-poc-app（:8790）
- [x] 實測：聊天寫入全鏈（自然語言→查編號→C2→C3→Notion 實寫→留痕→前端切頁高亮）、非法轉移被擋、MCP 驗收 PASS、介面零錯誤＋截圖
- [x] 排障：POC Notion 頁被移入垃圾桶（父頁 in_trash）→ API 還原、查詢恢復

### Phase 3.9: POC 閉環輪（2026-07-03 中午、Nelsen「像已可上線、至少跑通」）
- [x] 資料層遷至私人區：Notion「Personal Notes」→「BizPeak Flow — 資料層」（392b2192-4515-81e5-b756-f414b4ac1980）、舊頁封存、四庫重建（合約加期數／首期日欄）
- [x] 能力層補閉環：contract_create / contract_renew / payment_invoice、C4 自動產生款項排程、C6 未收清擋結案（終端不變量）
- [x] 三入口同步九能力；聊天提示詞帶當日日期（修「八月十五 → 2024」誤判、複驗 2026-08-15）
- [x] 前端：建約表單、開票、開新約、現金流長條頁、角色視角切換（業務／財務／管理層）
- [x] 驗收：test_e2e.py 18/18 PASS（建約→C4 自動排程→守門→開票→收款→結案→續約新約 C0）；MCP PASS；介面六項實測＋截圖
- [x] 伺服器由預覽面板託管（:8790）、已開給 Nelsen 測試

### Phase 3.10: POC v3 上線輪（2026-07-03 下午、Nelsen「更細緻＋上線分享」）
- [x] 公司資料串接：客戶大名單（514 家、Account Owner 當負責人來源）、報價 DB（9 筆已簽約可一鍵建約）；同事帳號庫未分享給整合（404、已回報）
- [x] 詳情面板（修「點不開」根因 — 原展開列不明顯）、日曆視圖、負責人載量卡、每列 Notion 直達連結
- [x] LLM 供應商切換層：gemini 預設（免費層足夠）/ nvidia 備援（實測免費端點兩度逾時、不設預設）
- [x] 上線：Vercel bizpeak-flow-app ＋ 存取關卡（伺服器端金鑰）；險情：環境變數帶換行 500 ＋ 除錯回傳外洩 Notion 權杖（已修、建議輪替）
- [x] 線上驗證：關卡 401/200、資料、聊天、報價匯入清單全綠；Notion 提案 v0.5（線上連結＋五分鐘試玩腳本）

### Phase 3.11: POC v4（2026-07-03 下午、產品目錄＋身份＋留言＋關聯）
- [x] Products 產品目錄庫：官網＋報價實務（案型分佈：清冊助手 6 最大宗）＋內部知識彙整 8 項種子、介面/Notion 雙向可調、建約下拉帶建議價
- [x] 身份系統：進站選身份（同事名單）、X-Actor 鏈到所有寫入、聊天代辦標「名字（經助理）」— 本人與代辦在留痕分流、多人接力各自身份
- [x] Comments 評論庫＋詳情面板留言區、同步 Notion 頁原生留言（整合未開留言能力、容錯待 Nelsen 勾選）
- [x] migrate_v2：四條真關聯（款項/事件/評論→合約、合約→產品）＋既有 27 筆回填
- [x] 驗證：身份分流實測（Nelsen Chen vs Philis Chen（經助理））、MCP 驗收修 C6 守門假設後 PASS、線上部署全綠、Notion 提案 v0.6

### Phase 3.12: POC v5（2026-07-03 傍晚、訪談前收尾）
- [x] 新權杖接手（含留言能力、poc/.env、與 NelsenClaw 整合並存 — 舊權杖仍有效、NelsenClaw 不受影響）
- [x] 同事名單正源 = 艦員名冊（45 位在職）；線上留言同步 Notion 驗證 True
- [x] SLA 卡關實裝（狀態進入日欄＋徽章＋超時紅標＋統計）、續約窗口提示、逾期自動標 P4、已結束收納
- [x] 文件整理（README／SPEC 資料模型 v2／poc README）、全部推上 GitHub（204071a）

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
