# BizPeak Flow — 技術架構 v0.1（eng-review 紀律：三選項、各列炸點、拍板一個）

> 依據研究：`docs/research/ai-raiser-planning-repo.md`（既有模式）+ `notion-backend-mcp.md`（Notion 邊界）+ `contract-flow-allen.md`（狀態機底稿）。

---

## 1. 架構選項比較

### 選項 A — 併入 AI-raiser-planning（儀表板 monorepo 加 contracts 模組）

掛接點研究已確認可行：Supabase 加 `contracts` 表（`notion_id` 外鍵接 `customer_cache`）+ `/api/contracts` 路由（走同一 `proxy.ts` JWT gate）+ 客戶詳情側欄加合約區塊。

**炸點**：
1. **受眾錯位** — 儀表板是業務漏斗工具、BizPeak Flow 橫跨業務＋行政＋財務；儀表板現行的部門級權限模型撐不住財務資料的敏感度、改權限會動到既有使用者
2. **主幹道被綁架** — 卡帶平台的發布節奏會跟儀表板的發布節奏互相拖累；一邊出事兩邊停擺
3. **對外產品化死路** — 未來 BizPeak 要對外賣、從別人的 monorepo 裡拆出來的成本遠高於一開始獨立

### 選項 B — 獨立平台應用（沿用已驗證模式、與儀表板互鏈）

獨立 repo `bizpeak-flow`、技術棧複製儀表板已驗證組合：**Next.js + Supabase（唯讀快取 + 交易佇列）+ Vercel（cron）+ Notion 權威源**。與儀表板透過連結卡互跳（儀表板現在就是這樣連報價單系統的）。

**炸點**：
1. **雙倉維運成本** — 認證、UI 慣例、部署管線要再建一次；靠「抄儀表板既有解法」壓成本、但仍是第二套要顧的系統
2. **跨系統一致性** — 客戶資料以 Notion 客戶大名單為權威、兩套快取（儀表板 Supabase / 本系統 Supabase）可能短暫不一致；靠「快取只讀、寫全回 Notion」守住
3. **整合面變寬** — 報價單系統（funraise-sales-skills）、NuEIP、sales@ 信箱、Teams 四個外部接口都要自己接、任何一個靜默失敗就重演 Allen 底稿的缺口；解法是憲法級的「失敗必出聲」

### 選項 C — NelsenClaw 式輕平台（Python/FastAPI + Notion 直連、無快取層）

最快能動、Q 最熟的模式；FastAPI + launchd/cron + Notion API 直打。

**炸點**：
1. **限流撞牆** — 無快取層、三入口同時用就頂到 Notion 3 req/s、尖峰直接 429；補快取 = 重做選項 B 的一半
2. **單點依賴** — 跑在誰的機器上？Allen 底稿已點名「本機排程單點」是現役缺口、公司級系統不能再犯
3. **RD 接手斷層** — 公司 RD 生態（Jaric 團隊、儀表板）是 TypeScript/Next.js；Python 平台會讓「拉兩位 RD 同學」的計畫多一道語言牆

## 2. 拍板：獨立平台應用（方向）＋ 技術棧與 RD 定案（v0.3 修正）

**方向鎖定**：獨立平台應用、與儀表板互鏈 — 主幹道要長期承載卡帶與對外產品化、必須獨立。**選定後不中途換、除非出現推翻性證據。**

**技術棧修正（2026-07-02 Nelsen）**：不照單全收既有工具的選型（Supabase 非公司 RD 慣用棧）。兩條路、開發前與 RD（Jaric 團隊）定案：

| 路徑 | 組合 | 取捨 |
|------|------|------|
| **A・正式產品線** | 公司雲慣例（GCP）：Cloud Run + Cloud SQL / Firestore + Cloud Scheduler + Pub/Sub | 對齊 RD 維運能力、直接是商轉多租戶地基；起步比 B 慢數天 |
| **B・快速原型** | Vercel + 輕量託管資料庫 | 一週內上線 dogfooding；商轉前需一次遷移 |

**建議**：時程要求下週上線 → B 先行驗證流程、8 月 MCP 化時評估遷 A；RD 若評估可直上 A 更好。能力層與資料層之間走 repository 介面隔離、切換成本已在架構內控制。

## 3. 系統分層（主機的解剖圖）

```
┌─ 介面層（皮）────────────────────────────────────────┐
│  1.0 三入口 GUI（Next.js）                            │
│  1.5 Agent 面板（Gamma 兩階段：草稿 → 人確認 → 執行）    │
│  2.0 FunRaise MCP server（tool = 能力層 1:1 映射）      │
├─ 能力層（骨、卡帶接入面）────────────────────────────┤
│  contract.create / contract.transition / payment.mark │
│  payment.overdue.list / cashflow.forecast / ...        │
│  （每個能力：TypeScript 函式 + REST 路由 + MCP tool）    │
├─ 平台服務（主機硬體）────────────────────────────────┤
│  狀態機引擎（單一定義檔、單向前進、退回留痕、樂觀鎖）      │
│  簽核引擎（自建：簽核鏈路由、代理人、行動端批准、留痕）     │
│  事件匯流排（cartridge 訂閱 / 發布）                    │
│  通知服務（Teams / Email、可操作卡片、失敗必出聲）        │
│  規則引擎（催收梯級、SLA 檢查、續約窗口）                │
│  代理執行環境（回簽識別 / 對帳 / 催收起草 — 建議經人審）    │
│  排程器（Vercel cron、比照儀表板每 10 分模式）           │
│  信任邊界（AI 只建議、trusted bridge 寫入 — Allen 底稿）  │
├─ 資料層（憲法第一條）────────────────────────────────┤
│  Notion＝權威源（Contracts / Payments / Events / …）    │
│  Supabase＝唯讀快取 + request queue（擋 3 req/s 限流）   │
│  Notion webhook（beta、僅 property 變更）+ 輪詢補漏      │
└──────────────────────────────────────────────────────┘
```

## 4. 外部整合面（四個接口、逐一有備援）

| 接口 | 整合方式 | 失敗行為 |
|------|----------|----------|
| 報價單系統（funraise-sales-skills） | 讀輸出格式、C0 建檔時帶入（格式見該 repo `skills/quotation/`、規格細化時對齊） | 手動建檔 fallback |
| NuEIP（可選 adapter） | 簽核引擎自建為主；個別流程若政策要求回接 NuEIP、走 adapter（範圍訪談後定） | 狀態手動更新、留痕不減 |
| sales@ 回簽信箱 | 信箱輪詢 / 轉發 webhook → 回簽落檔 + 通知財務 | 每日對帳檢查、漏抓必告警 |
| Teams 通知 | incoming webhook | 失敗轉 Email、再失敗進系統告警版 |

## 5. 對外產品化的架構預留（不是現在做、是現在不擋死）

- 能力層與資料層之間走 repository 介面 — 內部版實作 = Notion adapter；未來對外多租戶版換 Postgres 主存、Notion 變成客戶可選的同步目標
- 卡帶 manifest 與能力註冊從第一天就是資料（Cartridges DB）、不是硬編碼 — 對外賣的時候「模組市場」的雛形已在

## 6. 安全（憲法第七條落地)

- Vercel 部署 + 公司 IP 閘 / SSO（比照 `~/Brain/templates/vercel-ip-gate/`）
- 財務動作（收款打勾、催收升級）需財務角色、行級權限在應用層做（Notion 權限顆粒度不足、研究已確認）
- 稽核軌跡不可刪改
