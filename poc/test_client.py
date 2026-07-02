"""POC 驗收測試 — 以 MCP 客戶端連 server.py、實呼叫能力工具（Rule 7 live test）。
執行：uv run test_client.py
"""
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("工具清單:", [t.name for t in tools.tools])

            r1 = await s.call_tool("payment_overdue_list", {})
            print("\n逾期款項:", r1.content[0].text[:400])

            r2 = await s.call_tool("contract_get", {"contract_id": "CT-2026-041"})
            print("\n合約詳情:", r2.content[0].text[:400])

            r3 = await s.call_tool("cashflow_forecast", {})
            print("\n現金流預測:", r3.content[0].text[:300])

            r4 = await s.call_tool("contract_transition",
                                   {"contract_id": "CT-2026-047", "to_state": "C2", "actor": "驗收測試"})
            print("\n狀態轉移（C1→C2 合法前進）:", r4.content[0].text[:200])

            r5 = await s.call_tool("contract_transition",
                                   {"contract_id": "CT-2026-041", "to_state": "C2"})
            print("\n狀態轉移（C5→C2 退回無理由、應被擋）:", r5.content[0].text[:200])

            ok = ("逾期天數" in r1.content[0].text and '"ok": true' in r4.content[0].text
                  and "退回必須附理由" in r5.content[0].text)
            print("\n驗收:", "PASS" if ok else "FAIL")
            return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
