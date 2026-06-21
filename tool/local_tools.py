"""
Local Python tools (not MCP) — LangChain StructuredTools backed by local code.

These tools are given to agents so they can decide when to use them,
rather than having the workflow hard-code trigger conditions.
"""
from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("trading_team.tools.local")


# =============================================================================
# save_report
# =============================================================================

class _SaveReportInput(BaseModel):
    title: str = Field(description="Short descriptive title for the report (e.g. 'Báo cáo HPG 2026-05-07')")
    content: str = Field(description="Full markdown body of the report to save")


def make_save_report_tool(reports_dir: str) -> StructuredTool:
    """
    Return a StructuredTool that saves a markdown report to *reports_dir*.

    Give this tool to the Leader agent so it can decide — based on the user's
    intent, not keyword matching — whether to persist the final answer as a file.
    """
    _dir = Path(reports_dir)

    def _save_report(title: str, content: str) -> str:
        today = date.today().strftime("%Y-%m-%d")
        slug = re.sub(r"[^a-z0-9]+", "_", title[:50].lower()).strip("_")
        _dir.mkdir(parents=True, exist_ok=True)
        report_file = _dir / f"{today}_{slug}.md"
        report_file.write_text(
            f"# {title}\n\n_{today}_\n\n{content}\n",
            encoding="utf-8",
        )
        logger.info("Report saved: %s", report_file)
        return f"✅ Report saved → {report_file.name}"

    return StructuredTool.from_function(
        func=_save_report,
        name="save_report",
        description=(
            "Save a markdown report to the reports directory on disk. "
            "Call this when the user explicitly asks to create, save, export, "
            "or generate a report file / analysis document."
        ),
        args_schema=_SaveReportInput,
    )
