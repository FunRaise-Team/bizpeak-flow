"""BizPeak Flow MCP 伺服器（體驗 2.0 入口）— 薄層、能力全在 capabilities.py。

執行：uv run server.py（stdio）
掛載 Claude Code：claude mcp add bizpeak -- uv run --project <此目錄> server.py
"""
from mcp.server.fastmcp import FastMCP

import capabilities as cap

mcp = FastMCP("bizpeak-flow")


@mcp.tool()
def contract_list(status: str = "") -> list[dict]:
    """列出合約。status 可選（C0-C7 / X1 / X2）、空字串列全部。"""
    return cap.contract_list(status)


@mcp.tool()
def contract_get(contract_id: str) -> dict:
    """單張合約詳情＋其款項排程。contract_id 例：CT-2026-041。"""
    return cap.contract_get(contract_id)


@mcp.tool()
def contract_transition(contract_id: str, to_state: str, reason: str = "", actor: str = "MCP 使用者") -> dict:
    """合約狀態轉移 — 經狀態機驗證（單向前進；退回必附 reason）、寫入事件留痕。"""
    return cap.contract_transition(contract_id, to_state, reason, actor)


@mcp.tool()
def payment_overdue_list(today: str = "") -> list[dict]:
    """逾期款項清單（狀態 P4、或已過預計付款日且未收款）。today 預設今天、可覆寫供演示。"""
    return cap.payment_overdue_list(today)


@mcp.tool()
def payment_mark_paid(payment_id: str, paid_date: str = "", actor: str = "財務") -> dict:
    """收款打勾（人審動作 — 憲法第四條：確認由人發起、系統留痕）。"""
    return cap.payment_mark_paid(payment_id, paid_date, actor)


@mcp.tool()
def cashflow_forecast() -> dict:
    """現金流量預測 — 未收款項按月彙總（管理層入口的核心數字）。"""
    return cap.cashflow_forecast()


if __name__ == "__main__":
    mcp.run()
