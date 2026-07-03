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
            "狀態進入日": read_prop(r, "狀態進入日"),
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
        "狀態進入日": date(_date.today().isoformat()),
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
    update_row(c["page_id"], {"狀態": select(to_state), "狀態進入日": date(_date.today().isoformat())})
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


# ── 公司既有資料串接（客戶大名單 / 報價系統）──

COMPANY_DS = {
    "customers": "2a9b2192-4515-8189-a6c1-000b3d43763f",   # 生態系合作廠商大名單
    "quotes": "302b2192-4515-8077-8d4c-000b65889864",       # 報價 DB（funraise-sales-skills）
    "crew": "3455dbc4-a4ce-4144-bcf5-542d524def1d",         # 艦員名冊（同事正源）
}
_co_cache: dict = {}


def _cached(key, ttl, fn):
    import time as _t
    hit = _co_cache.get(key)
    if hit and _t.time() - hit[0] < ttl:
        return hit[1]
    val = fn()
    _co_cache[key] = (_t.time(), val)
    return val


def notion_url(page_id: str) -> str:
    return "https://www.notion.so/" + (page_id or "").replace("-", "")


def customer_list() -> list[dict]:
    """公司客戶主資料（生態系合作廠商大名單）— 名稱 + Account Owner。快取 5 分鐘。"""
    def fetch():
        from notion_layer import api
        out, cursor = [], None
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            res = api("POST", f"/data_sources/{COMPANY_DS['customers']}/query", body)
            for r in res["results"]:
                nm = next(("".join(t.get("plain_text", "") for t in v["title"])
                           for v in r["properties"].values() if v["type"] == "title"), "")
                own = r["properties"].get("Account Owner", {})
                owner = ""
                if own.get("type") == "people" and own["people"]:
                    owner = own["people"][0].get("name", "")
                elif own.get("type") == "rich_text":
                    owner = "".join(t.get("plain_text", "") for t in own["rich_text"])
                if nm and not nm.startswith("🖼"):
                    out.append({"name": nm, "owner": owner})
            if not res.get("has_more"):
                break
            cursor = res["next_cursor"]
        return sorted(out, key=lambda x: x["name"])
    return _cached("customers", 300, fetch)


def staff_list() -> list[str]:
    """同事名單 — 正源：艦員名冊（在職）；讀不到時退回 Account Owner ∪ 報價負責人。"""
    def fetch():
        try:
            from notion_layer import api
            names = []
            res = api("POST", f"/data_sources/{COMPANY_DS['crew']}/query", {"page_size": 100})
            for r in res["results"]:
                nm = read_prop(r, "姓名") or ""
                status = read_prop(r, "狀態") or ""
                code = next(("".join(t.get("plain_text", "") for t in v["title"])
                             for v in r["properties"].values() if v["type"] == "title"), "")
                if not nm or "TEST" in code.upper() or code == "F9999":
                    continue
                if status and any(k in status for k in ("離職", "停用", "停職")):
                    continue
                names.append(nm)
            if names:
                return sorted(set(names))
        except RuntimeError:
            pass
        names = {c["owner"] for c in customer_list() if c["owner"]}
        for q in quote_rows():
            if q["報價負責人"]:
                names.add(q["報價負責人"])
        return sorted(names)
    return _cached("staff", 300, fetch)


def quote_rows() -> list[dict]:
    """報價 DB 原始列（快取 60 秒）。"""
    def fetch():
        from notion_layer import api
        res = api("POST", f"/data_sources/{COMPANY_DS['quotes']}/query", {"page_size": 100})
        out = []
        for r in res["results"]:
            p = r["properties"]
            def rd(name):
                v = p.get(name, {})
                t = v.get("type")
                if t == "title": return "".join(x.get("plain_text", "") for x in v["title"])
                if t == "rich_text": return "".join(x.get("plain_text", "") for x in v["rich_text"])
                if t in ("select", "status"): return (v.get(t) or {}).get("name")
                if t == "number": return v.get("number")
                if t == "url": return v.get("url")
                if t == "people": return (v["people"][0].get("name", "") if v.get("people") else "")
                return None
            out.append({
                "page_id": r["id"],
                "報價單號": rd("報價單號"), "客戶名稱": rd("客戶名稱"),
                "狀態": rd("狀態"), "報價金額": rd("報價金額"), "優惠價": rd("優惠價"),
                "報價負責人": rd("報價負責人"), "部門": rd("部門"),
                "報價單連結": rd("報價單連結") or rd("審核連結"),
            })
        return out
    return _cached("quotes", 60, fetch)


READY_STATES = {"已簽約", "已核准", "已用印"}


def quote_ready_list() -> list[dict]:
    """可建約的報價單（狀態已簽約 / 已核准 / 已用印）、標記是否已匯入過。"""
    imported = set()
    for e in event_rows(200):
        a = e.get("動作") or ""
        if "報價單匯入" in a:
            for tok in a.split():
                if tok.startswith("FR-Q-"):
                    imported.add(tok.rstrip("、）("))
    out = []
    for q in quote_rows():
        if (q["狀態"] or "") in READY_STATES and q["報價單號"]:
            out.append({**q, "已匯入": q["報價單號"] in imported,
                        "notion_url": notion_url(q["page_id"])})
    return out


def quote_import(quote_no: str, terms: int = 1, first_due: str = "", actor: str = "使用者") -> dict:
    """從已簽約報價單一鍵建約（C0）— 帶入客戶、金額（優惠價優先）、負責人、留報價單號關聯。"""
    qs = [q for q in quote_rows() if q["報價單號"] == quote_no]
    if not qs:
        return {"error": f"找不到報價單 {quote_no}"}
    q = qs[0]
    if (q["狀態"] or "") not in READY_STATES:
        return {"error": f"報價單 {quote_no} 狀態為「{q['狀態']}」— 已簽約 / 已核准 / 已用印才能建約"}
    amount = q["優惠價"] or q["報價金額"] or 0
    r = contract_create(q["客戶名稱"] or "（報價單未填客戶）", amount, terms, first_due,
                        q["報價負責人"] or "", "", actor=actor)
    if not r.get("ok"):
        return r
    log_event(r["合約編號"], f"報價單匯入 {quote_no} → 建約（{q['客戶名稱']}、{amount:,.0f}、負責人 {q['報價負責人']}）", actor)
    return {"ok": True, "合約編號": r["合約編號"], "報價單號": quote_no,
            "客戶": q["客戶名稱"], "金額": amount}


# ── 產品目錄 / 評論 / 身份鏈（v3） ──

def _products(): return load_ids()["products"]
def _comments(): return load_ids()["comments"]


def product_list() -> list[dict]:
    """產品目錄（資料庫與介面兩邊都能調 — 這裡讀、介面與 Notion 都可寫）。"""
    def fetch():
        out = []
        for r in query_db(_products()):
            out.append({
                "page_id": r["id"],
                "產品名稱": read_prop(r, "產品名稱"),
                "類型": read_prop(r, "類型"),
                "定價模式": read_prop(r, "定價模式"),
                "建議單價": read_prop(r, "建議單價"),
                "狀態": read_prop(r, "狀態") or "上架",
                "說明": read_prop(r, "說明"),
            })
        out.sort(key=lambda x: (x["類型"] or "", x["產品名稱"] or ""))
        return out
    return _cached("products", 60, fetch)


def product_create(name: str, ptype: str = "顧問服務", pricing: str = "報價制",
                   price: float | None = None, note: str = "", actor: str = "使用者") -> dict:
    if not name.strip():
        return {"error": "產品名稱必填"}
    props = {"產品名稱": title(name.strip()), "類型": select(ptype),
             "定價模式": select(pricing), "狀態": select("上架"), "說明": text(note)}
    if price:
        props["建議單價"] = number(price)
    create_row(_products(), props)
    _co_cache.pop("products", None)
    log_event("", f"產品目錄新增：{name.strip()}（{ptype}・{pricing}）", actor)
    return {"ok": True, "產品名稱": name.strip()}


def comment_add(contract_id: str, content: str, actor: str = "使用者") -> dict:
    """合約留言 — 寫評論庫（含關聯）＋ 同步為該合約 Notion 頁的原生留言 ＋ 事件留痕。"""
    if not content.strip():
        return {"error": "留言內容必填"}
    cs = [c for c in contract_rows() if c["合約編號"] == contract_id]
    if not cs:
        return {"error": f"找不到合約 {contract_id}"}
    c = cs[0]
    from datetime import datetime as _dt
    create_row(_comments(), {
        "留言": title(content.strip()[:80]),
        "合約編號": text(contract_id), "留言人": text(actor),
        "時間": {"date": {"start": _dt.now().isoformat()}},
        "合約": {"relation": [{"id": c["page_id"]}]},
    })
    notion_comment = False
    try:
        from notion_layer import api as _api
        _api("POST", "/comments", {"parent": {"page_id": c["page_id"]},
             "rich_text": [{"type": "text", "text": {"content": f"{actor}：{content.strip()}"}}]})
        notion_comment = True
    except RuntimeError:
        pass  # 整合未開留言能力 — 評論庫仍有完整記錄
    log_event(contract_id, f"留言：{content.strip()[:60]}", actor)
    return {"ok": True, "合約編號": contract_id, "notion_comment": notion_comment}


def comment_list(contract_id: str = "") -> list[dict]:
    out = []
    for r in query_db(_comments()):
        cid = read_prop(r, "合約編號")
        if contract_id and cid != contract_id:
            continue
        out.append({"合約編號": cid, "留言人": read_prop(r, "留言人"),
                    "內容": read_prop(r, "留言"), "時間": read_prop(r, "時間")})
    out.sort(key=lambda x: x["時間"] or "", reverse=True)
    return out


def overdue_lazy_flag(actor: str = "催收規則引擎") -> int:
    """過期未收（P0/P1/P2 且過預計付款日）→ 標記 P4 並留痕。回傳更新筆數。"""
    t = _date.today().isoformat()
    n = 0
    for p in payment_rows():
        if p["狀態"] in ("P0", "P1", "P2") and p["預計付款日"] and p["預計付款日"] < t:
            update_row(p["page_id"], {"狀態": select("P4")})
            log_event(p["合約編號"] or "", f"款項 {p['款項編號']} 逾期（預計 {p['預計付款日']}）→ 標記 P4、進催收梯級", actor)
            n += 1
    return n


def renewal_alerts(days: int = 60) -> list[dict]:
    """續約窗口偵測 — 到期日在 N 天內、且尚未進續約流程（C5/C6）。讀取時動態計算、免排程器。"""
    from datetime import timedelta as _td
    t = _date.today()
    out = []
    for c in contract_rows():
        if c["狀態"] not in ("C5", "C6") or not c["到期日"]:
            continue
        try:
            exp = _date.fromisoformat(c["到期日"])
        except ValueError:
            continue
        left = (exp - t).days
        if left <= days:
            out.append({"合約編號": c["合約編號"], "客戶": c["客戶"], "到期日": c["到期日"],
                        "剩餘天數": left, "狀態": c["狀態"]})
    out.sort(key=lambda x: x["剩餘天數"])
    return out
