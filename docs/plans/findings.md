# BizPeak Flow — Findings

---

## What We Learned

### Notion 會議記錄（來源：Notion 頁 391b2192-4515-8075-a72d-c361a13033d6、2026-07-02 抓取）

**會議目標**：檢視合約簽核流程缺乏追蹤機制、將合約管理系統正式立項（BizPeak workflow）、同步 AI Raiser 第二屆節奏。

**痛點實例**：台北某客戶發票已寄出、款項未收、直到月底結帳才被發現、過程無人追蹤。

**已定決策**：
1. 合約管理系統以**正式立項**推動、不納入 Raiser 計畫分散打造
2. 三階段使用者體驗：1.0 圖形介面（Notion Database）→ 1.5 類 Gamma 邊聊邊操作 → 2.0 純聊天介面
3. 推進流程：**訪談（行政、財務）→ 開規格 → 打造 → 驗證 → 通過**

**分工（會議記錄版）**：Nelsen Chen（發起）、Philis Chen、Allen Hung（主導搭建）、Jaric Kuo（技術）、Carol（訪談協調）。訪談對象：Ting、Glendy、Carol 等日常流程使用者。

**入口設計**：個人入口 / 行政入口 / Funraise 入口 — 可查合約所在週期與追蹤狀態。

**開放問題（會議記錄原文）**：
- 正式 Decision Owner 與資源配置尚待明確指定
- 開發所需 Token 用量與資源仍待 Nelsen 與 Jaric 確認
- 訪談對象具體時程尚未排定

**風險**：各單位點狀 AI 工具資料格式不一致、整合難度需在規格階段評估；立項延遲 = 款項遺漏持續發生。

**本輪排除範圍**：詳細規格與介面設計細節（待訪談後）；對外銷售商業模式細節。

### Philis 的九步流程（來源：Teams、Nelsen 轉述）
1. 業務跟客戶確認合作（信件為基準）
2. 填寫報價單
3. 報價單上系統電子簽核用印（到事業群最高主管）
4. 發信將報價單寄給客戶
5. 客戶回簽報價單（寄到統一 mail 如 sales@funraise.com.tw）→ 預計付款日 + 金額列表（現金流量管控）
6. 指定 email 收到回簽後、自動發信通知財務
7. 財務開發票、告知客戶付款期限 + 匯款帳號
8. 財務收到匯款 → 後台打勾確認
9. 未如期付款 → 發催收信給業務 → 同步進逾期款項金額表

### 環境驗證（2026-07-02）
- **git 身份**：`~/work/bizpeak-flow` 的 `git config user.email` = `nelsen.chen@funraise.com.tw` ✅（includeIf 生效）
- **GitHub 憑證**：`gh` active 帳號是個人 Nelsen0717、但 per-URL credential helper 對 `FunRaise-Team/*` 回 `Nelsen-funraise` → git clone 可用、`gh api` 不可用（404）
- **Notion**：NOTION_API_KEY（NelsenClaw/.env）可讀提案頁 c97d47abdd164fc7a26bd0e206132705；會議記錄 ID 是 page 不是 database
- **AI-raiser-planning repo 頂層**：CLAUDE.md / README.md / ai-sharing / 新版_BSC-Dashboard / 舊版_PickPeak-Dashboard

---

## What We Tried That Didn't Work

| Approach | Why It Failed | Date |
|----------|---------------|------|
| `gh api repos/FunRaise-Team/...` | active 帳號是個人、404；改走 git credential 路由 | 2026-07-02 |
| Bash 直接 curl Notion API | context-mode hook 攔截重導；改 ctx_execute 沙箱 / python 腳本 | 2026-07-02 |

---

## External References
- Notion 提案頁（交付目標）：https://www.notion.so/c97d47abdd164fc7a26bd0e206132705
- Notion 會議記錄：https://www.notion.so/391b219245158075a72dc361a13033d6
- Allen 的工具：https://contract-flow-umber.vercel.app/
- 業務儀表板 repo：https://github.com/FunRaise-Team/AI-raiser-planning（本地 ~/work/AI-raiser-planning）
- 研究工作流：wf_3e35494e-76a（5 路、產出在 docs/research/）
