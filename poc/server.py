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


@mcp.tool()
def contract_create(customer: str, amount: float, terms: int = 1, first_due: str = "",
                    owner: str = "", expiry: str = "") -> dict:
    """建立合約（C0 報價草稿）— 閉環起點。terms 期數（1-12）、first_due 首期付款日（YYYY-MM-DD）。"""
    return cap.contract_create(customer, amount, terms, first_due, owner, expiry, actor="MCP 使用者")


@mcp.tool()
def payment_invoice(payment_id: str, invoice_no: str) -> dict:
    """開立發票（P0 → P1）— 人審動作、發票號必填。"""
    return cap.payment_invoice(payment_id, invoice_no, actor="MCP・財務")


@mcp.tool()
def quote_create(customer: str, plan: str = "Growth", owner: str = "", discount_untaxed: float = 0) -> dict:
    """建立 Co-Evo 報價單（Starter/Growth/Pro、寫公司報價庫、回編輯連結）— 整合自報價外掛、免各自分支。"""
    return cap.quote_create(customer, plan, owner, discount_untaxed or None, actor="MCP 使用者")


@mcp.tool()
def contract_renew(contract_id: str) -> dict:
    """續約開新約 — 原約需在 C7 續約窗口；新約沿用條件回 C0、閉環完成。"""
    return cap.contract_renew(contract_id, actor="MCP 使用者")


@mcp.tool()
def product_list() -> list[dict]:
    """產品目錄（顧問服務 / 標準產品 / 訂閱 / 客製、含建議單價與狀態）。"""
    return cap.product_list()


@mcp.tool()
def product_update(name: str, status: str = "", price: float = 0, note: str = "") -> dict:
    """產品目錄修改（人審動作）— status 上架/停售、price 建議單價、note 說明。"""
    return cap.product_update(name, status, price or None, note, actor="MCP 使用者")


@mcp.tool()
def quote_detail(quote_no: str) -> dict:
    """報價單完整內容（項目明細與 17 條固定條款、回編輯連結）。"""
    return cap.quote_detail(quote_no)


@mcp.tool()
def template_list(ttype: str = "") -> list[dict]:
    """樣板庫查詢 — 合約條款 / 報價條款 / 保密協議 / 催收信 / 信件範本。"""
    return cap.template_list(ttype)


if __name__ == "__main__":
    mcp.run()
