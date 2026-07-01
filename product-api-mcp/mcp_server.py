"""
MCP Server — 商品列表 API 的 AI 接口网关

自动处理 Basic Auth + JWT 登录，把商品接口暴露给 AI 调用。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 配置（可通过环境变量覆盖）
# ---------------------------------------------------------------------------

import os

API_BASE = os.getenv("MCP_API_BASE", "http://localhost:8000")
AUTH_USERNAME = os.getenv("MCP_AUTH_USERNAME", "docs")
AUTH_PASSWORD = os.getenv("MCP_AUTH_PASSWORD", "YOUR_PASSWORD_HERE")

# ---------------------------------------------------------------------------
# 全局状态
# ---------------------------------------------------------------------------

_token: str | None = None


async def ensure_token(client: httpx.AsyncClient) -> str:
    """获取或刷新 JWT Token"""
    global _token
    if _token:
        return _token
    resp = await client.post(
        f"{API_BASE}/auth/login",
        json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
        auth=(AUTH_USERNAME, AUTH_PASSWORD),
        timeout=10,
    )
    resp.raise_for_status()
    _token = resp.json()["access_token"]
    return _token


# ---------------------------------------------------------------------------
# MCP 协议工具定义
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_products",
        "description": "获取商品列表，支持分页、分类筛选、价格区间、关键词搜索、品牌、排序等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "页码，从1开始", "default": 1},
                "page_size": {"type": "integer", "description": "每页条数（最大100）", "default": 10},
                "category": {"type": "string", "description": "商品分类：电子产品、服装、食品、图书、家居、美妆、运动户外"},
                "min_price": {"type": "number", "description": "最低价格"},
                "max_price": {"type": "number", "description": "最高价格"},
                "keyword": {"type": "string", "description": "关键词搜索（名称/描述/品牌）"},
                "sort_by": {"type": "string", "description": "排序字段：price、rating、stock、sales、created_at"},
                "sort_order": {"type": "string", "description": "排序：asc 升序、desc 降序", "default": "asc"},
                "brand": {"type": "string", "description": "按品牌筛选"},
                "is_new": {"type": "boolean", "description": "是否仅看新品"},
                "is_hot": {"type": "boolean", "description": "是否仅看热销"},
                "tag": {"type": "string", "description": "按标签筛选"},
            },
        },
    },
    {
        "name": "get_product_detail",
        "description": "获取单个商品的详细信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "商品 ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_openapi_spec",
        "description": "获取商品列表 API 的 OpenAPI 规范（完整接口规格说明书）",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


async def handle_tool_call(name: str, args: dict) -> dict:
    """执行 MCP tool 调用"""
    async with httpx.AsyncClient() as client:
        token = await ensure_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        if name == "get_products":
            params = {}
            for k in (
                "page", "page_size", "min_price", "max_price",
                "category", "keyword", "sort_by", "sort_order",
                "brand", "is_new", "is_hot", "tag",
            ):
                if k in args and args[k] is not None:
                    params[k] = args[k]
            # 走 /api/ 通过 Nginx（需要 Basic Auth）
            resp = await client.get(
                f"{API_BASE}/products",
                params=params,
                headers=headers,
                auth=(AUTH_USERNAME, AUTH_PASSWORD),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
            }

        elif name == "get_product_detail":
            product_id = args["product_id"]
            resp = await client.get(
                f"{API_BASE}/products/{product_id}",
                headers=headers,
                auth=(AUTH_USERNAME, AUTH_PASSWORD),
                timeout=15,
            )
            if resp.status_code == 404:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"商品 {product_id} 不存在"}],
                }
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
            }

        elif name == "get_openapi_spec":
            resp = await client.get(
                f"{API_BASE}/openapi.json",
                auth=(AUTH_USERNAME, AUTH_PASSWORD),
                timeout=15,
            )
            resp.raise_for_status()
            spec = resp.json()
            return {
                "content": [{"type": "text", "text": json.dumps(spec, ensure_ascii=False, indent=2)}],
            }

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"未知工具: {name}"}],
            }


# ---------------------------------------------------------------------------
# FastAPI 应用 — MCP 传输层（SSE + POST）
# ---------------------------------------------------------------------------

app = FastAPI(title="商品列表 API MCP Server", version="1.0.0")

# 存储 pending 的 tool call response
_pending_responses: dict[str, asyncio.Future] = {}
_sse_queue: asyncio.Queue | None = None


@app.get("/mcp/events")
async def mcp_events():
    """SSE 端点 — AI 客户端从这里接收消息"""
    global _sse_queue
    _sse_queue = asyncio.Queue()

    # 生成一个 session ID
    session_id = str(uuid.uuid4())
    endpoint_url = f"/mcp/message?session_id={session_id}"

    async def event_stream():
        yield f"event: endpoint\ndata: {endpoint_url}\n\n"
        yield f"event: tools/list\ndata: {json.dumps(TOOLS, ensure_ascii=False)}\n\n"

        while True:
            msg = await _sse_queue.get()
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            if msg.get("type") == "close":
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class MCPMessage(BaseModel):
    jsonrpc: str = "2.0"
    method: str = Field(..., description="MCP 方法名")
    params: dict[str, Any] = Field(default_factory=dict)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


@app.post("/mcp/message")
async def mcp_message(msg: MCPMessage):
    """接收 AI 客户端的 tool 调用请求"""
    global _sse_queue

    if msg.method == "tools/call":
        tool_name = msg.params.get("name", "")
        tool_args = msg.params.get("arguments", {})

        result = await handle_tool_call(tool_name, tool_args)

        response = {
            "jsonrpc": "2.0",
            "id": msg.id,
            "result": result,
        }
        if _sse_queue:
            await _sse_queue.put(response)

        return {"ok": True}

    return {"ok": True}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "api": API_BASE}


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8765, reload=False)
