"""Jian's local sticker MCP server.

Install: pip install 'mcp[cli]' httpx
Run: python sticker_mcp.py

Runs over stdio. This does not automatically connect to ChatGPT mobile.
"""

import base64
import json
import re

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent

REPO = "1106540310wen-sketch/jian-stickers"
INDEX_URL = f"https://raw.githubusercontent.com/{REPO}/main/stickers.json"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"

mcp = FastMCP("jian-stickers")


def load_stickers() -> list[dict]:
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        response = client.get(INDEX_URL)
        response.raise_for_status()
        return response.json()["stickers"]


@mcp.tool()
def list_stickers() -> str:
    """List existing stickers with filenames, captions, and emotion tags."""
    stickers = load_stickers()
    return json.dumps(
        [
            {
                "file": sticker["file"],
                "caption": sticker.get("caption", ""),
                "tags": sticker.get("tags", []),
                "verified": sticker.get("verified", False),
            }
            for sticker in stickers
        ],
        ensure_ascii=False,
    )


@mcp.tool()
def show_sticker(filename: str) -> ImageContent:
    """Fetch an indexed sticker and return actual image content (not a URL)."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:jpeg|jpg|png|webp)", filename):
        raise ValueError("Invalid sticker filename")

    valid_files = {sticker["file"] for sticker in load_stickers()}
    if filename not in valid_files:
        raise ValueError("Sticker is not listed in stickers.json")

    with httpx.Client(timeout=20, follow_redirects=True) as client:
        response = client.get(f"{RAW_BASE}/{filename}")
        response.raise_for_status()

    mime_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
    if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError(f"Unexpected content type: {mime_type}")

    return ImageContent(
        type="image",
        data=base64.b64encode(response.content).decode("ascii"),
        mimeType=mime_type,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
