"""POC 驗收測試 — 以 MCP 客戶端連 server.py、實呼叫能力工具（Rule 7 live test）。
執行：uv run test_client.py
"""
import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import states


async def main():
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("工具清單:", [t.name for t in tools.tools])

            r1 = await s.call_tool("payment_overdue_list", {})
            print("\n逾期款項:", r1.content[0].text[:300])

            r2 = await s.call_tool("contract_get", {"contract_id": "CT-2026-041"})
            print("\n合約詳情:", r2.content[0].text[:300])

            r3 = await s.call_tool("cashflow_forecast", {})
            print("\n現金流預測:", r3.content[0].text[:250])

            # 動態取 CT-2026-047 當前狀態、推進到合法下一步
            g = await s.call_tool("contract_get", {"contract_id": "CT-2026-047"})
            st = json.loads(g.content[0].text)["狀態"]
            nxt = [x for x in states.FORWARD.get(st, []) if not x.startswith("X") and x != "C0"]
            if nxt:
                r4 = await s.call_tool("contract_transition",
                                       {"contract_id": "CT-2026-047", "to_state": nxt[0], "actor": "驗收測試"})
                t4 = r4.content[0].text
                gd = json.loads(g.content[0].text)
                unpaid = [x for x in gd.get("款項", []) if x["狀態"] != "P3"]
                if nxt[0] == "C6" and unpaid:
                    print(f"\n狀態轉移（{st}→C6、有未收款、應被守門擋）:", t4[:120])
                    fwd_ok = "不能結案" in t4
                else:
                    print(f"\n狀態轉移（{st}→{nxt[0]} 合法前進）:", t4[:160])
                    fwd_ok = '"ok": true' in t4
            else:
                print(f"\nCT-2026-047 已在 {st}、無合法前進目標 — 跳過前進測試")
                fwd_ok = True

            r5 = await s.call_tool("contract_transition",
                                   {"contract_id": "CT-2026-041", "to_state": "C2"})
            t5 = r5.content[0].text
            print("\n狀態轉移（C5→C2 退回無理由、應被擋）:", t5[:160])

            ok = ("逾期天數" in r1.content[0].text and fwd_ok and "退回必須附理由" in t5)
            print("\n驗收:", "PASS" if ok else "FAIL")
            return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
