"""資料層 v2 遷移 — 產品目錄、評論庫、跨庫真關聯（relation）、既有資料回填。

冪等：notion_ids.json 已含 products 則跳過建庫；回填只補空缺。
執行：uv run migrate_v2.py
"""
import json

from notion_layer import IDS_FILE, api, load_ids, read_prop

ids = load_ids()
POC_PAGE = ids["poc_page"]


def make_db(name: str, props: dict) -> dict:
    t = [{"type": "text", "text": {"content": name}}]
    try:
        res = api("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": POC_PAGE},
            "title": t, "initial_data_source": {"properties": props}})
    except RuntimeError:
        res = api("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": POC_PAGE},
            "title": t, "properties": props})
    ds = (res.get("data_sources") or [{}])[0].get("id")
    return {"database_id": res["id"], "data_source_id": ds}


def relation_prop(target: dict) -> dict:
    """relation 屬性定義 — 新版（data_source_id）優先、呼叫端負責容錯退舊版。"""
    return {"relation": {"data_source_id": target["data_source_id"],
                         "type": "single_property", "single_property": {}}}


def relation_prop_legacy(target: dict) -> dict:
    return {"relation": {"database_id": target["database_id"],
                         "type": "single_property", "single_property": {}}}


def add_props(db: dict, props: dict):
    try:
        api("PATCH", f"/data_sources/{db['data_source_id']}", {"properties": props})
    except RuntimeError:
        api("PATCH", f"/databases/{db['database_id']}", {"properties": props})


def main():
    changed = False

    # 1. Products 產品目錄
    if "products" not in ids:
        ids["products"] = make_db("Products 產品目錄", {
            "產品名稱": {"title": {}},
            "類型": {"select": {"options": [{"name": s} for s in ["顧問服務", "標準產品", "訂閱服務", "客製專案", "教育訓練"]]}},
            "定價模式": {"select": {"options": [{"name": s} for s in ["固定價", "報價制", "訂閱制"]]}},
            "建議單價": {"number": {"format": "number_with_commas"}},
            "狀態": {"select": {"options": [{"name": s} for s in ["上架", "停售"]]}},
            "說明": {"rich_text": {}},
        })
        changed = True
        print("Products 庫建立:", ids["products"]["database_id"])
    else:
        print("Products 已存在、跳過")

    # 2. Comments 評論庫
    if "comments" not in ids:
        ids["comments"] = make_db("Comments 評論", {
            "留言": {"title": {}},
            "合約編號": {"rich_text": {}},
            "留言人": {"rich_text": {}},
            "時間": {"date": {}},
        })
        changed = True
        print("Comments 庫建立:", ids["comments"]["database_id"])
    else:
        print("Comments 已存在、跳過")

    if changed:
        IDS_FILE.write_text(json.dumps(ids, ensure_ascii=False, indent=2))

    # 3. 跨庫 relation 欄位（容錯：新舊 relation 定義格式）
    def ensure_rel(db_key: str, prop_name: str, target_key: str):
        db, target = ids[db_key], ids[target_key]
        try:
            add_props(db, {prop_name: relation_prop(target)})
            print(f"{db_key}.{prop_name} → {target_key} relation OK")
        except RuntimeError:
            try:
                add_props(db, {prop_name: relation_prop_legacy(target)})
                print(f"{db_key}.{prop_name} → {target_key} relation OK（舊格式）")
            except RuntimeError as e:
                print(f"{db_key}.{prop_name} relation 失敗:", str(e)[:120])

    ensure_rel("contracts", "產品", "products")
    ensure_rel("payments", "合約", "contracts")
    ensure_rel("events", "合約", "contracts")
    ensure_rel("comments", "合約", "comments" if False else "contracts")
    # Contracts 加來源報價單欄
    try:
        add_props(ids["contracts"], {"來源報價單": {"rich_text": {}}})
        print("contracts.來源報價單 OK")
    except RuntimeError as e:
        print("contracts.來源報價單:", str(e)[:100])

    # 4. 回填 relation（Payments / Events 的合約編號字串 → Contracts 頁）
    from notion_layer import query_db, update_row
    cmap = {}
    for r in query_db(ids["contracts"]):
        cid = next(("".join(t2.get("plain_text", "") for t2 in v["title"])
                    for v in r["properties"].values() if v["type"] == "title"), "")
        if cid:
            cmap[cid] = r["id"]
    for key in ["payments", "events"]:
        rows = query_db(ids[key])
        fixed = 0
        for r in rows:
            rel = r["properties"].get("合約", {})
            if rel.get("type") == "relation" and rel.get("relation"):
                continue  # 已有
            cid = read_prop(r, "合約編號")
            if cid and cid in cmap:
                try:
                    update_row(r["id"], {"合約": {"relation": [{"id": cmap[cid]}]}})
                    fixed += 1
                except RuntimeError:
                    pass
        print(f"{key} 回填 relation：{fixed}/{len(rows)}")

    print("遷移完成")


if __name__ == "__main__":
    main()
