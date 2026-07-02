"""BizPeak Flow MCP 伺服器（POC）— 體驗 2.0 的第一塊真拼圖。

能力層原則（憲法第二條）：這裡的每個工具、就是未來 1.0 介面按鈕與 1.5 聊天框
背後的同一批能力 — 三種介面吃同一副骨。
寫入動作（狀態轉移、收款打勾）皆落 Events 事件庫 — 憲法第五條、每個狀態變化留痕。

執行：uv run server.py（stdio）
掛載 Claude Code：claude mcp add bizpeak -- uv run --project <此目錄> server.py
"""
from datetime import date as _date

from mcp.server.fastmcp import FastMCP

import states
from notion_layer import (create_row, date, load_ids, query_db, read_prop,
                          select, text, title, update_row)

mcp = FastMCP("bizpeak-flow")


def _contracts(): return load_ids()["contracts"]
def _payments(): return load_ids()["payments"]
def _events(): return load_ids()["events"]


def _contract_rows(status: str | None = None) -> list[dict]:
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
            "到期日": read_prop(r, "到期日"),
        })
    return out


def _payment_rows() -> list[dict]:
    rows = query_db(_payments())
    return [{
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


def _log_event(contract_id: str, action: str, actor: str):
    n = f"EVT-{_date.today().strftime('%m%d')}-{abs(hash(action)) % 10000:04d}"
    create_row(_events(), {
        "事件": title(n), "合約編號": text(contract_id),
        "動作": text(action), "執行者": text(actor),
        "時間": date(_date.today().isoformat()),
    })


@mcp.tool()
def contract_list(status: str = "") -> list[dict]:
    """列出合約。status 可選（C0-C7 / X1 / X2）、空字串列全部。"""
    return _contract_rows(status or None)


@mcp.tool()
def contract_get(contract_id: str) -> dict:
    """單張合約詳情＋其款項排程。contract_id 例：CT-2026-041。"""
    cs = [c for c in _contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    c["款項"] = [p for p in _payment_rows() if p["合約編號"] == contract_id]
    return c


@mcp.tool()
def contract_transition(contract_id: str, to_state: str, reason: str = "", actor: str = "MCP 使用者") -> dict:
    """合約狀態轉移 — 經狀態機驗證（單向前進；退回必附 reason）、寫入事件留痕。"""
    cs = [c for c in _contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    v = states.validate_transition(c["狀態"], to_state, reason)
    if not v["ok"]:
        return {"error": v["error"]}
    update_row(c["page_id"], {"狀態": select(to_state)})
    kind = "退回" if v["kind"] == "rollback" else "前進"
    _log_event(contract_id, f"狀態{kind}：{c['狀態']} → {to_state}" + (f"（理由：{reason}）" if reason else ""), actor)
    return {"ok": True, "合約編號": contract_id, "from": c["狀態"], "to": to_state,
            "to_name": states.STATES[to_state]["name"], "kind": v["kind"]}


@mcp.tool()
def payment_overdue_list(today: str = "") -> list[dict]:
    """逾期款項清單（狀態 P4、或已過預計付款日且未收款）。today 預設今天、可覆寫供演示。"""
    t = today or _date.today().isoformat()
    out = []
    for p in _payment_rows():
        if p["狀態"] == "P3":
            continue
        due = p["預計付款日"]
        if p["狀態"] == "P4" or (due and due < t):
            days = (_date.fromisoformat(t) - _date.fromisoformat(due)).days if due else None
            out.append({**p, "逾期天數": days})
    return out


@mcp.tool()
def payment_mark_paid(payment_id: str, paid_date: str = "", actor: str = "財務") -> dict:
    """收款打勾（人審動作 — 憲法第四條：確認由人發起、系統留痕）。"""
    ps = [p for p in _payment_rows() if p["款項編號"] == payment_id]
    if not ps:
        return {"error": f"找不到款項 {payment_id}"}
    p = ps[0]
    d = paid_date or _date.today().isoformat()
    update_row(p["page_id"], {"狀態": select("P3"), "實收日": date(d)})
    _log_event(p["合約編號"] or "", f"款項 {payment_id}（{p['期數']} 期、{p['金額']:,.0f}）收款確認、實收日 {d}", actor)
    return {"ok": True, "款項編號": payment_id, "實收日": d}


@mcp.tool()
def cashflow_forecast() -> dict:
    """現金流量預測 — 未收款項按月彙總（管理層入口的核心數字）。"""
    by_month: dict[str, float] = {}
    overdue = 0.0
    for p in _payment_rows():
        if p["狀態"] == "P3" or not p["預計付款日"]:
            continue
        amt = p["金額"] or 0
        if p["狀態"] == "P4":
            overdue += amt
        by_month[p["預計付款日"][:7]] = by_month.get(p["預計付款日"][:7], 0) + amt
    return {"未收款按月": dict(sorted(by_month.items())), "其中逾期": overdue,
            "未收合計": sum(by_month.values())}


if __name__ == "__main__":
    mcp.run()
