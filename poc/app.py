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

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import capabilities as cap
import states

app = FastAPI(title="BizPeak Flow POC")
WEB = Path(__file__).parent / "web"

GEMINI_MODEL = "gemini-2.5-flash"


def _gemini_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env = Path.home() / "NelsenClaw" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("找不到 GEMINI_API_KEY")


# ── 30 秒快取（擋 Notion 限流；寫入後主動失效）──
_cache: dict = {"t": 0.0, "data": None}


def _bootstrap_data(force: bool = False) -> dict:
    if not force and _cache["data"] and time.time() - _cache["t"] < 30:
        return _cache["data"]
    contracts = cap.contract_rows()
    payments = cap.payment_rows()
    data = {
        "contracts": contracts,
        "payments": payments,
        "overdue": cap.payment_overdue_list(),
        "cashflow": cap.cashflow_forecast(),
        "events": cap.event_rows(),
        "states": {k: v | {"next": states.FORWARD.get(k, [])} for k, v in states.STATES.items()},
        "order": states.ORDER,
        "synced_at": datetime.now().strftime("%H:%M:%S"),
    }
    _cache.update(t=time.time(), data=data)
    return data


def _invalidate():
    _cache["data"] = None


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/api/bootstrap")
def bootstrap():
    return _bootstrap_data()


class TransitionReq(BaseModel):
    contract_id: str
    to_state: str
    reason: str = ""


@app.post("/api/transition")
def transition(req: TransitionReq):
    r = cap.contract_transition(req.contract_id, req.to_state, req.reason, actor="網頁使用者")
    if r.get("ok"):
        _invalidate()
    return r


class PaidReq(BaseModel):
    payment_id: str


@app.post("/api/mark_paid")
def mark_paid(req: PaidReq):
    r = cap.payment_mark_paid(req.payment_id, actor="網頁・財務")
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
def create(req: CreateReq):
    r = cap.contract_create(req.customer, req.amount, req.terms, req.first_due,
                            req.owner, req.expiry, actor="網頁使用者")
    if r.get("ok"):
        _invalidate()
    return r


class InvoiceReq(BaseModel):
    payment_id: str
    invoice_no: str


@app.post("/api/invoice")
def invoice(req: InvoiceReq):
    r = cap.payment_invoice(req.payment_id, req.invoice_no, actor="網頁・財務")
    if r.get("ok"):
        _invalidate()
    return r


class RenewReq(BaseModel):
    contract_id: str


@app.post("/api/renew")
def renew(req: RenewReq):
    r = cap.contract_renew(req.contract_id, actor="網頁使用者")
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
    {"name": "ui_navigate", "description": "切換使用者眼前的介面頁籤、可高亮某編號。回答涉及某頁籤資料時呼叫、讓使用者直接看到",
     "parameters": {"type": "object", "properties": {
         "tab": {"type": "string", "enum": ["overview", "payments", "overdue", "cashflow", "events"]},
         "highlight": {"type": "string", "description": "要高亮的合約或款項編號（可選）"}}, "required": ["tab"]}},
]

def sys_prompt() -> str:
    return f"""今天是 {datetime.now().strftime('%Y-%m-%d')}。你是 BizPeak Flow（FUNRAISE 合約生命週期系統）介面裡的操作助理、使用者正在看網頁介面（頁籤：overview 合約總覽 / payments 收款 / overdue 逾期 / cashflow 現金流 / events 事件）。
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
- 建約（contract_create）至少要客戶名與金額；期數與首期付款日沒講就用預設並在回覆說明"""

CAP_FN = {
    "contract_list": cap.contract_list,
    "contract_get": cap.contract_get,
    "contract_transition": lambda **kw: cap.contract_transition(actor="聊天助理（人審後）", **kw),
    "payment_overdue_list": cap.payment_overdue_list,
    "payment_mark_paid": lambda **kw: cap.payment_mark_paid(actor="聊天助理（人審後）", **kw),
    "cashflow_forecast": cap.cashflow_forecast,
    "contract_create": lambda **kw: cap.contract_create(actor="聊天助理（人審後）", **kw),
    "payment_invoice": lambda **kw: cap.payment_invoice(actor="聊天助理（人審後）", **kw),
    "contract_renew": lambda **kw: cap.contract_renew(actor="聊天助理（人審後）", **kw),
}
WRITE_FNS = {"contract_transition", "payment_mark_paid", "contract_create", "payment_invoice", "contract_renew"}


def _gemini(contents: list) -> dict:
    body = {
        "system_instruction": {"parts": [{"text": sys_prompt()}]},
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


@app.post("/api/chat")
def chat(req: ChatReq):
    contents = [{"role": h["role"], "parts": [{"text": h["text"]}]}
                for h in req.history[-8:] if h.get("text")]
    contents.append({"role": "user", "parts": [{"text": req.message}]})
    actions, refresh = [], False

    for _ in range(6):
        try:
            res = _gemini(contents)
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
