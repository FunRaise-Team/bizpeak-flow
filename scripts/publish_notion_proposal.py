#!/usr/bin/env python3
"""BizPeak Flow 立項提案 v0.3 → Notion 專案頁（c97d47abdd164fc7a26bd0e206132705）
行為：找到頁面上舊提案起點（H1 含「Flow 立項提案」）、從該塊起全部封存、再發新版。
走 NelsenClaw integration token 直打 API。"""
import json, sys, time, urllib.error, urllib.request
from pathlib import Path

PAGE_ID = "c97d47abdd164fc7a26bd0e206132705"
MARKER = "Flow 立項提案"
VERSION = "BizPeak Flow 立項提案 v0.4"
SITE = "https://bizpeak-flow-proposal.vercel.app"
REPO = "https://github.com/FunRaise-Team/bizpeak-flow"

token = None
for line in (Path.home() / "NelsenClaw" / ".env").read_text().splitlines():
    if line.startswith("NOTION_API_KEY="):
        token = line.split("=", 1)[1].strip()
assert token
H = {"Authorization": f"Bearer {token}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}

def api(method, path, body=None):
    req = urllib.request.Request(f"https://api.notion.com/v1{path}", method=method,
                                 data=json.dumps(body).encode() if body else None, headers=H)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** attempt); continue
            print("HTTP", e.code, e.read().decode()[:300]); raise
    raise RuntimeError("429 重試耗盡")

def all_children(pid):
    out, cursor = [], None
    while True:
        q = f"/blocks/{pid}/children?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        res = api("GET", q)
        out += res["results"]
        if not res.get("has_more"): return out
        cursor = res["next_cursor"]

# ── 1. 刪舊提案（從第一個含 MARKER 的 H1 起、全部封存）──
blocks = all_children(PAGE_ID)
start = None
for i, b in enumerate(blocks):
    t = b["type"]
    txt = "".join(r.get("plain_text", "") for r in b.get(t, {}).get("rich_text", []))
    if t == "heading_1" and MARKER in txt:
        start = i; break
if start is None:
    print("找不到舊提案標記、直接發新版（頁面現有", len(blocks), "塊）")
    to_delete = []
else:
    to_delete = blocks[start:]
    print(f"舊提案從第 {start} 塊起、共 {len(to_delete)} 塊待封存")
for b in to_delete:
    api("DELETE", f"/blocks/{b['id']}")
    time.sleep(0.15)
print(f"封存完成 {len(to_delete)} 塊")

# ── rich text helpers ──
def rt(text, bold=False, color="default", link=None):
    seg = {"type": "text", "text": {"content": text}}
    if link: seg["text"]["link"] = {"url": link}
    ann = {}
    if bold: ann["bold"] = True
    if color != "default": ann["color"] = color
    if ann: seg["annotations"] = ann
    return seg
def h1(t): return {"type": "heading_1", "heading_1": {"rich_text": [rt(t)]}}
def h2(t): return {"type": "heading_2", "heading_2": {"rich_text": [rt(t)]}}
def p(*s): return {"type": "paragraph", "paragraph": {"rich_text": list(s)}}
def bullet(*s): return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": list(s)}}
def numbered(*s): return {"type": "numbered_list_item", "numbered_list_item": {"rich_text": list(s)}}
def callout(segs, icon="💡", color="yellow_background"):
    return {"type": "callout", "callout": {"rich_text": segs, "icon": {"type": "emoji", "emoji": icon}, "color": color}}
def divider(): return {"type": "divider", "divider": {}}
def toggle(title, children):
    return {"type": "toggle", "toggle": {"rich_text": [rt(title)], "children": children}}
def table(header, rows):
    trows = [{"type": "table_row", "table_row": {"cells": [[rt(c, bold=True)] for c in header]}}]
    for row in rows:
        trows.append({"type": "table_row", "table_row": {"cells": [[rt(c)] for c in row]}})
    return {"type": "table", "table": {"table_width": len(header), "has_column_header": True,
                                       "has_row_header": False, "children": trows}}

# ── 2. 提案內容 ──
b1 = [
    h1(VERSION),
    callout([rt("從報價單產生的那一刻、到收款與續約的完整閉環。", bold=True),
             rt("電子簽核、合約管理、催收自動化 — 公司工作流「主幹道」的第一段路、BizPeak 生態系第一個 Dogfooding 產品。")], icon="🎯"),
    p(rt("發起人：Nelsen Chen（COO）｜文件：FR-BPF-2026-001 v0.4｜2026-07-02｜狀態："),
      rt("待拍板", bold=True, color="orange")),
    callout([rt("一頁式互動提案（對外可分享）：", bold=True), rt(SITE, link=SITE),
             rt("　｜　協作程式庫："), rt("FunRaise-Team/bizpeak-flow", link=REPO), rt("（public、含完整規格文件與 POC）")], icon="🔗", color="gray_background"),
    callout([rt("POC 已可動：", bold=True), rt("Notion 資料層四庫已建（", ), rt("POC 頁", link="https://www.notion.so/391b219245158137a95cc1d0f74f97e6"), rt("）、MCP 伺服器六個能力工具驗收通過 — 在 Claude 掛上 repo 的 poc/ 即可直接問「哪些款項逾期」。掛載指令見 poc/README.md。")], icon="🧪", color="green_background"),
    p(rt("敘事主軸：", bold=True), rt("從公司自身痛點出發、先在內部打通合約閉環、驗證後產品化 — 成為 BizPeak 生態系對外的第一個產品。")),
    divider(),

    h1("① 為什麼是現在 — 三個正在流血的缺口"),
    bullet(rt("發票寄了、款沒收、月底才發現：", bold=True), rt("真實案例（台北客戶）、最長 30 天盲區、直接衝擊現金流。")),
    bullet(rt("流程只在人的腦子裡：", bold=True), rt("「簽核」「發票」「催收」在公司知識庫查無任何記錄 — 新人逐案教、離職知識蒸發。")),
    bullet(rt("點狀工具、無法成流：", bold=True), rt("先鋒計畫產出缺乏主流規範、資料格式不一致、串不成完整流程。")),

    h1("② 產品定位 — 主機與卡帶、品牌座標"),
    p(rt("平台像遊戲主機一次建好、功能像卡帶即插即用 — 合約生命週期是卡帶 #1。品牌座標依公司品牌架構頁（Company → Brand → Product、Teams 命名模式）：")),
    table(["層", "名稱", "備註"], [
        ["母品牌", "方睿科技 FUNRAISE", "放大能力、釋放專業"],
        ["事業群", "生態系事業群「釋放專業」", "與不動產事業群（PickPeak）平行"],
        ["子品牌", "BizPeak", "產品命名 = BizPeak + 使用情境"],
        ["產品", "BizPeak Flow（本提案）", "與 BizPeak Call / Chat / Studio（名稱 TBC）平行"],
        ["共用接口", "Funraise MCP", "本產品體驗 2.0 的能力層直接成為它的生態系拼圖"],
    ]),
    p(rt("憲法四條（不可退讓、修憲需拍板）：", bold=True), rt("Notion 唯一真相來源｜能力先於介面｜卡帶合規主幹道不分岔｜關鍵節點必有人。全文見 repo CONSTITUTION.md。")),

    h1("③ 合約生命週期（卡帶 #1）"),
    p(rt("狀態機依現行作業流程盤點設計：單向前進、退回留痕、樂觀鎖、狀態定義集中管理。疊上代理能力：")),
    table(["狀態", "名稱", "負責人", "SLA", "系統自動做的事"], [
        ["C0", "報價草稿", "業務", "—", "接自動報價單系統輸出、自動建檔"],
        ["C1", "內部簽核", "簽核鏈", "3 天", "自建簽核引擎：鏈路由、代理人、Teams 卡片批准、超 SLA 提醒"],
        ["C2", "用印完成", "行政 Ting", "2 天", "完成即通知業務可寄出"],
        ["C3", "待客戶回簽", "業務", "7 天", "超期自動提醒追蹤"],
        ["C4", "回簽生效", "系統＋財務", "即時", "回簽識別代理：判讀進信、抽付款日金額、落檔＋5 分鐘通知財務＋產生款項排程"],
        ["C5", "履約・收款", "財務 Glendy＋業務", "依款期", "對帳代理產生建議打勾清單；逾期觸發催收梯級"],
        ["C6", "結案", "財務", "—", "全款項結清自動歸檔"],
        ["C7", "續約窗口", "業務＋BU 主管", "前 60 天", "60／30 天自動提醒、一鍵開新約回 C0"],
    ]),
    p(rt("催收梯級：", bold=True), rt("D+3 提醒業務 → D+7 代理起草催收信（人審後寄）→ D+30 升級 BU 主管 → D+60–90 強制升級決策（正式催告／停服／委外；逾期 90 天回收率約剩五成）。")),

    h1("④ 三入口 — 同一套資料、各看各的"),
    table(["入口", "使用者", "核心畫面"], [
        ["個人入口", "業務", "我的合約、卡關節點自動浮現、我的催收任務"],
        ["行政・財務入口", "Ting／Glendy", "用印佇列、開票佇列、收款打勾、逾期款項表"],
        ["Funraise 入口", "Nelsen／BU 主管", "現金流量預測、全合約看板、逾期指標"],
    ]),
]
b2 = [
    h1("⑤ Agentic 差異化 — 從「系統追人」到「代理代辦、人只拍板」"),
    p(rt("傳統系統把狀態擺出來、提醒人去做；BizPeak Flow 把事情先做到只剩最後一個決定、人負責拍板。", bold=True),
      rt("每個代理動作守信任邊界：AI 起草建議 → 人審 → 信任橋接寫入。")),
    table(["代理能力", "現況（人工）", "BizPeak Flow（代理）"], [
        ["回簽識別", "有人看到信、轉給財務", "AI 判讀進信屬於哪張合約、抽取付款日金額、自動落檔通知"],
        ["收款對帳", "財務逐筆對、月底結帳", "銀行入帳 → AI 比對排程 → 建議打勾清單、財務一鍵確認"],
        ["催收代辦", "業務想起來才追、信自己寫", "代理起草催收信附完整上下文、業務按一下送出"],
        ["風險預警", "逾期才知道", "依歷史付款行為預測風險、開票前標記高風險客戶"],
        ["主動彙報", "要人去查", "代理在 Teams 主動說話、通知是可操作卡片、不是死訊息"],
    ]),
    p(rt("簽核自立（v0.2 拍板）：", bold=True), rt("自建簽核引擎（簽核鏈路由、代理人機制、Teams 卡片批准、沿途留痕）— 簽核是主幹道核心能力、不外包；NuEIP 降為可選接口、政策要求的流程走 adapter 回接。")),

    h1("⑥ 三階段體驗 — 換皮不換骨"),
    table(["階段", "定義", "驗收判準"], [
        ["1.0 圖形介面", "完整的合約管理系統：合約列表、生命週期追蹤、收款佇列、逾期看板", "一張真實合約 C0 → C6 走完、財務真的用它收款"],
        ["1.5 介面＋聊天框", "在 1.0 既有介面上長出聊天框 — 說一句話、介面自己動：導航、開表單、給連結（類 Gamma / Notion 內建助理）", "聊天框一句話、介面完成導航與草稿、人審後入庫"],
        ["2.0 AI 應用 × MCP", "在使用者慣用的 AI 聊天應用（Claude / GPT 等）、透過 Funraise MCP 把個人信箱檔案與公司合約系統接進同一場對話", "在外部 AI 助理完成跨系統操作（信箱回簽 → 合約歸檔）、不開我們的介面"],
    ]),

    h1("⑦ 轉移與嵌入 — 不搬家、先接管"),
    p(rt("導入原則：", bold=True), rt("信箱、Teams、報價單系統照用 — 系統把追蹤層疊在既有工具之上、只退役補洞用的表格與登記簿（Excel 逾期表 / 現金流表、紙本用印登記簿）；同仁自製小工具走四件套卡帶化。互動版雙態圖見線上提案第 7 節。")),
    table(["工具", "去向", "資料怎麼搬"], [
        ["Outlook 信箱", "照用 — 回簽識別代理自動讀", "回簽自動落合約庫、不用搬"],
        ["Teams", "照用 — 通知與簽核卡片可直接操作", "操作記錄落事件庫"],
        ["報價單系統", "照用 — 輸出直接建 C0", "報價資料自動帶入合約庫"],
        ["NuEIP", "降為可選接口（簽核引擎自建）", "政策要求的流程走接口回寫"],
        ["網銀・會計系統", "照用 — 入帳明細餵對帳代理", "實收結果回寫款項庫"],
        ["Excel 逾期表／現金流表", "退役 — 看板與預測取代", "歷史資料一次性導入款項庫"],
        ["用印登記簿", "退役 — 用印佇列取代", "掃描歸檔事件庫"],
        ["同仁自製小工具", "卡帶化 — 四件套接入（L0 起步）", "資料契約登記卡帶註冊庫"],
    ]),
    p(rt("存量三步導入：", bold=True), rt("① AI 讀歷史合約與報價抽欄位建檔、人逐筆確認 ② 雙軌兩週（新案 100% 進系統、舊表凍結唯讀）③ 退役與卡帶化。詳 repo docs/MIGRATION.md（含各角色一天的變化、訪談確認清單）。")),

    h1("⑧ Agentic 作業泳道 — 誰做、AI 做什麼、資料落在哪"),
    p(rt("六條泳道：", bold=True), rt("客戶／同仁／AI 代理／平台規則／外部工具／Notion 資料層。互動版（可播放一張合約走完閉環）見線上提案第 8 節、以下為摘要：")),
    table(["階段", "同仁（人審）", "AI 代理", "平台規則", "資料落庫"], [
        ["報價 C0", "業務確認合作、產報價", "—", "建 C0、SLA 起算", "合約庫 +C0"],
        ["簽核・用印 C1-C2", "Teams 卡片核准；行政用印", "—", "簽核路由＋SLA 監看", "事件庫留痕"],
        ["寄出・回簽 C3-C4", "業務寄出", "回簽識別：判讀信件、抽欄位、通知財務", "C4 生效＋產全期款項排程", "合約庫 C4・款項庫 +N 期"],
        ["開票・收款 C5", "財務開票、一鍵確認", "對帳比對 → 建議打勾", "P1 → P3", "款項庫 P3・事件庫"],
        ["逾期・催收 P4", "業務按一下送催收信；主管接升級", "起草催收信＋風險預警", "催收梯級 D+3/7/30/60", "逾期標記・催收歷程"],
        ["結案・續約 C6-C7", "拍板續約條件", "續約條件建議（依付款紀錄）", "前 60 天開續約窗口", "合約庫 +新約 C0 → 閉環"],
    ]),

    h1("⑨ 技術架構（技術棧與 RD 定案）"),
    p(rt("三件事是定案：", bold=True), rt("能力層先行（三種介面吃同一套能力）、Notion 為資料權威源、獨立平台應用（與業務儀表板互鏈）。四層：介面層（1.0／1.5／2.0）→ 能力層（函式＝REST＝MCP 工具、卡帶接入面）→ 平台服務（狀態機、自建簽核引擎、事件匯流排、通知、催收規則、代理執行環境、信任橋接）→ 資料層（Notion 權威源＋快取佇列層擋每秒 3 請求限流）。")),
    table(["路徑", "組合", "取捨"], [
        ["A・正式產品線", "公司雲慣例（GCP）：Cloud Run＋Cloud SQL／Firestore＋Cloud Scheduler＋Pub/Sub", "對齊 RD 維運能力、直接是商轉多租戶地基；起步比 B 慢數天"],
        ["B・快速原型", "Vercel＋輕量託管資料庫", "一週內上線 dogfooding；商轉前需一次遷移"],
    ]),
    callout([rt("建議：", bold=True), rt("時程要求下週上線 — B 先行驗證流程、8 月 MCP 化時評估遷 A；RD 若評估可直上 A 更好。能力層與資料層走介面隔離、切換成本已控制。技術棧本週與 RD 定案。")], icon="✅", color="green_background"),

    h1("⑩ 卡帶規範 — 先鋒計畫的出口"),
    p(rt("L0 私人（註冊即用）→ L1 團隊（四件套齊＋資料契約過檢）→ L2 全公司（安全檢查＋真實資料驗證、決策負責人拍板）。四件套：Manifest（有名有姓負責人、離職必轉移）｜資料契約（禁影子欄位）｜能力層（寫入經信任橋接）｜事件（卡帶間只透過事件說話）。")),

    h1("⑪ 成功指標（建議、待拍板）"),
    table(["指標", "現況", "目標"], [
        ["收款追蹤覆蓋率", "帳外追蹤", "100%"],
        ["逾期浮現延遲", "月底結帳（最長 30 天）", "D+1"],
        ["回簽 → 財務通知", "人工轉達", "5 分鐘內"],
        ["續約提醒觸發率", "靠個人記憶", "100%（前 60 天零漏網）"],
        ["財務月底對帳", "約半天", "≤ 1 小時（代理對帳）"],
        ["新人上手", "口耳相傳", "≤ 1 小時"],
        ["先鋒卡帶接入", "—", "6 個月 ≥ 2 個"],
    ]),

    h1("⑫ 執行路線圖 — 下週上線、七月 dogfooding、八月 MCP 化"),
    table(["波次", "時間", "內容", "關卡"], [
        ["本週", "07-02 – 07-05", "訪談（行政、財務）、RD 技術棧定案、Notion 資料庫建置", "第一張真實合約可建檔"],
        ["下週", "07-06 – 07-12", "體驗 1.0 核心閉環上線（合約追蹤＋收款佇列＋通知）", "真實合約 C0 起步、狀態全留痕"],
        ["7 月中–月底", "07-13 – 07-31", "全員 dogfooding、首批代理（回簽識別／收款對帳）、1.5 聊天框", "財務真的用它收款、一句話開出草稿"],
        ["8 月", "08-01 – 08-31", "MCP 化完成（能力層 1:1 → Funraise MCP）、商轉評估啟動", "外部 AI 助理完成真實跨系統操作"],
        ["9 月起", "—", "產品化：多租戶、DottedSign 簽章升級、對外銷售", "第一個外部客戶上線"],
    ]),
    p(rt("進度以關卡為準；dogfooding 期間的規格修正優先於新功能。")),

    h1("⑬ 團隊分工"),
    p(rt("Nelsen Chen（發起・COO）｜Philis Chen（業務總經理・流程定義）｜Allen Hung（主導搭建）｜Jaric Kuo（CTO・技術棧定案）｜Carol Liao（訪談協調）｜Ting・Glendy（關鍵使用者）｜RD × 2（下週進場、待定）。")),
]
b3 = [
    h1("⑭ 待拍板"),
    numbered(rt("決策負責人與資源配置", bold=True), rt(" — Nelsen")),
    numbered(rt("「Flow」正式進 BizPeak 產品家族", bold=True), rt("（品牌定位已對齊品牌架構頁、剩命名確認）— Nelsen")),
    numbered(rt("NuEIP adapter 必要範圍", bold=True), rt("（簽核引擎已拍板自建）— 本週訪談")),
    numbered(rt("技術棧定案", bold=True), rt("：路徑 A（GCP 主線）或 B（原型先行）— 本週 Jaric × RD")),
    numbered(rt("對外簽署升級時機", bold=True), rt("：電子郵件回簽 → DottedSign 數位簽章 — Philis × 法務")),
    numbered(rt("通知通道優先序", bold=True), rt("：Teams／電子郵件／LINE — 本週訪談")),
    numbered(rt("Token 用量與 RD 資源", bold=True), rt(" — Nelsen × Jaric")),
    numbered(rt("repo 已轉公開", bold=True), rt("（內部盤點研究已分流出版控、歷史重建、匿名可讀驗證通過）— 已結案"),),
    divider(),
    p(rt("附錄：", bold=True), rt("一頁式互動提案 "), rt(SITE, link=SITE),
      rt("｜程式庫 "), rt(REPO.replace("https://", ""), link=REPO),
      rt("｜立項會議 "), rt("會議記錄", link="https://www.notion.so/391b219245158075a72dc361a13033d6"),
      rt("｜完整規格四文件與研究在 repo docs/")),
    p(rt("v0.3（2026-07-02）：三階段體驗定義修正（1.5＝介面長出聊天框、2.0＝外部 AI 應用 × MCP）、技術棧改 RD 定案制、時程壓縮至 8 月 MCP 化、敘事清洗。", color="gray")),
]

total = 0
for i, chunk in enumerate([b1, b2, b3], 1):
    res = api("PATCH", f"/blocks/{PAGE_ID}/children", {"children": chunk})
    total += len(res.get("results", []))
    print(f"批次 {i}：append {len(res.get('results', []))} 塊 OK")
    time.sleep(0.5)

# ── 3. 驗證 ──
verify = all_children(PAGE_ID)
h1s = []
for b in verify:
    t = b["type"]
    txt = "".join(r.get("plain_text", "") for r in b.get(t, {}).get("rich_text", []))
    if t == "heading_1" and txt: h1s.append(txt)
print(f"\n驗證：頁面共 {len(verify)} 頂層塊、H1：")
for x in h1s: print("  -", x)
ok = any("v0.4" in x for x in h1s) and not any(("v0.1" in x or "v0.2" in x or "v0.3" in x) for x in h1s)
print(f"\nv0.4 存在且舊版已移除：{ok}｜合計 append {total} 塊")
sys.exit(0 if ok else 2)
