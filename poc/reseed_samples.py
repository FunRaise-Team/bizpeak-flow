"""樣本資料重造 — 封存舊資料、種全狀態多樣態資料集（訪談演示用、客戶皆虛構）。

覆蓋：C0-C7 全狀態、X1 作廢、時限內/超時、逾期多梯級、多期款項散佈 5-11 月、
產品關聯、真同事負責人、留言與操作歷史。執行：uv run reseed_samples.py
"""
from datetime import date, timedelta

import capabilities as cap
import notion_layer as nl

ids = nl.load_ids()
T = date.today()


def d(days: int) -> str:
    return (T + timedelta(days=days)).isoformat()


def archive_all(db_key: str) -> int:
    n = 0
    for r in nl.query_db(ids[db_key]):
        nl.api("PATCH", f"/pages/{r['id']}", {"in_trash": True})
        n += 1
    return n


def main():
    print("① 封存舊樣本…")
    for k in ["contracts", "payments", "events", "comments"]:
        print(f"  {k}: 封存 {archive_all(k)} 筆")

    prod = {p["產品名稱"]: p["page_id"] for p in cap.product_list()}
    P_COEVO = prod.get("Co-Evo 智慧互動導航")
    P_LEDGER = prod.get("智慧產權清冊助理")
    P_CUSTOM = prod.get("客製開發服務")
    P_EDU = prod.get("教育訓練・AI 導入工作坊")

    print("② 種合約…")
    # (編號, 客戶, 狀態, 負責人, 金額, 期數, 首期日, 生效日, 到期日, 狀態進入日, 產品, 來源報價單)
    contracts = [
        ("CT-2026-101", "威宇物業", "C0", "Jason Chang", 360000, 2, d(29), None, None, d(0), P_COEVO, ""),
        ("CT-2026-102", "亞泰開發", "C1", "Philis Chen", 520000, 1, d(45), None, None, d(-1), P_CUSTOM, ""),
        ("CT-2026-103", "京華資產", "C1", "Kyle Lu", 880000, 2, d(40), None, None, d(-6), P_LEDGER, ""),
        ("CT-2026-104", "日盛物流", "C2", "Jason Chang", 240000, 1, d(35), None, None, d(0), P_COEVO, ""),
        ("CT-2026-105", "宏遠建設", "C3", "Philis Chen", 1500000, 3, d(25), None, None, d(-9), P_CUSTOM, ""),
        ("CT-2026-106", "聯京商用", "C4", "Amanda Chou", 600000, 2, d(43), d(0), d(365), d(0), P_COEVO, ""),
        ("CT-2026-107", "中鼎租賃", "C5", "Jeff Hsieh", 960000, 4, d(-110), d(-140), d(225), d(-49), P_LEDGER, ""),
        ("CT-2026-108", "恆星超市", "C5", "Amanda Chou", 450000, 2, d(-32), d(-40), d(325), d(-32), P_COEVO, ""),
        ("CT-2026-109", "詠信顧問", "C6", "Jason Chang", 300000, 1, d(-300), d(-327), d(38), d(-14), P_EDU, ""),
        ("CT-2026-110", "開元保全", "C7", "Kyle Lu", 420000, 1, d(-330), d(-348), d(17), d(-3), P_COEVO, ""),
        ("CT-2026-111", "宏圖印刷（洽談中止）", "X1", "Jeff Hsieh", 120000, 1, None, None, None, d(-20), P_COEVO, ""),
    ]
    cmap = {}
    for cid, cust, st, owner, amt, terms, first, eff, exp, entered, pp, src in contracts:
        props = {
            "合約編號": nl.title(cid), "客戶": nl.text(cust), "狀態": nl.select(st),
            "負責業務": nl.text(owner), "金額": nl.number(amt), "期數": nl.number(terms),
            "首期日": nl.date(first), "生效日": nl.date(eff), "到期日": nl.date(exp),
            "狀態進入日": nl.date(entered),
        }
        if pp:
            props["產品"] = {"relation": [{"id": pp}]}
        if src:
            props["來源報價單"] = nl.text(src)
        r = nl.create_row(ids["contracts"], props)
        cmap[cid] = r["id"]
        print(f"  {cid} {cust} {st}")

    print("③ 種款項…")
    # (款項編號, 合約, 期, 預計日, 金額, 發票, 狀態, 實收)
    payments = [
        ("PM-106-1", "CT-2026-106", "1/2", d(43), 300000, "", "P0", None),
        ("PM-106-2", "CT-2026-106", "2/2", d(134), 300000, "", "P0", None),
        ("PM-107-1", "CT-2026-107", "1/4", d(-110), 240000, "QA-55201101", "P3", d(-108)),
        ("PM-107-2", "CT-2026-107", "2/4", d(-79), 240000, "QA-55201188", "P3", d(-75)),
        ("PM-107-3", "CT-2026-107", "3/4", d(-38), 240000, "QA-55201260", "P4", None),
        ("PM-107-4", "CT-2026-107", "4/4", d(74), 240000, "", "P0", None),
        ("PM-108-1", "CT-2026-108", "1/2", d(-32), 225000, "QA-55201233", "P3", d(-30)),
        ("PM-108-2", "CT-2026-108", "2/2", d(48), 225000, "", "P0", None),
        ("PM-109-1", "CT-2026-109", "1/1", d(-300), 300000, "QA-55200871", "P3", d(-296)),
        ("PM-110-1", "CT-2026-110", "1/1", d(-330), 420000, "QA-55200790", "P3", d(-326)),
        ("PM-105-預", "CT-2026-105", "1/3", d(25), 500000, "", "P0", None),
    ]
    for pid, cid, term, due, amt, inv, st, paid in payments:
        nl.create_row(ids["payments"], {
            "款項編號": nl.title(pid), "合約編號": nl.text(cid), "期數": nl.text(term),
            "預計付款日": nl.date(due), "金額": nl.number(amt), "發票號": nl.text(inv),
            "狀態": nl.select(st), "實收日": nl.date(paid),
            "合約": {"relation": [{"id": cmap[cid]}]},
        })
    print(f"  {len(payments)} 筆")

    print("④ 種操作歷史…")
    events = [
        ("CT-2026-103", "狀態前進：C0 → C1（送簽核、路由至事業群主管）", "Kyle Lu", d(-6)),
        ("CT-2026-103", "簽核卡關提醒：C1 已超過處理時限 3 天、已通知簽核人與發起人", "流程引擎", d(-2)),
        ("CT-2026-105", "報價單已寄出客戶（統一信箱副本存查）", "Philis Chen", d(-9)),
        ("CT-2026-105", "回簽追蹤提醒：已超過處理時限、建議業務電話跟催", "流程引擎", d(-1)),
        ("CT-2026-106", "回簽生效 → 自動產生款項排程 2 期、現金流量預測已更新", "流程引擎", d(0)),
        ("CT-2026-107", "款項 PM-107-3 逾期（預計 " + d(-38) + "）→ 標記逾期、進催收流程", "催收規則", d(-37)),
        ("CT-2026-107", "催收信已起草、業務確認後寄出（第 7 天）", "Jeff Hsieh（經助理）", d(-30)),
        ("CT-2026-107", "逾期滿 30 天 → 升級主管關注", "催收規則", d(-7)),
        ("CT-2026-109", "全款項結清 → 結案歸檔", "Amanda Chou", d(-14)),
        ("CT-2026-110", "到期前 60 天 → 續約窗口開啟、已通知負責業務", "流程引擎", d(-43)),
        ("CT-2026-111", "洽談中止 → 作廢（理由：客戶預算凍結、明年再議）", "Jeff Hsieh", d(-20)),
    ]
    for i, (cid, act, who, when) in enumerate(events, 1):
        nl.create_row(ids["events"], {
            "事件": nl.title(f"EV-{i:04d}"), "合約編號": nl.text(cid),
            "動作": nl.text(act), "執行者": nl.text(who), "時間": nl.date(when),
            "合約": {"relation": [{"id": cmap[cid]}]},
        })
    print(f"  {len(events)} 筆")

    print("⑤ 種留言…")
    comments = [
        ("CT-2026-107", "Nelsen Chen", "第三期逾期快 40 天了、這週要有結果 — 需要我出面就說。", d(-5)),
        ("CT-2026-105", "Philis Chen", "客戶窗口說回簽卡在他們法務、下週三前給消息。", d(-2)),
        ("CT-2026-106", "Amanda Chou（經助理）", "已請財務確認發票抬頭與統編、開票資訊齊了。", d(0)),
    ]
    for cid, who, content, when in comments:
        nl.create_row(ids["comments"], {
            "留言": nl.title(content[:60]), "合約編號": nl.text(cid),
            "留言人": nl.text(who), "時間": nl.date(when),
            "合約": {"relation": [{"id": cmap[cid]}]},
        })
    print(f"  {len(comments)} 筆")
    print("完成 — 合約 11（全狀態）、款項 11（5-11 月散佈、含逾期 D+38）、歷史 11、留言 3")


if __name__ == "__main__":
    main()
