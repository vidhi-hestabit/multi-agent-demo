"""Format a markdown report for display."""

from __future__ import annotations


def format_report(markdown: str) -> str:
    """Wrap markdown report in a styled container."""
    if not markdown:
        return ""
    return f"""
<div style="border:1px solid #ddd; border-radius:8px; padding:20px; background:#fff; font-family:Georgia,serif;">
  <pre style="white-space:pre-wrap; font-family:inherit; font-size:14px; line-height:1.6;">{markdown}</pre>
</div>
"""
