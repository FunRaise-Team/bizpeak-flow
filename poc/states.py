"""合約生命週期狀態機 — 單一定義檔（卡帶 #1 的第一個真實工件）。

原則（SPEC §4）：單向前進、退回留痕、終端不變量。
任何介面（1.0 / 1.5 / 2.0）與任何卡帶都引用這份定義、不得私自複製。
"""

STATES = {
    "C0": {"name": "報價草稿",   "owner": "業務",            "sla_days": None},
    "C1": {"name": "內部簽核",   "owner": "簽核鏈",          "sla_days": 3},
    "C2": {"name": "用印完成",   "owner": "行政",            "sla_days": 2},
    "C3": {"name": "待客戶回簽", "owner": "業務",            "sla_days": 7},
    "C4": {"name": "回簽生效",   "owner": "系統＋財務",      "sla_days": 0},
    "C5": {"name": "履約・收款", "owner": "財務＋業務",      "sla_days": None},
    "C6": {"name": "結案",       "owner": "財務",            "sla_days": None},
    "C7": {"name": "續約窗口",   "owner": "業務＋BU 主管",   "sla_days": None},
    "X1": {"name": "作廢",       "owner": "—", "sla_days": None, "terminal": True},
    "X2": {"name": "不需寄出歸檔", "owner": "—", "sla_days": None, "terminal": True},
}

# 合法轉移：單向前進；退回（往前狀態）允許但必附 reason、事件層標記為退回
FORWARD = {
    "C0": ["C1", "X1"],
    "C1": ["C2", "X1"],
    "C2": ["C3", "X2"],
    "C3": ["C4", "X1"],
    "C4": ["C5"],
    "C5": ["C6"],
    "C6": ["C7"],
    "C7": ["C0"],  # 續約開新約 — 閉環（實務上是建立新合約、原約結束）
}
ORDER = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]

PAYMENT_STATES = {
    "P0": "排程", "P1": "已開票", "P2": "已通知客戶", "P3": "已收款", "P4": "逾期",
}


def validate_transition(from_state: str, to_state: str, reason: str = "") -> dict:
    """回傳 {ok, kind, error}；kind ∈ forward / rollback。退回必附 reason。"""
    if from_state not in STATES or to_state not in STATES:
        return {"ok": False, "error": f"未知狀態：{from_state} → {to_state}"}
    if STATES[from_state].get("terminal"):
        return {"ok": False, "error": f"{from_state}（{STATES[from_state]['name']}）是終端狀態、不可再轉移"}
    if to_state in FORWARD.get(from_state, []):
        return {"ok": True, "kind": "forward"}
    if to_state in ORDER and from_state in ORDER and ORDER.index(to_state) < ORDER.index(from_state):
        if not reason.strip():
            return {"ok": False, "error": "退回必須附理由（退回留痕原則）"}
        return {"ok": True, "kind": "rollback"}
    return {"ok": False, "error": f"不允許的轉移：{from_state} → {to_state}（合法前進：{FORWARD.get(from_state, [])}）"}
