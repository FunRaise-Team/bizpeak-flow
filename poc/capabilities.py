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
            "各期金額": read_prop(r, "各期金額"),
            "來源報價單": read_prop(r, "來源報價單"),
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
                    owner: str = "", expiry: str = "", actor: str = "使用者",
                    per_term_amounts: str = "") -> dict:
    """建立合約（C0 報價草稿）— 閉環的起點。per_term_amounts 各期金額（逗號分隔或百分比、可空=均分）。"""
    if not customer or not amount:
        return {"error": "客戶與金額為必填"}
    if terms < 1 or terms > 12:
        return {"error": "期數需在 1–12 之間"}
    if per_term_amounts:
        parsed = _parse_amounts(per_term_amounts, amount, terms)
        if isinstance(parsed, dict):
            return parsed
    cid = _next_contract_id()
    owner_name = owner or actor.replace("（經助理）", "")
    props = {
        "合約編號": title(cid), "客戶": text(customer), "狀態": select("C0"),
        "負責業務": text(owner_name), "金額": number(amount), "期數": number(terms),
        "首期日": date(first_due or None), "到期日": date(expiry or None),
        "狀態進入日": date(_date.today().isoformat()),
    }
    if per_term_amounts:
        props["各期金額"] = text(per_term_amounts)
    uid = owner_user_id(owner_name)
    if uid:
        props["負責人"] = {"people": [{"id": uid}]}
    create_row(_contracts(), props)
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
    custom = []
    raw = c.get("各期金額") or ""
    if raw:
        parsed = _parse_amounts(raw, amount, terms)
        if isinstance(parsed, list) and parsed:
            custom = parsed
    base = round(amount / terms, 0)
    d0 = _date.fromisoformat(first)
    made = []
    for i in range(terms):
        amt = custom[i] if custom else (amount - base * (terms - 1) if i == terms - 1 else base)
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
        rich = [{"type": "text", "text": {"content": f"{actor}："}}] + mention_rich_text(content.strip())
        _api("POST", "/comments", {"parent": {"page_id": c["page_id"]}, "rich_text": rich})
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


# ── Co-Evo 報價產生（整合自 funraise-co-evo-quotation 外掛、業務免各自分支） ──

COEVO_PLANS = {
    "Starter": {"build": 3000, "annual": 19800, "pages": "300 頁", "chats": "100,000 次/月",
                "history": "30 天", "crawl": "每三個月 1 次", "manual": "✕", "questions": "最多 4 題",
                "report": "✕", "extra": []},
    "Growth": {"build": 6000, "annual": 35800, "pages": "300 頁", "chats": "250,000 次/月",
               "history": "90 天", "crawl": "每月 1 次", "manual": "2 次/月", "questions": "最多 6 題",
               "report": "每季一次", "extra": ["行銷優惠券模組"]},
    "Pro": {"build": 10000, "annual": 58800, "pages": "300 頁", "chats": "500,000 次/月",
            "history": "180 天", "crawl": "每週 1 次（客戶指定）", "manual": "5 次/月", "questions": "最多 6 題",
            "report": "每月一次", "extra": ["行銷優惠券模組", "對話資料匯出", "移除「Powered by 方睿」品牌客製"]},
}
QUOTE_DB_ID = "302b2192-4515-804b-8a56-ffaf847ebbdf"
QUOTE_EDIT = "https://funraise-quote-bsc.vercel.app/edit?id="
CRM_DS = "b4a6a57b-e0bf-42e7-92cc-f4978bf8fc8f"
_COEVO_TERMS = """### 備註
1. 報價效力與簽署
- 本報價單視同正式合約，經客戶簽署回傳（或數位簽章）後即生效，雙方應受本報價單載明之權利義務規範。
- 本報價單有效期限為開立日起 14 日內，逾期本公司保留調整價格與服務內容之權利。
2. 付款條件
- 本方案費用（建置費 + 首年年費，含客製項目）於合約簽訂後一次性支付 100%。
- 本公司於合約簽訂後開立發票，客戶應於發票開立日起 30 日內完成付款（票期 30 天）；營業稅 5% 外加。
3. 服務內容與額度說明
- 服務範圍、月對話次數額度、爬蟲頁數與頻率、對話歷史保存天數等，以上方報價項目所載之方案內容為準。
- 月對話次數額度於每月重置；當月額度用盡時，系統將暫停對話服務至次月重置（不會產生超額費用）。如有持續需求，可升級至更高方案，補繳兩方案年費差額後即取得新方案完整額度。
- 建置服務包含官網接入、Starter Questions 設定與部署上線；建置完成後之大幅內容調整或新增功能，以人時或另案計價。
4. 不含項目
- 報價項目未列明之功能、頁面或模組；客戶官網改版、第三方服務費（簡訊、Email、金流、LINE 推播等）由客戶依平台帳單自行負擔。
- 視覺素材與既有官網內容由客戶提供，不含於本報價。
5. 雲端與 AI 運算資源
- 提供本服務所需之 AI 模型呼叫、雲端主機與運算資源（Claude API、GCP、Vercel 等）費用，於方案額度範圍內均已包含於年費，客戶不另行負擔。
6. 服務期間與續約
- 本服務合約期間為一年，自帳號開通日起算；爬蟲更新、Lead 自動轉遞、24 小時服務與持續優化於服務期間內提供。
- 合約期間內如進行方案升級，合約到期日將自升級日起重新計算 12 個月。
- 合約期滿前 30 日，雙方重新評估次期合作需求並另行協議續約年費。
7. 系統維運與持續優化
- 年費已涵蓋全年度系統維運、版本更新與持續優化，並提供工作日線上技術支援服務。
8. 報價機密性
- 本報價單及其所載之價格、服務內容與商業條件均屬商業機密，未經本公司書面同意，客戶不得對外揭露或提供予任何第三方。
9. 中途終止與退費
- 合約簽訂並開通帳號後，除經雙方書面（含電子郵件）同意之特殊情況，客戶不得中途取消服務，已收款項不予退還。
10. 使用規範與免責聲明
- 本服務僅供客戶就其合法經營之業務進行對話導流與名單蒐集，嚴禁用於違法、詐欺、散布不實資訊或侵害第三人權利之用途。
- 如客戶違反使用規範（包括但不限於惡意使用、危害系統安全、將帳號提供予未授權之第三方使用、上傳違法內容等），本公司有權逕行暫停或終止服務，且不負退費義務。
- 本公司已取得提供本服務所需之一切合法授權。AI 對話內容係由模型自動生成，本公司已盡合理努力確保品質，惟不保證內容絕對無誤，客戶應自行審酌對外揭露之資訊。
11. 資料權源與個人資料保護
- 客戶保證所提供及合作過程涉及之資料（含官網內容、表單欄位設計）均具合法取得權源，無違反法令或侵害第三人權利之情事。
- 雙方應依「個人資料保護法」及相關法規辦理個人資料之蒐集、處理與利用。透過本服務蒐集之對話紀錄與名單，本公司僅於提供服務之目的範圍內處理，不作其他用途。
12. 遲延付款
- 如客戶逾期未付款，應自逾期日起按年息百分之二計算遲延利息。逾期超過 60 日仍未付款者，本公司有權暫停服務至款項清償為止。
13. 賠償責任上限
- 本公司因本服務所生之損害賠償責任，以該年度已收取之服務費用總額為上限。前述限制不適用於因故意或重大過失所致之損害。
14. 不可抗力
- 因天災、火災、水災、戰爭、罷工、傳染病、暴動、政府法令變更、媒體平台或 AI 服務供應商政策調整或其他不可歸責於雙方之事由，致無法履行本報價單所定義務者，免負損害賠償責任。受影響之一方應立即通知他方，並敘明詳情。
15. 智慧財產權
- 本報價範圍為雲端 SaaS 平台服務，Co-Evo 平台之核心程式碼、AI 模型及演算法之智慧財產權歸方睿科技所有。客戶擁有平台使用權（於授權期間內）及透過本服務蒐集之對話紀錄與名單資料之完整所有權。
16. 報價單變更與條款可分離性
- 關於本報價單內容之任何更正或修改，皆須經雙方書面（含電子郵件）協議，否則不生效力。
- 本報價單中任何條款如與相關法令牴觸而歸於無效者，僅該牴觸之部分無效，其餘條款仍具完全效力，不受影響。
17. 準據法與管轄法院
- 本報價單之解釋與適用，以中華民國法律為準據法。雙方因本報價單所生之爭議，應本於誠信原則協商解決；如未能於合理期間內達成共識而涉訟時，雙方同意以臺灣臺北地方法院為第一審管轄法院。"""


def _crm_contact(customer: str) -> dict:
    """CRM 查客戶窗口（容錯 — 查不到留空、不阻斷報價）。"""
    try:
        from notion_layer import api
        res = api("POST", f"/data_sources/{CRM_DS}/query", {"page_size": 100})
        for r in res["results"]:
            props = r["properties"]
            comp = ""
            for k, v in props.items():
                if "公司" in k and v.get("type") == "rich_text":
                    comp = "".join(t.get("plain_text", "") for t in v["rich_text"])
                    break
            if comp and (customer in comp or comp in customer):
                nm = next(("".join(t.get("plain_text", "") for t in v["title"])
                           for v in props.values() if v["type"] == "title"), "")
                return {"公司全名": comp, "窗口": nm}
    except RuntimeError:
        pass
    return {}


def _next_quote_no() -> str:
    today = _date.today().isoformat()
    prefix = f"FR-Q-{today}"
    mx = 0
    for q in quote_rows():
        no = q.get("報價單號") or ""
        if no.startswith(prefix) and no.endswith("SSIC"):
            try:
                mx = max(mx, int(no.split("-")[5]))
            except (IndexError, ValueError):
                pass
    return f"{prefix}-{mx + 1:03d}-SSIC"


def quote_create(customer: str, plan: str = "Growth", owner: str = "",
                 discount_untaxed: float | None = None, actor: str = "使用者") -> dict:
    """建立 Co-Evo 報價單（寫公司報價庫、與報價前端相容的 v4 格式）— 整合自報價外掛。"""
    plan = plan.strip().capitalize()
    if plan not in COEVO_PLANS:
        return {"error": f"方案需為 Starter / Growth / Pro（收到「{plan}」）"}
    if not customer.strip():
        return {"error": "客戶名稱必填"}
    from notion_layer import api
    from datetime import timedelta as _td
    p = COEVO_PLANS[plan]
    total = p["build"] + p["annual"]
    qno = _next_quote_no()
    today = _date.today()
    crm = _crm_contact(customer)
    comp = crm.get("公司全名") or customer.strip()
    owner = owner or actor.replace("（經助理）", "")

    props = {
        "名稱": {"title": [{"type": "text", "text": {"content": f"{customer.strip()}-Co-Evo {plan}"}}]},
        "報價單號": {"rich_text": [{"type": "text", "text": {"content": qno}}]},
        "報價日期": {"rich_text": [{"type": "text", "text": {"content": f"{today.year} 年 {today.month:02d} 月 {today.day:02d} 日"}}]},
        "客戶名稱": {"rich_text": [{"type": "text", "text": {"content": comp}}]},
        "案型": {"select": {"name": "Co-Evo"}},
        "狀態": {"select": {"name": "草稿"}},
        "報價金額": {"number": total},
        "部門": {"select": {"name": "SSIC"}},
        "有效期限": {"date": {"start": (today + _td(days=14)).isoformat()}},
        "版本號": {"number": 0},
        "報價負責人": {"rich_text": [{"type": "text", "text": {"content": owner}}]},
    }
    if discount_untaxed:
        props["優惠價"] = {"number": round(discount_untaxed * 1.05)}
    page = api("POST", "/pages", {"parent": {"type": "database_id", "database_id": QUOTE_DB_ID}, "properties": props})

    extras_build = "\n".join(f"- {x}" for x in p["extra"] if "品牌" in x)
    extras_annual = "\n".join(f"- {x}" for x in p["extra"] if "品牌" not in x)
    fm_discount = f"\n專案優惠價: {round(discount_untaxed * 1.05)}" if discount_untaxed else ""
    v4 = f"""---
專案名稱: {customer.strip()} Co-Evo {plan} 導入專案
報價單號: {qno}
日期: {today.year} 年 {today.month:02d} 月 {today.day:02d} 日
報價方: 方睿科技股份有限公司
統編: 00225692
地址: 台北市松山區民權東路三段170號
專案負責人: {owner}
客戶公司: {comp}
客戶窗口: {crm.get('窗口', '')}{fm_discount}
---
## Co-Evo {plan} 建置費 | 1 | {p['build']}
- 一次性官網接入與設定
- 爬蟲頁數 {p['pages']}
{extras_build}
## Co-Evo {plan} 首年年費 | 1 | {p['annual']}
- 月對話 {p['chats']}
- 對話歷史保存 {p['history']}
- 自動爬蟲 {p['crawl']}
- 手動觸發 {p['manual']}
- 對話分析報告 {p['report']}
- Starter Questions {p['questions']}
{extras_annual}
{_COEVO_TERMS}"""
    v4 = "\n".join(l for l in v4.splitlines() if l.strip() != "")
    # 前端解析需要逐字保留 v4 標記 → 包 code block（多段 rich_text、各 ≤1900 字）
    chunks = [v4[i:i + 1900] for i in range(0, len(v4), 1900)]
    api("PATCH", f"/blocks/{page['id']}/children", {"children": [{
        "type": "code", "code": {"language": "javascript",
            "rich_text": [{"type": "text", "text": {"content": c}} for c in chunks]}}]})
    _co_cache.pop("quotes", None)
    log_event("", f"建立 Co-Evo 報價單 {qno}（{customer.strip()}、{plan}、未稅 {total:,}）", actor)
    return {"ok": True, "報價單號": qno, "客戶": comp, "方案": plan,
            "首年總計未稅": total, "編輯連結": QUOTE_EDIT + page["id"].replace("-", "")}


# ── 人員屬性 / @ 提及 / 各期金額 / 演示模式（v7） ──

def notion_users() -> dict:
    """姓名 → Notion 使用者編號（艦員名冊姓名 ↔ workspace 成員互相比對）。快取 10 分鐘。"""
    def fetch():
        from notion_layer import api
        out = {}
        try:
            res = api("GET", "/users?page_size=100")
            for u in res.get("results", []):
                if u.get("type") == "person" and u.get("name"):
                    out[u["name"]] = u["id"]
        except RuntimeError:
            pass
        return out
    return _cached("nusers", 600, fetch)


def owner_user_id(name: str) -> str | None:
    """找同事對應的 Notion 使用者（全名互含比對、例「Kyle Lu」↔「呂哲源 Kyle Lu」）。"""
    if not name:
        return None
    users = notion_users()
    if name in users:
        return users[name]
    for un, uid in users.items():
        if un and (un in name or name in un):
            return uid
    return None


def mention_rich_text(content: str) -> list:
    """把內容中的 @姓名 轉成 Notion 提及（真的會通知本人）；其餘保留文字。"""
    import re
    parts, last = [], 0
    for m in re.finditer(r"@([\w一-鿿.\- ]{1,20}?)(?=[\s,，。;；!！?？@]|$)", content):
        uid = owner_user_id(m.group(1).strip())
        if not uid:
            continue
        if m.start() > last:
            parts.append({"type": "text", "text": {"content": content[last:m.start()]}})
        parts.append({"type": "mention", "mention": {"user": {"id": uid}}})
        last = m.end()
    if last < len(content):
        parts.append({"type": "text", "text": {"content": content[last:]}})
    return parts or [{"type": "text", "text": {"content": content}}]


def _parse_amounts(amounts: str, total: float, terms: int) -> list[float] | dict:
    """各期金額解析 —「300000,300000,400000」或「30%,30%,40%」；驗筆數與總和。"""
    vals = [a.strip() for a in (amounts or "").replace("，", ",").split(",") if a.strip()]
    if not vals:
        return []
    if len(vals) != terms:
        return {"error": f"各期金額有 {len(vals)} 筆、但期數是 {terms} — 兩者要一致"}
    try:
        if all(v.endswith("%") for v in vals):
            nums = [round(total * float(v[:-1]) / 100) for v in vals]
            nums[-1] = total - sum(nums[:-1])
        else:
            nums = [float(v) for v in vals]
    except ValueError:
        return {"error": "各期金額格式：逗號分隔的數字（或百分比、如 30%,30%,40%）"}
    if abs(sum(nums) - total) > 1:
        return {"error": f"各期金額合計 {sum(nums):,.0f} ≠ 合約金額 {total:,.0f}"}
    return nums


def demo_lifecycle(actor: str = "演示模式", cleanup: bool = True) -> dict:
    """完整流程演示 — 建一張【演示】合約走完全生命週期（含不均分款項、開票、收款、
    守門展示、結案、續約開新約）、預設結束後全部清掉。給「教我怎麼用」的實地展示。"""
    from datetime import timedelta as _td
    steps: list[str] = []
    demo_ids: list[str] = []
    r = contract_create("【演示】示範客戶股份有限公司", 100000, 2,
                        (_date.today() + _td(days=30)).isoformat(), actor, "", actor=actor)
    if not r.get("ok"):
        return r
    cid = r["合約編號"]; demo_ids.append(cid)
    steps.append(f"① 建約 {cid}（C0 報價草稿、10 萬、2 期）")
    # 設定不均分：40% / 60%
    cs = [c for c in contract_rows() if c["合約編號"] == cid][0]
    update_row(cs["page_id"], {"各期金額": text("40000,60000")})
    steps.append("② 設定各期金額 40,000 / 60,000（不均分、對應開票）")
    for st, note in [("C1", "③ 送內部簽核"), ("C2", "④ 簽核完成、用印"), ("C3", "⑤ 寄出待客戶回簽")]:
        contract_transition(cid, st, actor=actor)
        steps.append(note)
    r4 = contract_transition(cid, "C4", actor=actor)
    made = (r4.get("schedule") or {}).get("produced", [])
    steps.append(f"⑥ 回簽生效 → 自動產生款項排程 {len(made)} 期（金額照 40,000/60,000）")
    gate = contract_transition(cid, "C5", actor=actor) and contract_transition(cid, "C6", actor=actor)
    steps.append(f"⑦ 試著直接結案 → 被擋：「{gate.get('error', '')[:40]}…」（款項未收清不能結案）")
    for i, p in enumerate([x for x in payment_rows() if x["合約編號"] == cid], 1):
        payment_invoice(p["款項編號"], f"DEMO-{i:04d}", actor=actor)
        payment_mark_paid(p["款項編號"], actor=actor)
    steps.append("⑧ 逐期開發票、確認收款（兩期金額不同、發票各開各的）")
    contract_transition(cid, "C6", actor=actor)
    steps.append("⑨ 全收清 → 結案通過")
    contract_transition(cid, "C7", actor=actor)
    rn = contract_renew(cid, actor=actor)
    new_id = rn.get("新約", "")
    if new_id:
        demo_ids.append(new_id)
    steps.append(f"⑩ 續約窗口 → 一鍵開新約 {new_id}（條件沿用、回到 C0、閉環完成）")
    cleaned = 0
    if cleanup:
        from notion_layer import api
        for did in demo_ids:
            for c in [x for x in contract_rows() if x["合約編號"] == did]:
                api("PATCH", f"/pages/{c['page_id']}", {"in_trash": True}); cleaned += 1
            for p in [x for x in payment_rows() if x["合約編號"] == did]:
                api("PATCH", f"/pages/{p['page_id']}", {"in_trash": True}); cleaned += 1
        from notion_layer import query_db
        for e in query_db(load_ids()["events"]):
            if (read_prop(e, "合約編號") or "") in demo_ids:
                api("PATCH", f"/pages/{e['id']}", {"in_trash": True}); cleaned += 1
        steps.append(f"⑪ 演示資料已清理（封存 {cleaned} 筆）— 系統回到演示前狀態")
    return {"ok": True, "steps": steps, "演示合約": demo_ids, "已清理": cleanup}
