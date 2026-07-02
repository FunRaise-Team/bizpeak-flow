# BizPeak Flow POC — 能力層 × Notion 資料層 × MCP

> 這個 POC 驗證提案的核心主張：**能力先於介面**（憲法第二條）。這裡的六個工具、就是未來 1.0 介面按鈕與 1.5 聊天框背後的同一批能力 — 先讓體驗 2.0（在你慣用的 AI 助理裡問合約）今天就能動。
> 正式版技術棧由 RD 定案（見 `docs/ARCHITECTURE.md`）、本 POC 用 Python 求快、驗證概念用。

## 檔案

| 檔案 | 角色 |
|------|------|
| `states.py` | 狀態機單一定義檔（C0-C7 / X1-X2、合法轉移、SLA）— 卡帶 #1 的第一個真實工件 |
| `notion_layer.py` | Notion 資料層薄封裝（憲法第一條：唯一真相來源） |
| `setup_notion.py` | 建 POC 資料層：四庫（合約 / 款項 / 事件 / 卡帶註冊）＋示意資料（全虛構） |
| `server.py` | MCP 伺服器 — 六個能力工具 |
| `test_client.py` | 驗收測試（真連線、真呼叫） |

## 快速開始

```bash
# 1. 建資料層（冪等、已建過會中止）
uv run setup_notion.py

# 2. 驗收測試
uv run test_client.py     # 期望輸出最後一行：驗收: PASS

# 3. 掛進 Claude Code（之後任何對話都能問合約）
claude mcp add bizpeak --scope user -- uv run --project /Users/nelsen/work/bizpeak-flow/poc server.py
```

token 讀自 `~/NelsenClaw/.env` 的 `NOTION_API_KEY`（或環境變數）、不進版控。

## 六個能力工具

| 工具 | 做什麼 | 對應提案 |
|------|--------|----------|
| `contract_list` | 列合約（可依狀態篩） | 個人入口「我的合約」 |
| `contract_get` | 單張詳情＋款項排程 | 合約詳情頁 |
| `contract_transition` | 狀態轉移（狀態機驗證、退回必附理由、事件留痕） | 生命週期引擎 |
| `payment_overdue_list` | 逾期款項清單 | 逾期看板、催收梯級 |
| `payment_mark_paid` | 收款打勾（人審動作、留痕） | 財務入口一鍵確認 |
| `cashflow_forecast` | 未收款按月彙總 | 管理層入口現金流量預測 |

## 演示話術（掛載後在 Claude 直接說）

- 「我有哪些款項逾期？」→ `payment_overdue_list`
- 「CT-2026-041 現在狀態怎樣、還有幾期沒收？」→ `contract_get`
- 「祥豐那張用印完成了、幫我推進狀態」→ `contract_transition`（非法轉移會被狀態機擋下）
- 「未來三個月會收到多少錢？」→ `cashflow_forecast`

## POC 邊界（刻意不做）

- 無快取層（正式版擋每秒 3 請求限流用）、無簽核引擎、無通知、無代理自動化 — 這些照路線圖進：下週 1.0、7 月代理、8 月 MCP 化完整版
- 示意資料全虛構；正式 schema 於本週訪談後定稿
