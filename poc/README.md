# BizPeak Flow POC — 1.0 介面 × 1.5 聊天框 × 2.0 MCP

> 驗證提案的核心主張：**能力先於介面**（憲法第二條）。三個入口 — 網頁介面、介面內聊天框、外部 AI 助理（MCP）— 吃同一份 `capabilities.py`、同一個 Notion 資料層。
> 正式版技術棧由 RD 定案（`docs/ARCHITECTURE.md`）；本 POC 用 Python 求快、驗證概念與體驗用。

## 快速開始

```bash
# 0. 前置：~/NelsenClaw/.env 或環境變數需有 NOTION_API_KEY、GEMINI_API_KEY

# 1. 建資料層（冪等、已建過會中止）
uv run setup_notion.py

# 2. 網頁應用（體驗 1.0 + 1.5）→ 開 http://127.0.0.1:8790
uv run uvicorn app:app --port 8790

# 3. MCP 驗收測試（體驗 2.0）
uv run test_client.py        # 期望最後一行：驗收: PASS

# 4. 掛進 Claude Code（之後任何對話都能問合約）
claude mcp add bizpeak --scope user -- uv run --project /Users/nelsen/work/bizpeak-flow/poc server.py
```

## 三種體驗、同一能力層

| 體驗 | 入口 | 試試看 |
|------|------|--------|
| **1.0 圖形介面** | `app.py` + `web/index.html`（四頁籤：總覽 / 收款 / 逾期 / 事件） | 點合約列展開生命週期軌道；「推進」「確認收款」按鈕真的寫回 Notion 並留痕 |
| **1.5 介面＋聊天框** | 同一頁右下角「助理」 | 說「祥豐那張可以寄給客戶了、幫我推進」— 助理自己查編號、走狀態機、切頁籤並高亮該列；說「把它直接跳到結案」— 會被狀態機擋下並白話解釋 |
| **2.0 AI 助理 × MCP** | `server.py`（六個工具） | 在 Claude 直接問「我有哪些款項逾期」 |

## 檔案

| 檔案 | 角色 |
|------|------|
| `states.py` | 狀態機單一定義檔（C0-C7 / X1-X2、合法轉移、SLA）— 三個入口與未來所有卡帶共用 |
| `capabilities.py` | **能力層** — 六個能力（查詢 × 4、寫入 × 2）、寫入必留痕 |
| `notion_layer.py` | Notion 資料層薄封裝（憲法第一條：唯一真相來源） |
| `app.py` | 網頁應用（1.0 資料與操作 + 1.5 聊天：Gemini 函式呼叫、後端執行、指揮前端導航） |
| `web/index.html` | 前端（原生、零建構鏈） |
| `server.py` | MCP 伺服器（2.0、薄層） |
| `setup_notion.py` / `test_client.py` | 資料層建置 / 驗收測試 |

## 設計要點（給接手的 RD）

- **能力 = 函式 = 網頁動作 = MCP 工具**：加新能力只在 `capabilities.py` 寫一次、三個入口自動可用 — 這就是提案「換皮不換骨」的實作形狀
- **狀態機集中定義**：轉移合法性只在 `states.py` 判一次；退回必附理由、寫入必落事件庫
- **聊天框協定**：後端回 `{reply, actions:[{tab, highlight}], refresh}` — 模型透過 `ui_navigate` 工具指揮前端、前端只負責執行
- **限流**：`app.py` 有 30 秒快取擋 Notion 每秒 3 請求限流（寫入後主動失效）；正式版換獨立快取層
- 金鑰只在後端、不進前端；示意資料全虛構

## 端到端閉環（已驗收）

`uv run test_e2e.py` — 建約 → 推進 → C4 自動產生款項排程 → 未收清擋結案 → 開票 → 收款全清 → C6 結案 → C7 續約 → 一鍵開新約回 C0。18 項檢查全過、每步落 Notion 且事件留痕。

介面另含：現金流頁籤（按月長條）、角色視角切換（業務／財務／管理層 — 各見其職、按鈕權限跟著走）、「＋ 新增合約」表單。

## POC 邊界（刻意不做）

簽核引擎（多人簽核鏈）、通知（Teams）、回簽信箱代理、對帳代理、正式權限（視角切換僅為演示） — 照路線圖進：下週 1.0 正式版、7 月代理、8 月 MCP 化完整版。資料層位置：Notion「Personal Notes」下「BizPeak Flow — 資料層」。
