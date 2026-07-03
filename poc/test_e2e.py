"""端到端閉環驗收 — 一張合約從建檔走完全生命週期（打 HTTP 端點、與網頁同路徑）。

驗證點：建約 C0 → 推進 → C4 自動產生款項排程 → 未收清擋結案 →
開票 → 收款全清 → C6 結案 → C7 續約窗口 → 一鍵開新約回 C0（閉環）→ 事件留痕。

前置：uvicorn 已在 :8790 跑。執行：uv run test_e2e.py
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8790"
checks: list[tuple[str, bool]] = []


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.load(r)


def check(name, cond, detail=""):
    checks.append((name, bool(cond)))
    print(("  ✓ " if cond else "  ✗ ") + name + (f" — {detail}" if detail else ""))


def main():
    ev0 = len(get("/api/bootstrap")["events"])

    print("① 建約（C0）")
    r = post("/api/create", {"customer": "閉環測試株式會社", "amount": 120000,
                             "terms": 2, "first_due": "2026-08-01", "owner": "王小明"})
    check("建約成功", r.get("ok"), r.get("合約編號", r.get("error", "")))
    cid = r["合約編號"]

    print("② 推進 C0 → C3")
    for to in ["C1", "C2", "C3"]:
        r = post("/api/transition", {"contract_id": cid, "to_state": to})
        check(f"轉移 → {to}", r.get("ok"), r.get("error", ""))

    print("③ C4 回簽生效 — 自動產生款項排程")
    r = post("/api/transition", {"contract_id": cid, "to_state": "C4"})
    sched = r.get("schedule", {})
    check("轉移 → C4", r.get("ok"))
    check("自動產生 2 期款項", len(sched.get("produced", [])) == 2, "、".join(sched.get("produced", [])))
    pays = [p for p in get("/api/bootstrap")["payments"] if p["合約編號"] == cid]
    check("款項落 Notion（2 筆 P0）", len(pays) == 2 and all(p["狀態"] == "P0" for p in pays))
    check("金額拆分正確（60,000 × 2）", sum(p["金額"] for p in pays) == 120000)

    print("④ 終端不變量 — 未收清擋結案")
    post("/api/transition", {"contract_id": cid, "to_state": "C5"})
    r = post("/api/transition", {"contract_id": cid, "to_state": "C6"})
    check("未收清 → C6 被擋", "不能結案" in r.get("error", ""), r.get("error", "")[:60])

    print("⑤ 開票 → 收款全清")
    for i, p in enumerate(pays, 1):
        r = post("/api/invoice", {"payment_id": p["款項編號"], "invoice_no": f"E2E-{i:04d}"})
        check(f"開票 {p['款項編號']}", r.get("ok"), r.get("error", ""))
        r = post("/api/mark_paid", {"payment_id": p["款項編號"]})
        check(f"收款 {p['款項編號']}", r.get("ok"), r.get("note", r.get("error", "")))

    print("⑥ 結案 → 續約窗口 → 開新約（閉環）")
    r = post("/api/transition", {"contract_id": cid, "to_state": "C6"})
    check("全收清 → C6 結案", r.get("ok"), r.get("error", ""))
    r = post("/api/transition", {"contract_id": cid, "to_state": "C7"})
    check("→ C7 續約窗口", r.get("ok"))
    r = post("/api/renew", {"contract_id": cid})
    check("一鍵開新約", r.get("ok"), f"新約 {r.get('新約', '')}")
    new_id = r.get("新約")
    b = get("/api/bootstrap")
    nc = [c for c in b["contracts"] if c["合約編號"] == new_id]
    check("新約在 C0（閉環完成）", nc and nc[0]["狀態"] == "C0")

    print("⑦ 事件留痕")
    ev1 = len(b["events"])
    check(f"事件庫新增留痕（{ev0} → {ev1}）", ev1 > ev0)

    passed = sum(1 for _, ok in checks if ok)
    print(f"\n驗收：{passed}/{len(checks)} — " + ("PASS" if passed == len(checks) else "FAIL"))
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
