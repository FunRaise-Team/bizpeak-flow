"""BizPeak Flow 網頁應用（體驗 1.0 + 1.5）— POC。

1.0：三頁籤介面（總覽 / 收款 / 逾期 / 事件）、真資料、按鈕真的寫回 Notion。
1.5：右下聊天框 — Gemini 函式呼叫解意圖、驅動同一個能力層、並指揮前端導航。
三個入口（本應用、聊天框、MCP）共用 capabilities.py — 憲法第二條的活證明。

執行：uv run uvicorn app:app --port 8790
"""
import json
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

import capabilities as cap
import states

app = FastAPI(title="BizPeak Flow POC")
WEB = Path(__file__).parent / "web"

# ── 存取關卡（Rule 8：內部工具不裸奔）— 設 APP_ACCESS_KEY 才啟用；本機開發不擋 ──
APP_KEY = os.environ.get("APP_ACCESS_KEY", "")


@app.middleware("http")
async def access_gate(request: Request, call_next):
    if not APP_KEY:
        return await call_next(request)
    supplied = (request.query_params.get("key", "") or request.cookies.get("bpf_key", "")
                or request.headers.get("x-app-key", ""))
    if supplied != APP_KEY:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "未授權 — 請用完整分享連結重新開啟頁面"}, status_code=401)
        return HTMLResponse("<div style='font-family:sans-serif;padding:48px;color:#26261F'>"
                            "<h3>BizPeak Flow — 需要存取金鑰</h3><p>請使用完整的分享連結（含 key）開啟。</p></div>",
                            status_code=401)
    resp = await call_next(request)
    if request.url.path == "/":
        resp.set_cookie("bpf_key", APP_KEY, httponly=True, max_age=86400 * 30, samesite="lax")
    return resp

GEMINI_MODEL = "gemini-2.5-flash"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")          # gemini | nvidia
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")


def _gemini_key() -> str:
    return _env_key("GEMINI_API_KEY")


# ── 30 秒快取（擋 Notion 限流；寫入後主動失效）──
_cache: dict = {"t": 0.0, "data": None}


def _bootstrap_data(force: bool = False) -> dict:
    if not force and _cache["data"] and time.time() - _cache["t"] < 30:
        return _cache["data"]
    _safe(cap.overdue_lazy_flag, 0)   # 過期未收自動標 P4（冪等、有變更才寫）
    contracts = cap.contract_rows()
    payments = cap.payment_rows()
    # SLA 卡關計算（讀取時動態、免排程器）
    from datetime import date as _d
    for c in contracts:
        sla = states.STATES.get(c["狀態"] or "", {}).get("sla_days")
        entered = c.get("狀態進入日")
        c["卡關天數"] = None
        c["SLA 剩餘"] = None
        if entered:
            try:
                days = (_d.today() - _d.fromisoformat(entered[:10])).days
                c["卡關天數"] = days
                if sla:
                    c["SLA 剩餘"] = sla - days
            except ValueError:
                pass
    data = {
        "contracts": contracts,
        "payments": payments,
        "overdue": cap.payment_overdue_list(),
        "cashflow": cap.cashflow_forecast(),
        "events": cap.event_rows(),
        "states": {k: v | {"next": states.FORWARD.get(k, [])} for k, v in states.STATES.items()},
        "customers": _safe(lambda: [c["name"] for c in cap.customer_list()], []),
        "staff": _safe(cap.staff_list, []),
        "quotes_ready": _safe(cap.quote_ready_list, []),
        "quotes_all": _safe(lambda: [{**q, "編輯連結": cap.QUOTE_EDIT + (q["page_id"] or "").replace("-", ""),
                                      "notion_url": cap.notion_url(q["page_id"])} for q in cap.quote_rows()], []),
        "products": _safe(cap.product_list, []),
        "comments": _safe(cap.comment_list, []),
        "renewals": _safe(cap.renewal_alerts, []),
        "order": states.ORDER,
        "synced_at": datetime.now().strftime("%H:%M:%S"),
    }
    _cache.update(t=time.time(), data=data)
    return data


def _invalidate():
    _cache["data"] = None


def _safe(fn, fallback):
    try:
        return fn()
    except Exception:
        return fallback


def _actor(request: Request) -> str:
    from urllib.parse import unquote
    a = unquote((request.headers.get("x-actor") or "").strip())
    return a[:40] if a else "網頁使用者"


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/api/bootstrap")
def bootstrap():
    try:
        return _bootstrap_data()
    except Exception as e:
        import sys as _sys
        print(f"bootstrap 失敗: {type(e).__name__}", file=_sys.stderr)
        return JSONResponse({"error": f"資料層暫時無法讀取（{type(e).__name__}）"}, status_code=500)


class TransitionReq(BaseModel):
    contract_id: str
    to_state: str
    reason: str = ""


@app.post("/api/transition")
def transition(req: TransitionReq, request: Request):
    r = cap.contract_transition(req.contract_id, req.to_state, req.reason, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class PaidReq(BaseModel):
    payment_id: str


@app.post("/api/mark_paid")
def mark_paid(req: PaidReq, request: Request):
    r = cap.payment_mark_paid(req.payment_id, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class CreateReq(BaseModel):
    customer: str
    amount: float
    terms: int = 1
    first_due: str = ""
    owner: str = ""
    expiry: str = ""


@app.post("/api/create")
def create(req: CreateReq, request: Request):
    r = cap.contract_create(req.customer, req.amount, req.terms, req.first_due,
                            req.owner, req.expiry, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class InvoiceReq(BaseModel):
    payment_id: str
    invoice_no: str


@app.post("/api/invoice")
def invoice(req: InvoiceReq, request: Request):
    r = cap.payment_invoice(req.payment_id, req.invoice_no, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class QuoteImportReq(BaseModel):
    quote_no: str
    terms: int = 1
    first_due: str = ""


@app.post("/api/quote_import")
def quote_import(req: QuoteImportReq, request: Request):
    r = cap.quote_import(req.quote_no, req.terms, req.first_due, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class RenewReq(BaseModel):
    contract_id: str


@app.post("/api/renew")
def renew(req: RenewReq, request: Request):
    r = cap.contract_renew(req.contract_id, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class ProductReq(BaseModel):
    name: str
    ptype: str = "顧問服務"
    pricing: str = "報價制"
    price: float | None = None
    note: str = ""


@app.post("/api/product_create")
def product_create(req: ProductReq, request: Request):
    r = cap.product_create(req.name, req.ptype, req.pricing, req.price, req.note, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class QuoteCreateReq(BaseModel):
    customer: str
    plan: str = "Growth"
    owner: str = ""
    discount_untaxed: float | None = None


@app.post("/api/quote_create")
def quote_create_ep(req: QuoteCreateReq, request: Request):
    r = cap.quote_create(req.customer, req.plan, req.owner, req.discount_untaxed, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


class CommentReq(BaseModel):
    contract_id: str
    content: str


@app.post("/api/comment")
def comment(req: CommentReq, request: Request):
    r = cap.comment_add(req.contract_id, req.content, actor=_actor(request))
    if r.get("ok"):
        _invalidate()
    return r


# ── 1.5 聊天框：Gemini 函式呼叫 ──

TOOL_DECLS = [
    {"name": "contract_list", "description": "列出合約、可依狀態（C0-C7/X1/X2）過濾",
     "parameters": {"type": "object", "properties": {"status": {"type": "string"}}}},
    {"name": "contract_get", "description": "單張合約詳情與款項排程",
     "parameters": {"type": "object", "properties": {"contract_id": {"type": "string"}}, "required": ["contract_id"]}},
    {"name": "contract_transition", "description": "合約狀態轉移（單向前進；退回必附 reason、會被狀態機驗證）",
     "parameters": {"type": "object", "properties": {"contract_id": {"type": "string"}, "to_state": {"type": "string"}, "reason": {"type": "string"}}, "required": ["contract_id", "to_state"]}},
    {"name": "payment_overdue_list", "description": "逾期款項清單",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "payment_mark_paid", "description": "款項收款確認（人審動作、使用者明確要求才可呼叫）",
     "parameters": {"type": "object", "properties": {"payment_id": {"type": "string"}}, "required": ["payment_id"]}},
    {"name": "cashflow_forecast", "description": "未收款按月彙總（現金流量預測）",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "contract_create", "description": "建立合約（C0 報價草稿、閉環起點）。需客戶名與金額；期數 1-12、首期付款日 YYYY-MM-DD",
     "parameters": {"type": "object", "properties": {
         "customer": {"type": "string"}, "amount": {"type": "number"},
         "terms": {"type": "integer"}, "first_due": {"type": "string"},
         "owner": {"type": "string"}, "expiry": {"type": "string"}}, "required": ["customer", "amount"]}},
    {"name": "payment_invoice", "description": "開立發票（P0/P4 → P1）、發票號必填（人審動作、使用者明確要求才可呼叫）",
     "parameters": {"type": "object", "properties": {"payment_id": {"type": "string"}, "invoice_no": {"type": "string"}}, "required": ["payment_id", "invoice_no"]}},
    {"name": "contract_renew", "description": "續約開新約（原約需在 C7 續約窗口）、新約沿用條件回 C0（人審動作）",
     "parameters": {"type": "object", "properties": {"contract_id": {"type": "string"}}, "required": ["contract_id"]}},
    {"name": "customer_list", "description": "公司客戶主資料清單（名稱與負責人）— 建約前查客戶正式名稱用",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "quote_ready_list", "description": "可建約的報價單清單（狀態已簽約/已核准/已用印、含是否已匯入）",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "quote_import", "description": "從已簽約報價單一鍵建約（帶入客戶、金額、負責人）。quote_no 例 FR-Q-2026-06-18-001-SSIC（人審動作）",
     "parameters": {"type": "object", "properties": {"quote_no": {"type": "string"}, "terms": {"type": "integer"}, "first_due": {"type": "string"}}, "required": ["quote_no"]}},
    {"name": "product_list", "description": "產品目錄（顧問服務 / 標準產品 / 訂閱 / 客製、含建議單價）",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "comment_add", "description": "在某張合約上留言（會同步到 Notion 合約頁、留言人=目前操作者）",
     "parameters": {"type": "object", "properties": {"contract_id": {"type": "string"}, "content": {"type": "string"}}, "required": ["contract_id", "content"]}},
    {"name": "comment_list", "description": "查某張合約的留言（contract_id 空字串查全部）",
     "parameters": {"type": "object", "properties": {"contract_id": {"type": "string"}}}},
    {"name": "quote_create", "description": "建立 Co-Evo 報價單（寫入公司報價庫、回編輯連結）。plan = Starter / Growth / Pro；discount_untaxed 為議價未稅金額（會自動 ×1.05 換含稅）。人審動作、使用者明確要求才可呼叫",
     "parameters": {"type": "object", "properties": {"customer": {"type": "string"}, "plan": {"type": "string"}, "owner": {"type": "string"}, "discount_untaxed": {"type": "number"}}, "required": ["customer"]}},
    {"name": "ui_navigate", "description": "切換使用者眼前的介面頁籤、可高亮某編號。回答涉及某頁籤資料時呼叫、讓使用者直接看到",
     "parameters": {"type": "object", "properties": {
         "tab": {"type": "string", "enum": ["overview", "payments", "overdue", "calendar", "cashflow", "quotes", "products", "events"]},
         "highlight": {"type": "string", "description": "要高亮的合約或款項編號（可選）"}}, "required": ["tab"]}},
]

def sys_prompt(who: str = "使用者") -> str:
    return f"""今天是 {datetime.now().strftime('%Y-%m-%d')}。目前操作者：{who} — 你替這個人執行、寫入記錄會標「{who}（經助理）」。你是 BizPeak Flow（FUNRAISE 合約生命週期系統）介面裡的操作助理、使用者正在看網頁介面（頁籤：overview 合約總覽 / payments 收款 / overdue 逾期 / calendar 日曆 / cashflow 現金流 / quotes 報價 / products 產品 / events 操作紀錄）。
使用者說相對日期（八月十五、下個月初）一律解讀為未來最近的那個日期、年份以今天為準。
規則：
- 查詢與操作一律用工具、絕不編造資料
- 寫入動作（contract_transition / payment_mark_paid）只在使用者明確要求時執行、執行後說清楚做了什麼；被狀態機擋下就白話解釋原因
- 回答涉及某頁籤的資料時、呼叫 ui_navigate 切過去（可帶 highlight 編號）、讓使用者直接看到
- 繁體中文、白話簡潔、金額千分位
- 狀態代號：C0 報價草稿→C1 內部簽核→C2 用印完成→C3 待客戶回簽→C4 回簽生效→C5 履約收款→C6 結案→C7 續約窗口；X1 作廢、X2 不需寄出歸檔；款項 P0 排程/P1 已開票/P2 已通知/P3 已收款/P4 逾期
- 轉移只能單向前進、退回必附理由
- 使用者用客戶名稱指稱合約時、先用 contract_list 自行找到對應的合約編號再操作、不要反問使用者編號；只有同名多筆時才請使用者確認
- 閉環規則：轉入 C4 會自動產生款項排程；C6 結案前款項必須全收（系統會擋）；C7 續約窗口用 contract_renew 開新約回 C0
- 建約（contract_create）至少要客戶名與金額；期數與首期付款日沒講就用預設並在回覆說明
- Co-Evo 報價（quote_create）：Starter 首年 22,800 / Growth 41,800（主推）/ Pro 68,800（皆未稅）；建立後把編輯連結給使用者；報價單簽回後用 quote_import 建約"""

CAP_FN = {
    "contract_list": cap.contract_list,
    "contract_get": cap.contract_get,
    "contract_transition": cap.contract_transition,
    "payment_overdue_list": cap.payment_overdue_list,
    "payment_mark_paid": cap.payment_mark_paid,
    "cashflow_forecast": cap.cashflow_forecast,
    "contract_create": cap.contract_create,
    "payment_invoice": cap.payment_invoice,
    "contract_renew": cap.contract_renew,
    "customer_list": cap.customer_list,
    "quote_ready_list": cap.quote_ready_list,
    "quote_import": cap.quote_import,
    "quote_create": cap.quote_create,
    "product_list": cap.product_list,
    "comment_add": cap.comment_add,
    "comment_list": cap.comment_list,
}
_SYS_WHO: dict = {}
WRITE_FNS = {"contract_transition", "payment_mark_paid", "contract_create", "payment_invoice", "contract_renew", "quote_import", "comment_add", "quote_create"}


def _env_key(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name].strip()
    env = Path.home() / "NelsenClaw" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(f"找不到 {name}")


def _nvidia(contents: list) -> dict:
    """NVIDIA 免費端點（OpenAI 相容）— 格式雙向轉換、回傳仿 Gemini 結構。備援用（實測延遲高）。"""
    msgs = []
    for c in contents:
        parts = c.get("parts", [])
        if any("functionResponse" in x for x in parts):
            for x in parts:
                fr = x["functionResponse"]
                msgs.append({"role": "tool", "name": fr["name"],
                             "tool_call_id": fr["name"], "content": json.dumps(fr["response"], ensure_ascii=False)})
        elif any("functionCall" in x for x in parts):
            msgs.append({"role": "assistant", "tool_calls": [
                {"id": x["functionCall"]["name"], "type": "function",
                 "function": {"name": x["functionCall"]["name"],
                              "arguments": json.dumps(x["functionCall"].get("args", {}), ensure_ascii=False)}}
                for x in parts if "functionCall" in x]})
        else:
            msgs.append({"role": "user" if c.get("role") == "user" else "assistant",
                         "content": "".join(x.get("text", "") for x in parts)})
    body = {"model": NVIDIA_MODEL,
            "messages": [{"role": "system", "content": sys_prompt(_SYS_WHO.get("w", "使用者"))}] + msgs,
            "tools": [{"type": "function", "function": d} for d in TOOL_DECLS],
            "temperature": 0.2, "max_tokens": 1024}
    req = urllib.request.Request("https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_env_key('NVIDIA_API_KEY')}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    m = d["choices"][0]["message"]
    parts = []
    for tc in m.get("tool_calls") or []:
        parts.append({"functionCall": {"name": tc["function"]["name"],
                                       "args": json.loads(tc["function"].get("arguments") or "{}")}})
    if m.get("content"):
        parts.append({"text": m["content"]})
    return {"candidates": [{"content": {"parts": parts}}]}


def _gemini(contents: list) -> dict:
    body = {
        "system_instruction": {"parts": [{"text": sys_prompt(_SYS_WHO.get("w", "使用者"))}]},
        "contents": contents,
        "tools": [{"function_declarations": TOOL_DECLS}],
        "generation_config": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={_gemini_key()}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


class ChatReq(BaseModel):
    message: str
    history: list = []  # [{role: "user"|"model", text: str}]
    actor: str = ""


@app.post("/api/chat")
def chat(req: ChatReq, request: Request):
    who = (req.actor or _actor(request)).strip()[:40] or "使用者"
    via = f"{who}（經助理）"
    _SYS_WHO["w"] = who
    contents = [{"role": h["role"], "parts": [{"text": h["text"]}]}
                for h in req.history[-8:] if h.get("text")]
    contents.append({"role": "user", "parts": [{"text": req.message}]})
    actions, refresh = [], False

    for _ in range(6):
        try:
            res = _nvidia(contents) if LLM_PROVIDER == "nvidia" else _gemini(contents)
        except Exception as e:
            return JSONResponse({"reply": f"助理暫時連不上（{e}）、請再試一次。", "actions": [], "refresh": False})
        parts = (res.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if not calls:
            reply = "".join(p.get("text", "") for p in parts) or "（沒有回覆）"
            return {"reply": reply, "actions": actions, "refresh": refresh}

        contents.append({"role": "model", "parts": parts})
        fr_parts = []
        for call in calls:
            name, args = call["name"], call.get("args", {}) or {}
            if name == "ui_navigate":
                actions.append(args)
                result = {"ok": True}
            elif name in CAP_FN:
                try:
                    if name in WRITE_FNS:
                        args = {**args, "actor": via}
                    result = CAP_FN[name](**args)
                except Exception as e:
                    result = {"error": str(e)}
                if name in WRITE_FNS and isinstance(result, dict) and result.get("ok"):
                    refresh = True
                    _invalidate()
            else:
                result = {"error": f"未知工具 {name}"}
            if not isinstance(result, dict):
                result = {"result": result}
            fr_parts.append({"functionResponse": {"name": name, "response": result}})
        contents.append({"role": "user", "parts": fr_parts})

    return {"reply": "這個要求太複雜、我卡住了 — 換個說法試試？", "actions": actions, "refresh": refresh}
