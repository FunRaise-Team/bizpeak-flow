"""能力層 — 憲法第二條「能力先於介面」的實體。

三個入口共用這一份：
  server.py（MCP、體驗 2.0）· app.py 的 /api/*（網頁 1.0）· app.py 的 /api/chat（聊天框 1.5）
寫入動作皆落 Events 事件庫（憲法第五條）。
"""
from datetime import date as _date

import states
from notion_layer import (create_row, date, load_ids, query_db, read_prop,
                          select, text, title, update_row)


def _contracts(): return load_ids()["contracts"]
def _payments(): return load_ids()["payments"]
def _events(): return load_ids()["events"]


def contract_rows(status: str | None = None) -> list[dict]:
    rows = query_db(_contracts())
    out = []
    for r in rows:
        st = read_prop(r, "狀態")
        if status and st != status:
            continue
        out.append({
            "page_id": r["id"],
            "合約編號": read_prop(r, "合約編號"),
            "客戶": read_prop(r, "客戶"),
            "狀態": st,
            "狀態名": states.STATES.get(st, {}).get("name") if st else None,
            "負責業務": read_prop(r, "負責業務"),
            "金額": read_prop(r, "金額"),
            "生效日": read_prop(r, "生效日"),
            "到期日": read_prop(r, "到期日"),
        })
    out.sort(key=lambda c: c["合約編號"] or "")
    return out


def payment_rows() -> list[dict]:
    rows = query_db(_payments())
    out = [{
        "page_id": r["id"],
        "款項編號": read_prop(r, "款項編號"),
        "合約編號": read_prop(r, "合約編號"),
        "期數": read_prop(r, "期數"),
        "預計付款日": read_prop(r, "預計付款日"),
        "金額": read_prop(r, "金額"),
        "發票號": read_prop(r, "發票號"),
        "狀態": read_prop(r, "狀態"),
        "實收日": read_prop(r, "實收日"),
    } for r in rows]
    out.sort(key=lambda p: (p["預計付款日"] or "9999", p["款項編號"] or ""))
    return out


def event_rows(limit: int = 20) -> list[dict]:
    rows = query_db(_events())
    out = [{
        "事件": read_prop(r, "事件"),
        "合約編號": read_prop(r, "合約編號"),
        "動作": read_prop(r, "動作"),
        "執行者": read_prop(r, "執行者"),
        "時間": read_prop(r, "時間"),
    } for r in rows]
    out.sort(key=lambda e: e["時間"] or "", reverse=True)
    return out[:limit]


def log_event(contract_id: str, action: str, actor: str):
    n = f"EVT-{_date.today().strftime('%m%d')}-{abs(hash(action + actor)) % 10000:04d}"
    create_row(_events(), {
        "事件": title(n), "合約編號": text(contract_id),
        "動作": text(action), "執行者": text(actor),
        "時間": date(_date.today().isoformat()),
    })


# ── 六個能力（與 MCP 工具 1:1） ──

def contract_list(status: str = "") -> list[dict]:
    return contract_rows(status or None)


def contract_get(contract_id: str) -> dict:
    cs = [c for c in contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    c["款項"] = [p for p in payment_rows() if p["合約編號"] == contract_id]
    return c


def contract_transition(contract_id: str, to_state: str, reason: str = "",
                        actor: str = "使用者") -> dict:
    cs = [c for c in contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    v = states.validate_transition(c["狀態"], to_state, reason)
    if not v["ok"]:
        return {"error": v["error"]}
    update_row(c["page_id"], {"狀態": select(to_state)})
    kind = "退回" if v["kind"] == "rollback" else "前進"
    log_event(contract_id, f"狀態{kind}：{c['狀態']} → {to_state}" + (f"（理由：{reason}）" if reason else ""), actor)
    return {"ok": True, "合約編號": contract_id, "from": c["狀態"], "to": to_state,
            "to_name": states.STATES[to_state]["name"], "kind": v["kind"]}


def payment_overdue_list(today: str = "") -> list[dict]:
    t = today or _date.today().isoformat()
    out = []
    for p in payment_rows():
        if p["狀態"] == "P3":
            continue
        due = p["預計付款日"]
        if p["狀態"] == "P4" or (due and due < t):
            days = (_date.fromisoformat(t) - _date.fromisoformat(due)).days if due else None
            out.append({**p, "逾期天數": days})
    return out


def payment_mark_paid(payment_id: str, paid_date: str = "", actor: str = "財務") -> dict:
    ps = [p for p in payment_rows() if p["款項編號"] == payment_id]
    if not ps:
        return {"error": f"找不到款項 {payment_id}"}
    p = ps[0]
    d = paid_date or _date.today().isoformat()
    update_row(p["page_id"], {"狀態": select("P3"), "實收日": date(d)})
    amt = p["金額"] or 0
    log_event(p["合約編號"] or "", f"款項 {payment_id}（{p['期數']} 期、{amt:,.0f}）收款確認、實收日 {d}", actor)
    return {"ok": True, "款項編號": payment_id, "實收日": d}


def cashflow_forecast() -> dict:
    by_month: dict[str, float] = {}
    overdue = 0.0
    for p in payment_rows():
        if p["狀態"] == "P3" or not p["預計付款日"]:
            continue
        amt = p["金額"] or 0
        if p["狀態"] == "P4":
            overdue += amt
        m = p["預計付款日"][:7]
        by_month[m] = by_month.get(m, 0) + amt
    return {"未收款按月": dict(sorted(by_month.items())), "其中逾期": overdue,
            "未收合計": sum(by_month.values())}
