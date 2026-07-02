# CLAUDE.md — BizPeak Flow

FUNRAISE 內部合約生命週期系統（主機 + 卡帶架構）。動這個 repo 前先讀 `CONSTITUTION.md`（不可退讓原則）。

## 專案語境
- 這是 **FUNRAISE 公司資產**：git 身份必須是 `nelsen.chen@funraise.com.tw`（`~/work/` includeIf 自動生效、動手前 `git config user.email` 驗證）
- 遠端：`FunRaise-Team/bizpeak-flow`（private；轉 public 前必先清洗 docs/research/ 的真實客戶名與應收款資訊）
- 提案頁線上版：https://bizpeak-flow-proposal.vercel.app （個人 Vercel 帳號、搬公司帳號待 Nelsen 登入）
- 視覺紀律：對外 HTML 過 `feedback_de_ai_design_taste.md` 黑白名單（禁有色邊條 / 卡片浮起 / 漸層）
- 資料層原則：**所有業務資料回 Notion**、系統本身不做第二真相來源（詳 CONSTITUTION）
- Notion 讀寫全走 NelsenClaw integration token 直打 API（`~/NelsenClaw/.env` 的 `NOTION_API_KEY`）、不用 MCP

## Cross-Session Planning
- **Task plan**: `docs/plans/task_plan.md`
- **Findings**: `docs/plans/findings.md`
- Resume: 讀 task_plan.md → 找 **CURRENT** → 接續

## 文件優先序（寫 code 前）
1. `CONSTITUTION.md` — 憲法、引用不重新協商
2. `docs/SPEC.md` — 產品規格
3. `docs/ARCHITECTURE.md` — 技術架構拍板
4. `docs/CARTRIDGE-SPEC.md` — 任何新功能模組（卡帶）必須符合此規範

## 利害關係人速查
Nelsen Chen（發起、COO）/ Philis Chen（流程定義）/ Allen Hung（主導搭建）/ Jaric Kuo（技術）/ Carol（訪談協調）/ Ting・Glendy（行政財務使用者、訪談對象）
