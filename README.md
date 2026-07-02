# BizPeak Flow

> FUNRAISE 內部合約生命週期系統（REW）— 從報價單產生到收款追蹤的完整閉環、電子簽核 + 合約管理 + 催收自動化。
> 同時是「BizPeak 生態系事業群」的第一個 Dogfooding 產品：內部打磨 → 對外兜售（不動產與 B2B 傳統企業）。

**發起人**: Nelsen Chen（COO）
**立項依據**: 2026-07-02 會議決策 — 正式立項、不納入 AI Raiser 計畫分散打造
**團隊**: Nelsen Chen（發起）/ Philis Chen（流程）/ Allen Hung（主導搭建）/ Jaric Kuo（技術）/ Carol（訪談協調）+ 兩位 RD（待拉入）

---

## 核心理念：遊戲主機 + 卡帶

這個專案不只是做一個合約系統、而是建立公司內部工作流的「主幹道」：

1. **主機（Platform）**：資料層（Notion）+ 流程引擎 + 通知系統 + 入口框架 — 一次建好、長期不變
2. **第一個卡帶（Cartridge #1）**：合約生命週期模組（報價 → 簽核 → 回簽 → 開票 → 收款 → 催收 → 續約）
3. **卡帶規範**：AI 先鋒計畫的 Vibe Coder 照 `docs/CARTRIDGE-SPEC.md` 開發、即插即用長出新功能

## 三階段體驗

| 階段 | 介面 | 說明 |
|------|------|------|
| 1.0 | 傳統 GUI | 互動型產品、後端 Notion Database、接現有自動報價單系統 |
| 1.5 | GUI × Agent 混合 | 類 Gamma、邊聊邊操作、產品掛載 Agent |
| 2.0 | 純聊天 MCP | FunRaise MCP、任何入口（如 Clockwork）都能問合約 |

## 文件地圖

| 文件 | 內容 |
|------|------|
| [CONSTITUTION.md](CONSTITUTION.md) | 專案憲法 — 不可退讓原則（修憲需 Nelsen 拍板） |
| [docs/SPEC.md](docs/SPEC.md) | 產品規格 — 流程、資料模型、三入口、通知矩陣 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 技術架構 — 選型 trade-off 與拍板 |
| [docs/CARTRIDGE-SPEC.md](docs/CARTRIDGE-SPEC.md) | 卡帶規範 — 先鋒計畫接入標準 |
| [docs/plans/task_plan.md](docs/plans/task_plan.md) | 跨階段任務計畫（接手先讀這個） |
| [docs/research/](docs/research/) | 立項研究（repo / Allen 工具 / CLM 地景 / Notion 邊界 / 內部脈絡） |
| [proposal/index.html](proposal/index.html) | 一頁式互動提案（給利害關係人看的版本） |

## 相關連結

- Notion 專案頁：https://www.notion.so/c97d47abdd164fc7a26bd0e206132705
- 立項會議記錄：https://www.notion.so/391b219245158075a72dc361a13033d6
- 業務儀表板（掛接點）：https://github.com/FunRaise-Team/AI-raiser-planning
- Allen 的廠商生命週期工具（參考）：https://contract-flow-umber.vercel.app/
