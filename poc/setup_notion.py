"""建立 POC 資料層 v2 — 在指定父頁下建子頁 + 四個資料庫 + 示意資料（全虛構）。

v2（2026-07-03）：資料層落點改 Nelsen 私人區「Personal Notes」；合約 schema 加
「期數」「首期日」（供 C4 回簽生效時自動產生款項排程）。

冪等：notion_ids.json 已存在 → 中止、不重複建。
執行：uv run setup_notion.py
"""
import json

from notion_layer import IDS_FILE, api, create_row, date, number, select, text, title

PARENT_PAGE = "2a0b2192-4515-80a8-9406-dacd31417904"  # Personal Notes（Nelsen 私人區）


def make_db(parent_page: str, name: str, props: dict) -> dict:
    t = [{"type": "text", "text": {"content": name}}]
    try:
        res = api("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": parent_page},
            "title": t,
            "initial_data_source": {"properties": props},
        })
    except RuntimeError:
        res = api("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": parent_page},
            "title": t,
            "properties": props,
        })
    ds = (res.get("data_sources") or [{}])[0].get("id")
    return {"database_id": res["id"], "data_source_id": ds}


def main():
    if IDS_FILE.exists():
        ids = json.loads(IDS_FILE.read_text())
        print(f"ABORT: notion_ids.json 已存在（資料層頁 {ids.get('poc_page')}）— 要重建先處理舊頁與此檔")
        return

    page = api("POST", "/pages", {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": "BizPeak Flow — 資料層"}}]}},
        "children": [{"type": "callout", "callout": {
            "rich_text": [{"type": "text", "text": {"content": "BizPeak Flow 的資料層（憲法第一條：Notion 是唯一真相來源）。四庫皆由能力層讀寫 — 網頁介面、聊天助理、MCP 三個入口共用。示意資料全虛構。請勿手動改欄位結構（資料契約、詳 docs/CARTRIDGE-SPEC.md）。"}}],
            "icon": {"type": "emoji", "emoji": "🗄️"}}}],
    })
    poc_page = page["id"]
    print("資料層頁建立:", poc_page)

    contracts = make_db(poc_page, "Contracts 合約", {
        "合約編號": {"title": {}},
        "客戶": {"rich_text": {}},
        "狀態": {"select": {"options": [{"name": s} for s in
                 ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "X1", "X2"]]}},
        "負責業務": {"rich_text": {}},
        "金額": {"number": {"format": "number_with_commas"}},
        "期數": {"number": {}},
        "首期日": {"date": {}},
        "生效日": {"date": {}},
        "到期日": {"date": {}},
        "SLA 截止": {"date": {}},
    })
    payments = make_db(poc_page, "Payments 款項", {
        "款項編號": {"title": {}},
        "合約編號": {"rich_text": {}},
        "期數": {"rich_text": {}},
        "預計付款日": {"date": {}},
        "金額": {"number": {"format": "number_with_commas"}},
        "發票號": {"rich_text": {}},
        "狀態": {"select": {"options": [{"name": s} for s in ["P0", "P1", "P2", "P3", "P4"]]}},
        "實收日": {"date": {}},
    })
    events = make_db(poc_page, "Events 事件", {
        "事件": {"title": {}},
        "合約編號": {"rich_text": {}},
        "動作": {"rich_text": {}},
        "執行者": {"rich_text": {}},
        "時間": {"date": {}},
    })
    cartridges = make_db(poc_page, "Cartridges 卡帶註冊", {
        "卡帶": {"title": {}},
        "負責人": {"rich_text": {}},
        "等級": {"select": {"options": [{"name": s} for s in ["L0", "L1", "L2"]]}},
        "狀態": {"select": {"options": [{"name": s} for s in ["開發中", "運行中", "歸檔"]]}},
        "暴露能力": {"rich_text": {}},
    })
    print("四庫建立完成")

    demo_contracts = [
        ("CT-2026-041", "宏昇開發", "C5", "王小明", 720000, 3, "2026-04-15", "2025-12-01", "2026-11-30"),
        ("CT-2026-047", "祥豐置業", "C4", "王小明", 450000, 2, "2026-08-01", None, None),
        ("CT-2026-018", "景富資產管理", "C5", "李小華", 312000, 4, "2026-03-20", "2026-01-15", "2027-01-14"),
    ]
    for cid, cust, st, owner, amt, terms, first, start, end in demo_contracts:
        create_row(contracts, {
            "合約編號": title(cid), "客戶": text(cust), "狀態": select(st),
            "負責業務": text(owner), "金額": number(amt), "期數": number(terms),
            "首期日": date(first), "生效日": date(start), "到期日": date(end),
        })
    demo_payments = [
        ("PM-041-2", "CT-2026-041", "2/3", "2026-07-02", 240000, "KA-33018274", "P3", "2026-07-01"),
        ("PM-041-3", "CT-2026-041", "3/3", "2026-10-15", 240000, "", "P0", None),
        ("PM-018-3", "CT-2026-018", "3/4", "2026-06-20", 78000, "KA-33017902", "P4", None),
        ("PM-047-1", "CT-2026-047", "1/2", "2026-08-01", 225000, "", "P0", None),
    ]
    for pid, cid, term, due, amt, inv, st, paid in demo_payments:
        create_row(payments, {
            "款項編號": title(pid), "合約編號": text(cid), "期數": text(term),
            "預計付款日": date(due), "金額": number(amt), "發票號": text(inv),
            "狀態": select(st), "實收日": date(paid),
        })
    create_row(events, {
        "事件": title("EVT-0001"), "合約編號": text("CT-2026-018"),
        "動作": text("款項 PM-018-3 逾期、觸發催收梯級 D+7（催收信已起草待業務送出）"),
        "執行者": text("催收規則引擎"), "時間": date("2026-06-27"),
    })
    create_row(cartridges, {
        "卡帶": title("contract-lifecycle 合約生命週期"), "負責人": text("Allen Hung"),
        "等級": select("L2"), "狀態": select("開發中"),
        "暴露能力": text("contract_create / list / get / transition / renew、payment_invoice / mark_paid / overdue_list、cashflow_forecast"),
    })
    print("示意資料寫入完成（3 合約、4 款項、1 事件、1 卡帶）")

    IDS_FILE.write_text(json.dumps({
        "poc_page": poc_page, "contracts": contracts, "payments": payments,
        "events": events, "cartridges": cartridges,
    }, ensure_ascii=False, indent=2))
    print("ids 已寫入", IDS_FILE)
    print("資料層頁：https://www.notion.so/" + poc_page.replace("-", ""))


if __name__ == "__main__":
    main()
