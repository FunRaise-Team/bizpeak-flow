# Notion-as-Backend + MCP + Generative UI — 架構研究（2026-07）

> 目的：為 BizPeak Flow 判斷「Notion 當系統資料層」的能力邊界、MCP 包裝架構模式、以及 Gamma 式邊聊邊生成 UI 的可參考實作。純架構研究，不含程式碼原型。

---

## 1. Notion-as-Backend 能力邊界（2026 現況）

### 1.1 API Rate Limit

- 官方不公開精確數字，但社群與生態系整理一致：**平均 3 requests/sec per integration（per connection）**，允許短暫 burst，另有 **workspace 級別的共享上限**（隨方案等級調整）。
- 換算：約 180 req/min、粗估 2,700 req/15min。
- Payload 限制：單一 request **最多 1,000 個 block elements**、**body 上限 500KB**。
- 來源：[Notion Request limits](https://developers.notion.com/reference/request-limits)、[Notion API Rate Limits Explained 2026](https://www.unbanai.org/blog/notion-api-rate-limits-explained-2026)、[Notion API Rate Limits Are Breaking Your Automation](https://dev.to/kanta13jp1/notion-api-rate-limits-are-breaking-your-automation-heres-the-real-fix-o5p)

**對 BizPeak Flow 的意義**：3 req/s 是「輕量協作工具」的量級，不是「多租戶 SaaS 後端」量級。任何需要高併發寫入（例如多個使用者同時觸發 workflow 更新同一批 row）都需要在應用層排隊 / 批次化，不能假設 Notion 能吸收突發流量。

### 1.2 Database 規模上限

- 免費版與付費版皆有 row 數上限；**付費版可到 20,000 rows / database**（多個 database 不設總數上限，但單庫有硬頂）。
- 效能實務上遠早於硬頂就會惡化：**5,000+ rows 起就常見瀏覽器端 DOM/計算開銷問題**（relations / rollups / formulas 對「當前 view」全量計算）。
- 兩向關聯（two-way relation）有 **10,000 次引用**上限；單一 page 被關聯的項目數建議上限 **約 1,000**，超過會有明顯效能衰退，尤其疊加 Formula / Rollup / Calculate 時。
- 來源：[Notion Database Limits & Workarounds](https://dev.to/kanta13jp1/notion-database-limits-workarounds-7-walls-every-power-user-hits-5n0)、[Optimize database load times](https://www.notion.com/help/optimize-database-load-times-and-performance)、[Notion as a SaaS Backend: Pros and Cons](https://www.superfa.st/blog/notion-as-a-saas-backend)

**對 BizPeak Flow 的意義**：Notion 適合當「配置層 / 知識層 / 輕量記錄層」，**不適合當高頻交易記錄或大量時序資料的主資料庫**。若 BizPeak Flow 預期單一 workspace 資料量會超過幾千筆且需要複雜 relation 查詢，需要規劃「Notion 為 source of truth 的淺層資料 + 外部 DB 為運算/歷史層」的混合架構，而非純 Notion-as-backend。

### 1.3 權限模型

- 權限最小顆粒是「page-level access rules」，可基於 Person 屬性（如 Assignee / Owner）做**列級（row-level）存取控制**，但**僅 Business / Enterprise 方案支援**。
- 2026-03 新增「Can Create Pages」toggle：讓 No Access / Can View / Can Comment 身份也能被授權「只能新增、不能看其他列」，適合表單式資料收集情境。
- API 整合本身不是「拿到 token 就有權限」——**每個 database / page 必須顯式與 integration 分享**，且應採最小權限原則。
- 來源：[Notion Granular Database Permissions](https://thomasjfrank.com/notion-granular-database-permissions-guide/)、[Notion Authorization docs](https://developers.notion.com/docs/authorization)

**對 BizPeak Flow 的意義**：多租戶情境下，「租戶 A 看不到租戶 B 的資料」這件事在 Notion 原生做得到，但要 Business/Enterprise 方案 + 手動設定 page-level rules，**不是 API 層可以動態、細顆粒地程式化管理的權限系統**（不像 Postgres RLS 那樣宣告式）。若 BizPeak Flow 需要動態租戶隔離，建議在應用層（MCP server 或 API gateway）做二次授權檢查，不要把 Notion 權限當唯一防線。

### 1.4 Webhook / Automation 觸發能力

- 2026-03-01 API 版本起，**REST API webhook 系統進入 public beta**：page / database property 變更時，Notion 主動 POST 到指定 endpoint。
- 另有「Automation webhook」路線：no-code 使用者可在 button / database automation 裡設定「Send webhook」動作，觸發外部 HTTP POST。
- **已知限制**：webhook 目前只對 **page property 變更**觸發，**不涵蓋 block 內容層編輯**（例如新增段落、勾選 to-do）——這類仍需輪詢（polling）補完整同步。
- 來源：[Notion Webhooks docs](https://developers.notion.com/reference/webhooks)、[Notion API Webhooks Support in 2026](https://fazm.ai/blog/notion-api-webhooks-support-2026)、[Guide to Notion Webhooks](https://hookdeck.com/webhooks/platforms/guide-to-notion-webhooks-features-and-best-practices)

**對 BizPeak Flow 的意義**：可以用 webhook 做「屬性變更觸發 workflow」（例如狀態欄位從「待審」變「已核准」時觸發下一步），但**不能單靠 webhook 保證內容完整同步**，需搭配定期輪詢或在寫入時由應用層主動雙寫事件，避免依賴 webhook 做強一致性的觸發器。

### 1.5 查詢效能

- 沒有真正的查詢引擎（無 join 最佳化、無索引可調），複雜 filter + relation + rollup 疊加時效能明顯下降；官方本身在 help doc 承認「大型資料庫需要優化技巧」。
- 來源同 1.2。

**架構結論（給 BizPeak Flow）**：**Notion 適合當「人類可讀、可協作編輯的配置 / 知識 / 半結構化記錄層」**，不適合當「高併發、大資料量、複雜查詢的系統資料庫」。合理定位是：Notion 存放 workflow 定義、模板、審核紀錄、知識庫內容；真正的交易 / 事件 / 時序資料應該落在專屬 DB（Postgres / SQLite 等），MCP server 作為兩者之間的協調層。

---

## 2. MCP 包 Notion + 內部工具、支撐「純聊天介面」的架構模式

### 2.1 MCP 核心三元件

MCP server 對外暴露三種原語（來源：[MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)、[MCP 2026 Complete Guide](https://dev.to/x4nent/complete-guide-to-mcp-model-context-protocol-in-2026-architecture-implementation-and-4a11)）：

| 原語 | 用途 | BizPeak Flow 對應 |
|------|------|------|
| **Tools** | LLM 可呼叫的函式（有副作用，如寫入、查詢、觸發） | 「建立 workflow」「更新任務狀態」「查詢客戶資料」 |
| **Resources** | LLM 可讀的資料來源（唯讀、有 URI） | Notion database 匯出的唯讀 view、文件、模板 |
| **Prompts** | 預先定義的工作流程範本 | 「產生週報」「建案盤點」這類固定流程的 prompt 模板 |

**設計慣例**：
- 每個 MCP server 應該**只做一件事**（single responsibility）——例如「Notion server」只管 Notion 讀寫，「內部工具 server」單獨部署，不要把所有內部系統塞進一個 monolith MCP server。這對應 Notion 官方自己的架構選擇（見下）。
- Tool input 一律用嚴格 schema 驗證（Zod / Pydantic），**不可信任 LLM 產出的參數**——hallucinated 參數名是真實故障模式。
- **大資料集用「查詢工具」而非「原始 resource」**：例如不要把整個 Notion database dump 成一個 resource 丟給 LLM，而是提供 `query_database(filter, limit)` 這種 tool，讓 LLM 主動要多少拿多少，避免 context 爆炸（這點直接對應第 1.2 節的規模限制——用 tool 包一層等於在應用層做分頁 / 過濾，繞開「整庫載入」的效能問題）。
- 來源：[MCP Resources concept](https://modelcontextprotocol.info/docs/concepts/resources/)

### 2.2 官方 Notion MCP Server 的實際架構（可直接參考的範例）

- Hosting：Cloudflare Workers（全球分散、serverless 彈性擴展）
- State：Cloudflare Durable Objects + KV store（管理 session / token 這類需要狀態的操作）
- Server framework：Hono（輕量 HTTP framework）
- Auth：**Embedded 架構**——Notion 同時扮演 Resource Server 與 Authorization Server
- 生成 pipeline：內部先把 OpenAPI schema 轉 Zod，再接進 hosted MCP server 的 tool 定義（等於「API 規格自動生成 MCP tool」，避免手寫 tool 定義漂移）
- 來源：[Notion's hosted MCP server: an inside look](https://www.notion.com/blog/notions-hosted-mcp-server-an-inside-look)

**對 BizPeak Flow 的啟示**：如果要包一個內部「BizPeak MCP server」，可仿照這個模式——用既有內部 API 的 OpenAPI/schema 定義自動生成 tool schema，避免手動維護兩份定義漂移；用 serverless + durable state 分離「無狀態的請求處理」與「有狀態的 session/token」。

### 2.3 2026 傳輸層與協定更新（影響部署決策）

- **Streamable HTTP** 取代舊的 HTTP+SSE，且新增 `Mcp-Method` / `Mcp-Name` header，讓 gateway / load balancer / rate limiter 可以不解析 body 就依 operation 路由——這對「多租戶、需要 API gateway 做限流」的架構直接相關。
- **Elicitation**：server 可在執行中要求使用者補充結構化輸入（accept / decline / cancel），適合「聊天中途需要澄清」的場景。
- **Sampling**：server 可以請求 client 端做一次 LLM 補全，讓「巢狀 agent 呼叫」成為可能，但**設計上是 human-in-the-loop**——client 掌控模型選擇與可否決。
- **Tool annotations**：工具可標示 read-only / destructive，讓 client 端做更安全的執行前確認（例如「這是刪除操作，需要二次確認」）。
- 來源：[2026-07-28 MCP Spec Release Candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)、[What changed in 2026-07 MCP spec](https://stacktr.ee/blog/mcp-2026-spec-changes)

**對 BizPeak Flow 的意義**：若要做「純聊天介面」，`elicitation` 這個原語直接對應「AI 問一句確認再繼續」的體驗、`tool annotations` 的 destructive 標記可以直接掛勾 UI 上的二次確認彈窗——這是把「聊天體驗的安全機制」內建進協定層、不用自己在應用層重造。

### 2.4 讓「純聊天介面」成立的整體架構模式

一個典型可行的分層（綜合以上資料歸納）：

```
使用者（聊天介面 / 前端）
   ↕ (AG-UI 或類似協議：把 agent 狀態、UI 更新推到前端)
Agent / Orchestrator（LLM + 對話狀態管理）
   ↕ (MCP：tools / resources / prompts)
MCP Server 們（各自單一職責）
   ├─ Notion MCP server（讀寫 workflow 定義、知識庫、審核紀錄）
   ├─ 內部工具 MCP server（查詢/寫入 BizPeak 自家系統）
   └─ 其他第三方 MCP server（行事曆、通知等）
   ↕
底層資料源（Notion API / 內部 DB / 第三方 API）
```

關鍵原則：**聊天介面本身不直接呼叫 Notion API**，一律經過 MCP server 這層做 schema 驗證、權限檢查、rate limit 緩衝（例如在 MCP server 內部做 request queue，吸收 Notion 的 3 req/s 限制，避免直接把限制暴露給使用者體驗）。

---

## 3. Gamma 式「邊聊邊生成 UI」的業界實作模式

### 3.1 Gamma 本身的架構特徵

- **先產大綱、後產視覺**：使用者輸入主題 → Gamma 先生成**可編輯大綱** → 使用者確認/調整結構 → 才生成完整視覺內容。這個「先結構後視覺」的順序被視為關鍵設計決策，避免使用者在生成大量視覺後才發現論述結構不對。
- **多模型並行**：文字生成、圖片選擇、排版決策、視覺一致性由不同模型分別負責，而非單一模型端到端生成。
- **Gamma Agent（3.0 起）**：生成後有獨立的聊天面板，讓使用者用自然語言對整份或單張內容做二次編輯（restyle / rewrite / 調語氣），這是「生成」與「編輯」分成兩個介面層。
- **卡片式資料模型**：底層把內容拆成「card」這種模組化區塊，本質上跟 slide/web section 通用，方便前端渲染引擎統一處理。
- **平台整合**：透過 connector 模式讓 ChatGPT 等外部聊天介面「委派」生成任務給 Gamma、回傳一個連結，而不是把生成邏輯塞進宿主聊天視窗本身。
- 來源：[What Is Gamma](https://gamma.app/explore/content/guides/what-is-gamma-and-how-does-it-use-ai-to-build-presentations)、[Gamma AI Explained 2026](https://www.sketchbubble.com/blog/gamma-explained-a-comprehensive-deep-dive-into-the-ai-powered-presentation-platform/)

### 3.2 業界可參考的通用生成式 UI 框架

| 框架 | 核心思路 | 特徵 |
|------|----------|------|
| **Vercel AI SDK** | Model-provider 抽象層 + `useChat`/`useCompletion` hook，處理 streaming 生命週期 | 最主流（20M+ 月下載）、著重「串流文字/物件」而非直接生 UI 元件本身 |
| **CopilotKit** | Client-side React 元件庫，讓聊天 agent 能讀寫「宿主應用既有的 state」 | 不是 server 端 stream 元件，而是把聊天 sidebar 嵌進既有 app、讓 agent 操作既有 UI 狀態；主導 **AG-UI Protocol**（已被 Google/LangChain/AWS/Microsoft 等採用作 agent-frontend 通訊標準） |
| **Thesys C1** | **LLM API 直接輸出 UI**（OpenAI API 格式相容，換 endpoint 即可） | 與 AG-UI/CopilotKit 是互補而非取代關係：C1 負責「文字→UI 元件」這一段，AG-UI/MCP 負責「agent↔前端」「agent↔工具」的協議層 |

- 來源：[CopilotKit Generative UI Guide 2026](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026)、[Thesys C1 announcement](https://www.businesswire.com/news/home/20250418761213/en/Thesys-Introduces-C1-to-Launch-the-Era-of-Generative-UI)、[Agentic UI: Frameworks, GenUI Protocols](https://www.thesys.dev/blogs/agentic-ui)、[CopilotKit vs Vercel AI SDK vs Thesys](https://www.generativeui.ru/en/learn/copilotkit-vs-vercel-ai-sdk-vs-thesys)

**分層心智模型（業界共識）**：
1. **MCP**：agent 呼叫工具、讀資料（後端能力層）
2. **AG-UI / 類似協議**：agent 狀態變化推播到前端（前端同步層）
3. **A2UI / C1 這類**：把 LLM 輸出直接轉成 UI schema/元件（UI 生成層）

這三層可以組合使用，也可以各自單獨採用一部分。

**對 BizPeak Flow 的意義**：若目標是「聊天中逐步生成表單/看板/報表」這種體驗，不需要重造 Gamma 的多模型架構，合理路線是：
- 用 **Vercel AI SDK** 或 **CopilotKit** 處理串流與前端狀態同步（成熟度高、生態系大）；
- 若要讓 LLM 直接輸出可渲染的 UI schema（而非純文字），評估 **Thesys C1** 這類「文字轉 UI」層，或退而求其次用結構化 JSON + 前端自訂 renderer（技術風險較低、但需要自己維護 schema-to-component 的映射）；
- **先大綱後視覺**這個 Gamma 模式值得直接借用：任何「一次生成整頁」的功能，都先讓 LLM 產出結構化大綱給使用者確認，再生成細節，降低返工成本。

---

## 4. 對 BizPeak Flow 架構決策的直接影響（摘要判準）

1. **Notion 定位**：只適合當配置/知識/審核紀錄層，量級超過幾千 row 或需要複雜查詢即應轉存專屬 DB。
2. **併發假設**：3 req/s per integration 是硬約束，MCP server 必須內建 request queue/緩衝，不可讓前端直接觸發高頻 Notion 呼叫。
3. **多租戶隔離**：Notion 原生 row-level 權限需 Business/Enterprise 方案且是手動規則，不可當唯一租戶隔離機制，需在 MCP/應用層加一層授權檢查。
4. **即時性**：webhook 只覆蓋 property 變更、不含 block 內容，強一致性同步需搭配輪詢，不能只依賴 webhook 做觸發器。
5. **MCP server 拆分**：Notion 與內部工具應拆成獨立 MCP server（單一職責），並用 schema 自動生成 tool 定義降低維護成本。
6. **聊天介面生成 UI**：可分層採用 MCP（工具層）+ AG-UI/CopilotKit（前端同步層）+ 可選的 C1 式 UI 生成層；「先大綱後細節」的兩階段生成值得直接沿用。
