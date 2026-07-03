"""Notion 資料層薄封裝 — 憲法第一條：Notion 是唯一真相來源。

POC 直連（無快取層）；正式版加快取佇列擋每秒 3 請求限流（ARCHITECTURE §3）。
token 讀自 ~/NelsenClaw/.env 的 NOTION_API_KEY、或環境變數（不寫死、不進版控）。
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.notion.com/v1"
IDS_FILE = Path(__file__).parent / "notion_ids.json"


def _token() -> str:
    if os.environ.get("NOTION_API_KEY"):
        return os.environ["NOTION_API_KEY"].strip()
    for env in (Path(__file__).parent / ".env", Path.home() / "NelsenClaw" / ".env"):
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("NOTION_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise RuntimeError("找不到 NOTION_API_KEY（環境變數、poc/.env 或 ~/NelsenClaw/.env）")


def api(method: str, path: str, body: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(f"{API}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Notion API {e.code}: {e.read().decode()[:300]}") from e
    raise RuntimeError("Notion API 429 重試耗盡")


def load_ids() -> dict:
    if not IDS_FILE.exists():
        raise RuntimeError("notion_ids.json 不存在 — 先跑 `uv run setup_notion.py` 建立資料層")
    return json.loads(IDS_FILE.read_text())


def query_db(db: dict, filter_: dict | None = None) -> list[dict]:
    """查詢資料庫 — 先走 data_source 端點（2025-09-03）、失敗回退 database 端點。"""
    body: dict = {"page_size": 100}
    if filter_:
        body["filter"] = filter_
    try:
        if db.get("data_source_id"):
            return api("POST", f"/data_sources/{db['data_source_id']}/query", body)["results"]
    except RuntimeError:
        pass
    return api("POST", f"/databases/{db['database_id']}/query", body)["results"]


def create_row(db: dict, properties: dict) -> dict:
    try:
        if db.get("data_source_id"):
            return api("POST", "/pages", {"parent": {"type": "data_source_id", "data_source_id": db["data_source_id"]}, "properties": properties})
    except RuntimeError:
        pass
    return api("POST", "/pages", {"parent": {"database_id": db["database_id"]}, "properties": properties})


def update_row(page_id: str, properties: dict) -> dict:
    return api("PATCH", f"/pages/{page_id}", {"properties": properties})


# ── 屬性讀寫小工具 ──
def title(v): return {"title": [{"type": "text", "text": {"content": v}}]}
def text(v): return {"rich_text": [{"type": "text", "text": {"content": v}}]}
def select(v): return {"select": {"name": v}}
def number(v): return {"number": v}
def date(v): return {"date": {"start": v}} if v else {"date": None}


def read_prop(page: dict, name: str):
    p = page.get("properties", {}).get(name)
    if not p:
        return None
    t = p["type"]
    if t == "title":
        return "".join(x.get("plain_text", "") for x in p["title"])
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in p["rich_text"])
    if t == "select":
        return (p["select"] or {}).get("name")
    if t == "number":
        return p["number"]
    if t == "date":
        return (p["date"] or {}).get("start")
    if t == "url":
        return p["url"]
    return None
