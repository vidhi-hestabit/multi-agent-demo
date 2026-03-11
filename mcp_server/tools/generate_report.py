"""Generate a structured text report from provided data."""

from __future__ import annotations
from datetime import datetime
from typing import Any


TOOL_NAME = "generate_report"
TOOL_DESCRIPTION = (
    "Generate a structured markdown report from provided data sections."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Report title"},
        "summary": {"type": "string", "description": "Executive summary paragraph"},
        "sections": {
            "type": "array",
            "description": "List of report sections",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["heading", "content"],
            },
        },
        "metadata": {
            "type": "object",
            "description": "Optional key-value metadata (author, topic, etc.)",
            "additionalProperties": True,
        },
    },
    "required": ["title", "summary", "sections"],
}


async def handle(
    title: str,
    summary: str,
    sections: list[dict],
    metadata: dict[str, Any] | None = None,
) -> dict:
    now = datetime.utcnow().isoformat() + "Z"
    metadata = metadata or {}

    lines = [f"# {title}", "", f"**Generated:** {now}", ""]

    if metadata:
        for k, v in metadata.items():
            lines.append(f"**{k.capitalize()}:** {v}")
        lines.append("")

    lines += ["## Summary", "", summary, ""]

    for section in sections:
        heading = section.get("heading", "Section")
        content = section.get("content", "")
        lines += [f"## {heading}", "", content, ""]

    markdown = "\n".join(lines)

    return {
        "title": title,
        "markdown": markdown,
        "sections_count": len(sections),
        "generated_at": now,
        "metadata": metadata,
    }
