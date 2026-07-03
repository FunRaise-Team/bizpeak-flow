"""能力層 — 憲法第二條「能力先於介面」的實體。

三個入口共用這一份：
  server.py（MCP、體驗 2.0）· app.py 的 /api/*（網頁 1.0）· app.py 的 /api/chat（聊天框 1.5）
寫入動作皆落 Events 事件庫（憲法第五條）。

閉環規則（本檔集中執法）：
  轉入 C4（回簽生效）→ 自動產生款項排程
  轉入 C6（結案）→ 款項未全收擋下（終端不變量）
  C7（續約窗口）→ contract_renew 一鍵開新約回 C0
"""
from datetime import date as _date, timedelta

import states
from notion_layer import (create_row, date, load_ids, number, query_db,
                          read_prop, select, text, title, update_row)


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
            "期數": read_prop(r, "期數"),
            "首期日": read_prop(r, "首期日"),
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


def event_rows(limit: int = 30) -> list[dict]:
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


_evt_seq = {"n": 0}


def log_event(contract_id: str, action: str, actor: str):
    _evt_seq["n"] += 1
    n = f"EVT-{_date.today().strftime('%m%d')}-{(abs(hash(action + actor)) + _evt_seq['n']) % 10000:04d}"
    create_row(_events(), {
        "事件": title(n), "合約編號": text(contract_id),
        "動作": text(action), "執行者": text(actor),
        "時間": date(_date.today().isoformat()),
    })


def _next_contract_id() -> str:
    year = _date.today().year
    nums = []
    for c in contract_rows():
        cid = c["合約編號"] or ""
        parts = cid.split("-")
        if len(parts) == 3 and parts[2].isdigit():
            nums.append(int(parts[2]))
    return f"CT-{year}-{(max(nums) + 1 if nums else 1):03d}"


# ── 能力（三入口共用、與 MCP 工具 1:1） ──

def contract_list(status: str = "") -> list[dict]:
    return contract_rows(status or None)


def contract_get(contract_id: str) -> dict:
    cs = [c for c in contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    c["款項"] = [p for p in payment_rows() if p["合約編號"] == contract_id]
    return c


def contract_create(customer: str, amount: float, terms: int = 1, first_due: str = "",
                    owner: str = "", expiry: str = "", actor: str = "使用者") -> dict:
    """建立合約（C0 報價草稿）— 閉環的起點。terms 期數、first_due 首期付款日。"""
    if not customer or not amount:
        return {"error": "客戶與金額為必填"}
    if terms < 1 or terms > 12:
        return {"error": "期數需在 1–12 之間"}
    cid = _next_contract_id()
    create_row(_contracts(), {
        "合約編號": title(cid), "客戶": text(customer), "狀態": select("C0"),
        "負責業務": text(owner or actor), "金額": number(amount), "期數": number(terms),
        "首期日": date(first_due or None), "到期日": date(expiry or None),
    })
    log_event(cid, f"建立合約（C0 報價草稿）：{customer}、{amount:,.0f}、{terms} 期", actor)
    return {"ok": True, "合約編號": cid, "狀態": "C0", "客戶": customer}


def payment_schedule_generate(contract_id: str, actor: str = "平台規則") -> dict:
    """依合約金額 / 期數 / 首期日產生款項排程（每期間隔 3 個月、末期補差）。冪等：已有款項則跳過。"""
    c = contract_get(contract_id)
    if c.get("error"):
        return c
    if c.get("款項"):
        return {"ok": True, "skipped": True, "note": f"{contract_id} 已有 {len(c['款項'])} 筆款項、不重複產生"}
    terms = int(c["期數"] or 1)
    amount = c["金額"] or 0
    first = c["首期日"] or _date.today().isoformat()
    base = round(amount / terms, 0)
    d0 = _date.fromisoformat(first)
    made = []
    for i in range(terms):
        amt = amount - base * (terms - 1) if i == terms - 1 else base
        due = d0 + timedelta(days=91 * i)
        pid = f"PM-{contract_id.split('-')[2]}-{i + 1}"
        create_row(_payments(), {
            "款項編號": title(pid), "合約編號": text(contract_id), "期數": text(f"{i + 1}/{terms}"),
            "預計付款日": date(due.isoformat()), "金額": number(amt), "狀態": select("P0"),
        })
        made.append(pid)
    log_event(contract_id, f"回簽生效 → 自動產生款項排程 {terms} 期（{'、'.join(made)}）、現金流量預測已更新", actor)
    return {"ok": True, "produced": made}


def contract_transition(contract_id: str, to_state: str, reason: str = "",
                        actor: str = "使用者") -> dict:
    cs = [c for c in contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    v = states.validate_transition(c["狀態"], to_state, reason)
    if not v["ok"]:
        return {"error": v["error"]}
    # 終端不變量：結案前款項必須全收
    if to_state == "C6":
        pays = [p for p in payment_rows() if p["合約編號"] == contract_id]
        unpaid = [p["款項編號"] for p in pays if p["狀態"] != "P3"]
        if unpaid:
            return {"error": f"不能結案：還有 {len(unpaid)} 筆款項未收（{'、'.join(unpaid)}）— 全部收款確認後才可轉 C6"}
    update_row(c["page_id"], {"狀態": select(to_state)})
    kind = "退回" if v["kind"] == "rollback" else "前進"
    log_event(contract_id, f"狀態{kind}：{c['狀態']} → {to_state}" + (f"（理由：{reason}）" if reason else ""), actor)
    out = {"ok": True, "合約編號": contract_id, "from": c["狀態"], "to": to_state,
           "to_name": states.STATES[to_state]["name"], "kind": v["kind"]}
    # 閉環規則：回簽生效 → 自動產生款項排程
    if to_state == "C4":
        out["schedule"] = payment_schedule_generate(contract_id)
    return out


def contract_renew(contract_id: str, actor: str = "使用者") -> dict:
    """續約開新約 — 原約需在 C7（續約窗口）；新約沿用客戶 / 金額 / 期數、回到 C0。閉環完成。"""
    c = contract_get(contract_id)
    if c.get("error"):
        return c
    if c["狀態"] != "C7":
        return {"error": f"{contract_id} 目前是 {c['狀態']}（{c['狀態名']}）— 需先到 C7 續約窗口才能開新約"}
    new = contract_create(c["客戶"], c["金額"] or 0, int(c["期數"] or 1), "",
                          c["負責業務"] or "", "", actor=actor)
    if not new.get("ok"):
        return new
    log_event(contract_id, f"續約成立 → 新約 {new['合約編號']}（條件沿用、閉環回 C0）", actor)
    return {"ok": True, "原約": contract_id, "新約": new["合約編號"], "客戶": c["客戶"]}


def payment_invoice(payment_id: str, invoice_no: str, actor: str = "財務") -> dict:
    """開立發票（P0 → P1）— 人審動作。"""
    ps = [p for p in payment_rows() if p["款項編號"] == payment_id]
    if not ps:
        return {"error": f"找不到款項 {payment_id}"}
    p = ps[0]
    if p["狀態"] not in ("P0", "P4"):
        return {"error": f"{payment_id} 目前是 {p['狀態']}、只有排程中（P0）或逾期（P4）可開票"}
    if not invoice_no.strip():
        return {"error": "發票號為必填"}
    update_row(p["page_id"], {"狀態": select("P1"), "發票號": text(invoice_no.strip())})
    log_event(p["合約編號"] or "", f"款項 {payment_id} 開立發票 {invoice_no.strip()}（P{'4' if p['狀態']=='P4' else '0'} → P1）", actor)
    return {"ok": True, "款項編號": payment_id, "發票號": invoice_no.strip()}


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
    # 全清提示
    left = [x for x in payment_rows() if x["合約編號"] == p["合約編號"] and x["狀態"] != "P3"]
    return {"ok": True, "款項編號": payment_id, "實收日": d,
            "該約未收筆數": len(left), "note": "全部款項已收清、可結案（C6）" if not left else ""}


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
    received = sum((p["金額"] or 0) for p in payment_rows() if p["狀態"] == "P3")
    return {"未收款按月": dict(sorted(by_month.items())), "其中逾期": overdue,
            "未收合計": sum(by_month.values()), "已收合計": received}
