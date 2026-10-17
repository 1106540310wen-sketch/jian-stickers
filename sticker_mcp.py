"""简简表情包 MCP：本地 stdio + 云端 Streamable HTTP 双模式。

本地运行：python sticker_mcp.py
云端运行：MCP_TRANSPORT=streamable-http python sticker_mcp.py
云端连接地址：https://<部署域名>/mcp
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.utilities.types import Image

REPO = "1106540310wen-sketch/jian-stickers"
INDEX_URL = f"https://raw.githubusercontent.com/{REPO}/main/stickers.json"
CDN_BASE = f"https://cdn.jsdelivr.net/gh/{REPO}@main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")

mcp = MCPServer(
    "jian-stickers",
    instructions=(
        "简简的私有使用习惯：可在合适的闲聊场景自然主动使用表情包；"
        "先用 list_stickers 了解表情包含义，再选择一张调用 show_sticker。"
        "不需要每次询问，也不要每句话都发送。"
        "show_sticker 返回真实图片数据，不是让用户打开的普通链接。"
    ),
)


def _load_stickers() -> list[dict[str, Any]]:
    """从公开 GitHub 清单读取已确认的图片索引。"""
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        response = client.get(INDEX_URL)
        response.raise_for_status()
        payload = response.json()
    items = payload.get("stickers")
    if not isinstance(items, list):
        raise ValueError("stickers.json 必须包含 stickers 数组")
    return [entry for entry in items if isinstance(entry, dict)]


@mcp.tool()
def list_stickers() -> str:
    """列出全部表情包的文件名、含义与情绪标签，供自然选图；不要凭数字猜图。"""
    items = _load_stickers()
    return json.dumps(
        [
            {
                "file": item["file"],
                "caption": item.get("caption") or "",
                "tags": item.get("tags") or [],
                "verified": bool(item.get("verified")),
            }
            for item in items
            if isinstance(item.get("file"), str)
        ],
        ensure_ascii=False,
    )


@mcp.tool()
def show_sticker(filename: str) -> Image:
    """发送指定表情包的实际 JPEG/PNG/WebP 图片数据（非文本链接）。

    请先用 list_stickers 选择语义合适的 file，然后把 file 原样传进来。
    """
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|webp)", filename):
        raise ValueError("无效的表情包文件名")

    allowed = {
        str(entry["file"])
        for entry in _load_stickers()
        if entry.get("verified") is True and isinstance(entry.get("file"), str)
    }
    if filename not in allowed:
        raise ValueError("表情包未在 stickers.json 中通过核对")

    # jsDelivr 做图片 CDN；如果源站尚未缓存或暂不可用，就回退 GitHub Raw。
    urls = [f"{CDN_BASE}/{filename}", f"{RAW_BASE}/{filename}"]
    last_error: Exception | None = None
    for url in urls:
        try:
            with httpx.Client(timeout=25, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
            if len(response.content) > 5_000_000:
                raise ValueError("图片超过 5 MB 限制")
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
            if content_type == "application/octet-stream":
                content_type = "image/png" if filename.endswith(".png") else (
                    "image/webp" if filename.endswith(".webp") else "image/jpeg"
                )
            if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise ValueError(f"图片响应类型不受支持：{content_type}")
            # MCP Python SDK v2 会自动编码为协议中的 ImageContent。
            return Image(data=response.content, format=content_type.split("/", 1)[1])
        except (httpx.HTTPError, ValueError) as error:
            last_error = error
    raise RuntimeError(f"无法读取表情包：{last_error}")


if __name__ == "__main__":
    if TRANSPORT not in {"stdio", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT 只能是 stdio 或 streamable-http")
    if TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "10000")),
            stateless_http=True,
            json_response=True,
        )
