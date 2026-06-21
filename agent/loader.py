"""
AgentLoader — reads Markdown files in agent/ and returns system message + metadata.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_AGENTS_DIR = Path(__file__).parent

_AGENT_FILES = {
    "leader": "leader.md",
    "lead_analysis": "lead_analysis.md",
    "lead_strategy": "lead_strategy.md",
    "macro_analyst": "macro_analyst.md",
    "technical_analyst": "technical_analyst.md",
    "bull_analyst": "bull_analyst.md",
    "bear_analyst": "bear_analyst.md",
}


def _parse_frontmatter(content: str) -> dict[str, Any]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    meta: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v.lower() in ("true", "yes"):
                v = True  # type: ignore[assignment]
            elif v.lower() in ("false", "no"):
                v = False  # type: ignore[assignment]
            elif v.lower() in ("null", "none", "~"):
                v = None  # type: ignore[assignment]
            else:
                v = v.strip('"\'')
            meta[k] = v
    return meta


def _extract_system_message(content: str) -> str:
    pattern = r"## System Message\s*\n+```(?:\w+)?\s*\n(.*?)\n```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("No '## System Message' code block found in agent markdown.")
    return match.group(1).strip()


class AgentLoader:
    """Loads agent configurations from markdown files in the agent/ directory."""

    @staticmethod
    def load(agent_key: str, **template_vars: str) -> dict[str, Any]:
        """
        Load agent config by key.

        Args:
            agent_key: One of 'leader', 'macro_analyst', 'technical_analyst',
                       'bull_analyst', 'bear_analyst'.
            **template_vars: Variables to inject into system message,
                             e.g. CURRENT_DATE="03/05/2026".

        Returns:
            dict with keys: name, description, tool_preset, system_message
        """
        filename = _AGENT_FILES.get(agent_key)
        if not filename:
            raise KeyError(f"Unknown agent key: {agent_key!r}. Valid keys: {list(_AGENT_FILES)}")

        path = _AGENTS_DIR / filename
        text = path.read_text(encoding="utf-8")

        meta = _parse_frontmatter(text)
        system_message = _extract_system_message(text)

        # Inject template variables (e.g. {{CURRENT_DATE}})
        for var_name, var_value in template_vars.items():
            system_message = system_message.replace(f"{{{{{var_name}}}}}", var_value)

        return {
            "name": meta.get("name", agent_key),
            "description": meta.get("description", ""),
            "tool_preset": meta.get("tool_preset"),
            "system_message": system_message,
        }

    @staticmethod
    def load_all(**template_vars: str) -> dict[str, dict[str, Any]]:
        """Load all agents and return a dict keyed by agent_key."""
        return {key: AgentLoader.load(key, **template_vars) for key in _AGENT_FILES}
