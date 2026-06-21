"""
LangGraph Trading Team — StateGraph
--------------------------------------
Flow:
    START
      ↓
    leader_intake          ← Leader parses the request, asks for clarification if needed
      ↓ (needs clarification)  ↓ (clear)
    END                    lead_analysis       ← LeadAnalysis routes + runs analysts in parallel
                             ↓  (asyncio.gather)
                           [macro_agent ‖ technical_agent]  ← run concurrently inside node
                             ↓  (synthesis brief)
                           bull_argument       ← BullAnalyst (DeepAgent + filesystem memory)
                             ↓
                           bear_argument       ← BearAnalyst (DeepAgent + filesystem memory)
                             ↓
                           arbitration         ← Leader evaluates the debate
                             ↓ (continue & < max)  ↓ (done)
                           bull_argument ←←←  synthesis   ← Leader synthesizes final answer
                                               ↓
                                             END

Per-agent LLM config (env vars, all fall back to TRADING_MODEL / TRADING_BASE_URL / TRADING_API_KEY):
    TRADING_LEADER_MODEL / _BASE_URL / _API_KEY
    TRADING_LEAD_ANALYSIS_MODEL / _BASE_URL / _API_KEY
    TRADING_MACRO_MODEL / _BASE_URL / _API_KEY
    TRADING_TECHNICAL_MODEL / _BASE_URL / _API_KEY
    TRADING_BULL_MODEL / _BASE_URL / _API_KEY
    TRADING_BEAR_MODEL / _BASE_URL / _API_KEY

Streaming: graph.astream(state, stream_mode="updates")
    → yield {node_name: state_updates} after each node completes.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from pathlib import Path
from typing import AsyncIterator, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from agent.loader import AgentLoader
from tool.local_tools import make_save_report_tool
from tool.mcp_tools import ToolRegistry, set_tool_log_context
from uuid import uuid4 as _uuid4
from contextvars import ContextVar as _ContextVar
from tool.memory_layer import (
    create_analysis_agent,
    create_lead_analysis_agent,
    create_strategy_agent,
    create_leader_agent,
    ensure_memory_structure,
    MEMORY_ROOT,
)
from config import settings

# ContextVar that tracks the active session_key across the async call chain.
# Set at astream() entry; read by _invoke() to tag tool-call log entries.
_active_session: _ContextVar[str] = _ContextVar("active_session", default="-")

logger = logging.getLogger("trading_team.workflow")


# =============================================================================
# Graph State
# =============================================================================

class TradingState(TypedDict, total=False):
    question: str
    history: str
    session_key: str
    # Phase: intake
    leader_intake: str
    needs_clarification: bool
    # Flow type decided by Leader at intake
    # "full"          → analysis → debate → synthesis → review
    # "analysis_only" → analysis → synthesis → review  (no debate)
    # "strategy_only" → synthesis → review             (follow-up / strategy-room only)
    flow_type: str  # default "full"
    # Phase: analysis (parallel inside lead_analysis node)
    macro_analysis: str
    technical_analysis: str
    macro_tool_trace: str       # tool call trace from MacroAnalyst (for verification)
    tech_tool_trace: str        # tool call trace from TechnicalAnalyst (for verification)
    lead_analysis: str          # synthesized brief from LeadAnalysis coordinator
    # Phase: analysis verification
    analysis_verify_count: int   # number of verification cycles run
    analysis_verify_notes: str   # issues found in last verification (empty = verified)
    # Phase: debate
    bull_last: str
    bear_last: str
    debate_round: int
    debate_complete: bool
    debate_transcript: str
    debate_summary: str
    arbitration_result: str
    # Phase: synthesis + review
    synthesis_draft: str        # output from LeadStrategy (strategy room head)
    synthesis_round: int        # number of synthesis attempts
    review_feedback: str        # Leader's feedback when revision needed
    review_approved: bool       # True when Leader approves synthesis
    portfolio_context: str      # inferred holder/non-holder context for current question
    final_answer: str


_PORTFOLIO_FILE = MEMORY_ROOT / "portfolio" / "AGENTS.md"
_TICKER_PATTERN = re.compile(r"\b[A-Z]{3,5}\b")

# Vietnamese analysis verbs/phrases — if any appears in the leader directive, the
# request is real analysis and must NOT be auto-demoted to `direct`.
_ANALYSIS_VERBS = re.compile(
    r"\b("
    r"phân\s*tích|đánh\s*giá|nhận\s*định|chiến\s*lược|so\s*sánh|tư\s*vấn|"
    r"phân\s*bổ|vị\s*thế|nắm\s*giữ|mua|vào\s*lệnh|bán|cắt\s*lỗ|"
    r"dự\s*báo|triển\s*vọng|định\s*giá|tín\s*hiệu|xu\s*hướng|"
    r"analy[sz]e|evaluat|assess|recommend|outlook|forecast|valuation"
    r")\b",
    re.IGNORECASE,
)


def _looks_like_analysis_request(text: str) -> bool:
    """Heuristic: does the leader directive look like a real analysis request?

    Returns True when the text mentions a stock ticker (3-5 uppercase letters,
    e.g. HPG, VCB, VN30) OR contains an analysis verb (phân tích, đánh giá, ...).
    False for greetings, definitions, status checks, generic small talk — those
    are demoted to [FLOW:direct] to skip the analysis/strategy rooms.
    """
    if not text:
        return False
    if _TICKER_PATTERN.search(text):
        return True
    if _ANALYSIS_VERBS.search(text):
        return True
    return False
_PORTFOLIO_LINE_PATTERN = re.compile(
    r"^([A-Z]{2,10}):\s*(.+?)\s+shares\s*@\s*avg\s*([\d,]+(?:\.\d+)?)\s*\|\s*([^|]+?)\s*NAV\s*\|\s*SL:\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)


# =============================================================================
# LLM factory
# =============================================================================


def _parse_number(text: str) -> float | None:
    cleaned = text.replace(",", "").replace("~", "").replace("≤", "").strip()
    m = re.search(r"\d+(?:\.\d+)?", cleaned)
    return float(m.group(0)) if m else None


def _load_portfolio_positions() -> dict[str, dict[str, float | str]]:
    if not _PORTFOLIO_FILE.exists():
        return {}
    positions: dict[str, dict[str, float | str]] = {}
    for raw_line in _PORTFOLIO_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("-").strip()
        match = _PORTFOLIO_LINE_PATTERN.match(line)
        if not match:
            continue
        ticker, shares_text, avg_text, nav_text, sl_text = match.groups()
        shares = _parse_number(shares_text)
        avg_price = _parse_number(avg_text)
        nav_pct = _parse_number(nav_text)
        stop_loss = _parse_number(sl_text)
        positions[ticker.upper()] = {
            "ticker": ticker.upper(),
            "shares": shares or 0.0,
            "avg_price": avg_price or 0.0,
            "nav_pct": nav_pct or 0.0,
            "stop_loss": stop_loss or 0.0,
            "raw_line": line,
        }
    return positions


def _infer_primary_ticker(question: str, *texts: str) -> str:
    search_space = "\n".join([question, *texts])
    for match in _TICKER_PATTERN.finditer(search_space.upper()):
        ticker = match.group(0)
        if ticker not in {"NAV", "SL", "RSI", "MACD", "VNINDEX", "VN30F"}:
            return ticker
    return ""


def _extract_reference_price(*texts: str) -> float | None:
    price_patterns = [
        re.compile(r"giá đóng cửa[^\d]*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"đóng cửa[^\d]*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"current price[^\d]*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
        re.compile(r"close price[^\d]*([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    ]
    for text in texts:
        if not text:
            continue
        for pattern in price_patterns:
            match = pattern.search(text)
            if match:
                return _parse_number(match.group(1))
    return None


def _infer_holding_state(
    question: str,
    nav_pct: float,
    avg_price: float,
    reference_price: float | None,
) -> tuple[str, str, str, str]:
    lowered_question = question.lower()

    concentration_state = "overweight" if nav_pct >= 20 else "normal_size"
    concentration_reason = (
        f"position size is {nav_pct:g}% NAV" if nav_pct >= 20 else f"position size is {nav_pct:g}% NAV, not concentrated"
    )

    if reference_price is not None and avg_price > 0:
        if reference_price > avg_price:
            return "holding_profit", f"reference price {reference_price:,.0f} is above avg price {avg_price:,.0f}", concentration_state, concentration_reason
        if reference_price < avg_price:
            return "holding_loss", f"reference price {reference_price:,.0f} is below avg price {avg_price:,.0f}", concentration_state, concentration_reason
        return "at_cost", f"reference price {reference_price:,.0f} is near avg price {avg_price:,.0f}", concentration_state, concentration_reason

    if any(phrase in lowered_question for phrase in ("đang lỗ", "lỗ nhẹ", "lỗ", "kẹt hàng")):
        return "holding_loss", "question wording indicates the user is under pressure / in loss", concentration_state, concentration_reason
    if any(phrase in lowered_question for phrase in ("đang lời", "có lời", "lãi")):
        return "holding_profit", "question wording indicates the user is in profit", concentration_state, concentration_reason
    return "normal_position", "position exists but no reliable profit/loss signal was inferred", concentration_state, concentration_reason



def _format_effective_holding_state(pnl_state: str, concentration_state: str) -> str:
    if concentration_state == "overweight" and pnl_state in {"holding_profit", "holding_loss", "at_cost"}:
        return f"{concentration_state}_{pnl_state}"
    if concentration_state == "overweight":
        return concentration_state
    return pnl_state



def _build_strategy_requirements(effective_holding_state: str, pnl_state: str, concentration_state: str) -> str:
    requirements = [
        "- Distinguish clearly between advice for the existing holder and a fresh entrant.",
        "- If the user is already holding, anchor the recommendation to current stop-loss / thesis protection rather than generic entry logic.",
    ]
    if concentration_state == "overweight":
        requirements.append("- Concentration risk is elevated; address risk control before any add recommendation.")
    if pnl_state == "holding_profit":
        requirements.append("- Prioritize hold / trailing / partial take-profit logic before discussing any add.")
    if pnl_state == "holding_loss":
        requirements.append("- Prioritize thesis protection / reduce-vs-hold logic and do not default to averaging down.")
    if effective_holding_state == "no_position":
        requirements.append("- Focus on new-entry conditions, starter size, invalidation, and whether waiting is preferable.")
    return "\n".join(requirements)



def _build_portfolio_context(question: str, lead_analysis: str = "", macro_analysis: str = "", technical_analysis: str = "") -> str:
    ticker = _infer_primary_ticker(question, lead_analysis, macro_analysis, technical_analysis)
    if not ticker:
        return "Portfolio context unavailable: no primary ticker inferred from the request."

    positions = _load_portfolio_positions()
    position = positions.get(ticker)
    if not position:
        return (
            f"Primary ticker inferred: {ticker}\n"
            "Holding state: no_position\n"
            "User does not currently hold this ticker in portfolio/AGENTS.md.\n"
            "Recommendation should focus on new-entry conditions, starter size, invalidation, and whether waiting is preferable."
        )

    nav_pct = float(position["nav_pct"])
    avg_price = float(position["avg_price"])
    stop_loss = float(position["stop_loss"])
    shares = float(position["shares"])
    reference_price = _extract_reference_price(technical_analysis, lead_analysis, macro_analysis)
    pnl_state, pnl_reason, concentration_state, concentration_reason = _infer_holding_state(
        question,
        nav_pct,
        avg_price,
        reference_price,
    )
    effective_holding_state = _format_effective_holding_state(pnl_state, concentration_state)

    price_context = (
        f"Reference price: {reference_price:,.0f}\n" if reference_price is not None else "Reference price: unavailable\n"
    )

    return (
        f"Primary ticker inferred: {ticker}\n"
        f"Holding state: {effective_holding_state}\n"
        f"P&L state: {pnl_state}\n"
        f"P&L state reason: {pnl_reason}\n"
        f"Concentration state: {concentration_state}\n"
        f"Concentration state reason: {concentration_reason}\n"
        f"Current position: {shares:,.0f} shares @ avg {avg_price:,.0f} | {nav_pct:g}% NAV | SL {stop_loss:,.0f}\n"
        f"{price_context}"
        f"Portfolio line: {position['raw_line']}\n"
        "Strategy requirements:\n"
        f"{_build_strategy_requirements(effective_holding_state, pnl_state, concentration_state)}"
    )





# =============================================================================
# Node helpers
# =============================================================================


def _make_llm_for(cfg: dict) -> ChatOpenAI:
    """Create a ChatOpenAI instance from a per-agent config dict."""
    return ChatOpenAI(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=0.7,
    )


# =============================================================================
# Node helpers
# =============================================================================

def _make_llm_for(cfg: dict) -> ChatOpenAI:
    """Create a ChatOpenAI instance from a per-agent config dict."""
    return ChatOpenAI(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=0.7,
    )


# =============================================================================
# Node helpers
# =============================================================================

def _last_ai_text(result: dict) -> str:
    """Extract text from the last AIMessage in a deep/ReAct agent result."""
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return msg.content or ""
    return ""


def _extract_tool_trace(result: dict) -> str:
    """Extract a readable tool call trace from an agent result's message list.

    Returns a compact log of every tool call and its trimmed result, e.g.:
      [1] get_stock_quote(symbol='HPG') → {"price": 25.3, ...} (200 chars)
      [2] get_finpath_stock_snapshot(symbol='HPG') → {"identity": ...} (500 chars)

    Used by analysis_verify so the verifier can inspect *what* the analysts
    actually did instead of re-calling tools itself.
    """
    from langchain_core.messages import ToolMessage
    messages = result.get("messages", [])
    # Build a map tool_call_id → tool result content
    tool_results: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, ToolMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            tool_results[msg.tool_call_id] = content[:400]

    lines: list[str] = []
    call_idx = 1
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                args_str = ", ".join(f"{k}={v!r}" for k, v in tc.get("args", {}).items())
                result_str = tool_results.get(tc["id"], "(no result captured)")
                lines.append(f"[{call_idx}] {tc['name']}({args_str}) → {result_str}")
                call_idx += 1
    return "\n".join(lines) if lines else "(no tool calls made)"


# Tool name keywords used by _split_trace_by_domain to route a gap-fill tool
# call to either the macro or technical analyst's trace. The categorisation
# mirrors which MCP server / data domain the tool belongs to — anything that
# returns market-wide / macro-economic / sentiment data goes to macro; anything
# that returns symbol-level price / indicator data goes to technical. Web
# research tools (web_search, research_topic) are treated as macro because the
# verifier's criterion [A] only requires them when the original macro analyst
# was missing them.
_MACRO_TOOL_KEYWORDS = (
    "asean", "unified_macro", "market_breadth", "market_overview",
    "market_top", "money_flow", "sector_overview", "index_overview",
    "index_futures", "hot_news", "web_search", "research_topic",
)
_TECHNICAL_TOOL_KEYWORDS = (
    "price_data", "ohlcv", "technical_analysis", "index_bars",
    "stock_snapshot", "symbols_by_group", "local_vn",
)


def _classify_tool_name(tool_name: str) -> str:
    """Return 'macro', 'technical', or 'unknown' for a given tool name."""
    lowered = tool_name.lower()
    for kw in _MACRO_TOOL_KEYWORDS:
        if kw in lowered:
            return "macro"
    for kw in _TECHNICAL_TOOL_KEYWORDS:
        if kw in lowered:
            return "technical"
    return "unknown"


def _split_trace_by_domain(trace: str) -> tuple[str, str]:
    """Split a gap-fill tool trace into (macro_trace, technical_trace).

    Each input line has the form `[N] tool_name(...) → ...`. Lines whose
    tool_name classifies as 'unknown' are dropped (they aren't useful for
    the macro/tech verification criteria). Empty input → both outputs are
    '(no tool calls made)' so the per-analyst trace placeholder stays valid.
    """
    if not trace or trace == "(no tool calls made)":
        return "(no tool calls made)", "(no tool calls made)"

    macro_lines: list[str] = []
    tech_lines: list[str] = []
    macro_idx = tech_idx = 1
    for raw_line in trace.splitlines():
        if not raw_line.startswith("["):
            continue
        # Format: '[N] tool_name(args) → result'
        try:
            header, rest = raw_line.split("]", 1)
            # skip leading "[" digit
            after_bracket = rest.lstrip()
            # tool name is the first whitespace-delimited token of after_bracket
            tool_name = after_bracket.split("(", 1)[0].strip()
        except ValueError:
            continue
        domain = _classify_tool_name(tool_name)
        if domain == "macro":
            # Re-number so the verifier sees a clean [1] [2] ... sequence
            new_line = raw_line.replace(f"{header}]", f"[{macro_idx}]", 1)
            macro_lines.append(new_line)
            macro_idx += 1
        elif domain == "technical":
            new_line = raw_line.replace(f"{header}]", f"[{tech_idx}]", 1)
            tech_lines.append(new_line)
            tech_idx += 1
        # else: unknown domain — drop

    macro_out = "\n".join(macro_lines) if macro_lines else "(no tool calls made)"
    tech_out = "\n".join(tech_lines) if tech_lines else "(no tool calls made)"
    return macro_out, tech_out


# =============================================================================
# TradingTeamGraph
# =============================================================================

class TradingTeamGraph:
    """
    LangGraph-based trading team orchestrator.

    Usage:
        registry = ToolRegistry(...)
        await registry.load()
        graph = TradingTeamGraph(registry)

        async for event_type, text in graph.astream({"question": "...", ...}):
            print(event_type, text)
    """

    # Maps node names → readable labels for the channel
    NODE_LABELS: dict[str, str] = {
        "leader_intake":          "📋 *Leader*",
        "lead_analysis":          "🔬 *Analysis Room* (Macro ∥ Technical)",
        "analysis_verify":        "🔍 *Data Verifier*",
        "bull_argument":          "🐂 *BullAnalyst*",
        "bear_argument":          "🐻 *BearAnalyst*",
        "arbitration":            "⚖️ *Leader (Arbitrator)*",
        "strategy_synthesis":     "📝 *Strategy Room*",
        "leader_review":          "✅ *Final Summary (Approved)*",
        "leader_review_revision": "🔄 *Leader: Revision Requested*",
    }

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._registry = tool_registry
        today = settings.CURRENT_DATE
        self._prompts = AgentLoader.load_all(
            CURRENT_DATE=today,
            CURRENT_MONTH=settings.CURRENT_MONTH,
            CURRENT_YEAR=settings.CURRENT_YEAR,
            RESPONSE_LANGUAGE_INSTRUCTION=settings.RESPONSE_LANGUAGE_INSTRUCTION,
        )
        self._skill_agent = None  # lazy: built in _get_skill_agent()
        self._graph = self._build_graph()

    # -------------------------------------------------------------------------
    # Skill curator agent (deepagent) — used by node_memory_save after each
    # session to decide CREATE/UPDATE/no_skill. Built lazily because
    # create_deep_agent needs the running event loop for some backends.
    # -------------------------------------------------------------------------

    def _get_skill_agent(self):
        """Return the singleton skill-curator deepagent. Reads /memory/skills/
        via LocalShellBackend, writes only to that path, and returns structured
        SkillDecision (action, category, name, description, content, rationale).
        """
        if self._skill_agent is not None:
            return self._skill_agent

        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
        from typing import Literal

        # Local schema for the structured response (kept here, not in a shared
        # module, because only the skill curator uses it).
        class SkillDecision(BaseModel):
            action: Literal["create", "update", "no_skill"] = Field(
                description="create | update | no_skill"
            )
            category: Literal["shared", "analysis", "strategy", ""] = Field(
                default="",
                description="target category; empty for no_skill",
            )
            name: str = Field(
                default="",
                description="kebab-case skill name; for update, must match existing",
            )
            description: str = Field(
                default="",
                description="1-2 sentence frontmatter description",
            )
            content: str = Field(
                default="",
                description="full SKILL.md body (after the frontmatter), empty for no_skill",
            )
            rationale: str = Field(
                default="",
                description="why this decision; logged for audit",
            )

        from deepagents import create_deep_agent
        from deepagents.backends import CompositeBackend, LocalShellBackend, StateBackend
        from deepagents.middleware.filesystem import FilesystemPermission

        # Use the same model as the leader (Vietnamese fluency + cost alignment).
        # The skill task is small — no tool calls beyond ls/read_file/write_file.
        llm_cfg = settings.LEADER_LLM_CFG
        skill_llm = ChatOpenAI(
            model=llm_cfg["model"],
            api_key=llm_cfg["api_key"],
            base_url=llm_cfg["base_url"],
            temperature=0,
        )

        # System prompt explicitly tells the agent HOW to decide, not just WHAT
        # the categories are. The key instructions:
        #   - MUST read full content before UPDATE
        #   - Same name/category for update; new name for create
        #   - Vietnamese: respond in Vietnamese when content is in Vietnamese
        system_prompt = (
            "You are a SKILL CURATOR for a Vietnamese stock trading AI team.\n"
            "Your job: after each session, decide if a REUSABLE workflow should be "
            "captured as a skill file under /memory/skills/<category>/<name>/SKILL.md.\n\n"
            "A SKILL IS: a step-by-step procedure useful for MANY future sessions.\n"
            "NOT a skill: ticker-specific facts, one-time lessons, single trade decisions, "
            "or one-off greetings/status checks.\n\n"
            "Categories:\n"
            "  - 'shared'    : cross-domain workflows (apply to many ticker types)\n"
            "  - 'analysis'  : macro/technical analysis workflows\n"
            "  - 'strategy'  : trading, position sizing, execution workflows\n\n"
            "Names: English, lowercase-hyphens (e.g. vn-stock-oversell-screen).\n\n"
            "MANDATORY workflow:\n"
            "1. ls /memory/skills/ — see all categories.\n"
            "2. For each relevant category, ls /memory/skills/<category>/ — see existing skills.\n"
            "3. Read the FULL SKILL.md of any existing skill whose description looks RELATED. "
            "Do NOT decide UPDATE without reading the full content first.\n"
            "4. Compare the new session's workflow with the existing skill's full content.\n"
            "5. Decide:\n"
            "     no_skill  — nothing new or fully covered by an existing skill\n"
            "     update    — existing skill is RELATED and needs EXPANSION; keep the same "
            "(category, name); preserve useful content from the old version; add new insights\n"
            "     create    — genuinely NEW workflow with no overlap; pick a fresh English name\n"
            "6. If update/create: use write_file to write the FULL SKILL.md to the right path. "
            "The file MUST start with the YAML frontmatter (---\\nname: ...\\ndescription: ...\\n---) "
            "followed by markdown body with ## sections.\n"
            "7. Return the structured response — no prose outside the structured fields."
        )

        self._skill_agent = create_deep_agent(
            model=skill_llm,
            system_prompt=system_prompt,
            # Permission scope: only /memory/skills/ — the agent CANNOT read or
            # write to code, logs, sessions, portfolio, or anywhere else.
            permissions=[
                FilesystemPermission(operations=["read"],  paths=["/memory/skills/"]),
                FilesystemPermission(operations=["write"], paths=["/memory/skills/"]),
            ],
            backend=CompositeBackend(
                default=StateBackend(),
                routes={
                    "/memory/": LocalShellBackend(
                        root_dir=str(MEMORY_ROOT),
                        virtual_mode=True,
                    ),
                },
            ),
            response_format=SkillDecision,
            name="SkillCuratorAgent",
        )
        return self._skill_agent

    # -------------------------------------------------------------------------
    # Build graph
    # -------------------------------------------------------------------------

    def _build_graph(self):
        ensure_memory_structure()

        analysis_tools = self._registry.get_analysis_tools()
        strategy_tools = self._registry.get_strategy_tools()
        leader_tools   = self._registry.get_leader_tools()

        # Each agent gets its own LLM — configurable via env vars independently
        macro_agent         = create_analysis_agent(
            _make_llm_for(settings.MACRO_LLM_CFG), analysis_tools,
            self._prompts["macro_analyst"]["system_message"], name="MacroAnalyst", domain="macro",
        )
        tech_agent          = create_analysis_agent(
            _make_llm_for(settings.TECHNICAL_LLM_CFG), analysis_tools,
            self._prompts["technical_analyst"]["system_message"], name="TechnicalAnalyst", domain="technical",
        )
        lead_analysis_agent = create_lead_analysis_agent(
            _make_llm_for(settings.LEAD_ANALYSIS_LLM_CFG), analysis_tools,
            self._prompts["lead_analysis"]["system_message"],
        )
        lead_strategy_agent = create_strategy_agent(
            _make_llm_for(settings.LEAD_STRATEGY_LLM_CFG), strategy_tools,
            self._prompts["lead_strategy"]["system_message"], name="LeadStrategy",
        )
        bull_agent          = create_strategy_agent(
            _make_llm_for(settings.BULL_LLM_CFG), strategy_tools,
            self._prompts["bull_analyst"]["system_message"], name="BullAnalyst",
        )
        bear_agent          = create_strategy_agent(
            _make_llm_for(settings.BEAR_LLM_CFG), strategy_tools,
            self._prompts["bear_analyst"]["system_message"], name="BearAnalyst",
        )
        leader_llm          = _make_llm_for(settings.LEADER_LLM_CFG)
        self._leader_llm    = leader_llm
        self._save_report_tool = make_save_report_tool(settings.REPORTS_DIR)
        leader_agent        = create_leader_agent(
            leader_llm, leader_tools,
            self._prompts["leader"]["system_message"],
        )

        # --- Per-call timeout + retry helpers ---

        _timeout     = settings.NODE_TIMEOUT
        _retries     = settings.NODE_LLM_RETRIES
        _retry_delay = settings.NODE_LLM_RETRY_DELAY

        _TRANSIENT = ("timeout", "connection", "rate limit", "overloaded", "503", "502", "429")

        def _is_transient_error(exc: Exception) -> bool:
            return any(p in str(exc).lower() for p in _TRANSIENT)

        async def _invoke(agent, prompt: str, node_name: str = "") -> str:
            """Invoke a deepagents agent with per-call timeout + retry on transient errors."""
            import time as _time
            total = _retries + 1
            last_exc: Exception | None = None
            for attempt in range(total):
                _t0 = _time.monotonic()
                try:
                    # Tag all tool calls within this invocation with a unique run_id
                    # so tools_debug.log entries can be grouped by exact node execution.
                    # Join keys: run_id (unique per invoke) → node → session
                    _run_id = str(_uuid4())[:8]  # short 8-char prefix is enough
                    set_tool_log_context(node_name or "unknown", _active_session.get(), _run_id)
                    logger.info("[NODE_START] node=%s session=%s run_id=%s attempt=%d",
                                node_name or "unknown", _active_session.get(), _run_id, attempt + 1)
                    result = await asyncio.wait_for(
                        agent.ainvoke({"messages": [HumanMessage(content=prompt)]}),
                        timeout=_timeout,
                    )
                    elapsed = _time.monotonic() - _t0
                    if node_name:
                        logger.info("[TIMING] node=%s elapsed=%.1fs attempt=%d", node_name, elapsed, attempt + 1)
                    return _last_ai_text(result)
                except asyncio.TimeoutError as exc:
                    last_exc = exc
                    elapsed = _time.monotonic() - _t0
                    logger.warning(
                        "[TIMEOUT] node=%s elapsed=%.1fs timeout=%ss attempt=%d/%d",
                        node_name or "unknown", elapsed, _timeout, attempt + 1, total,
                    )
                except Exception as exc:
                    if _is_transient_error(exc):
                        last_exc = exc
                        logger.warning(
                            "[TRANSIENT] node=%s attempt=%d/%d error=%s",
                            node_name or "unknown", attempt + 1, total, exc,
                        )
                    else:
                        raise  # non-transient — propagate immediately
                if attempt < _retries:
                    await asyncio.sleep(_retry_delay)
            assert last_exc is not None
            raise last_exc

        async def _invoke_with_trace(agent, prompt: str, node_name: str = "") -> tuple[str, str]:
            """Like _invoke but also returns the tool call trace string.

            Returns (text_output, tool_trace) so callers can store the trace
            in TradingState for the verifier to inspect.
            """
            import time as _time
            total = _retries + 1
            last_exc: Exception | None = None
            for attempt in range(total):
                _t0 = _time.monotonic()
                try:
                    _run_id = str(_uuid4())[:8]
                    set_tool_log_context(node_name or "unknown", _active_session.get(), _run_id)
                    logger.info("[NODE_START] node=%s session=%s run_id=%s attempt=%d",
                                node_name or "unknown", _active_session.get(), _run_id, attempt + 1)
                    result = await asyncio.wait_for(
                        agent.ainvoke({"messages": [HumanMessage(content=prompt)]}),
                        timeout=_timeout,
                    )
                    elapsed = _time.monotonic() - _t0
                    if node_name:
                        logger.info("[TIMING] node=%s elapsed=%.1fs attempt=%d", node_name, elapsed, attempt + 1)
                    return _last_ai_text(result), _extract_tool_trace(result)
                except asyncio.TimeoutError as exc:
                    last_exc = exc
                    elapsed = _time.monotonic() - _t0
                    logger.warning(
                        "[TIMEOUT] node=%s elapsed=%.1fs timeout=%ss attempt=%d/%d",
                        node_name or "unknown", elapsed, _timeout, attempt + 1, total,
                    )
                except Exception as exc:
                    if _is_transient_error(exc):
                        last_exc = exc
                        logger.warning(
                            "[TRANSIENT] node=%s attempt=%d/%d error=%s",
                            node_name or "unknown", attempt + 1, total, exc,
                        )
                    else:
                        raise
                if attempt < _retries:
                    await asyncio.sleep(_retry_delay)
            assert last_exc is not None
            raise last_exc

        # --- Node functions ---

        async def node_leader_intake(state: TradingState) -> dict:
            question = state.get('question', '')
            history  = state.get('history', '')
            prompt = (
                f"User question: {question}\n\n"
                f"Conversation history (if any):\n{history}\n\n"
                "You must do TWO things:\n\n"
                "1. CLASSIFY the request into exactly one flow type:\n"
                "   [FLOW:full]           — new ticker/market question requiring full research\n"
                "                           (analysis + bull/bear debate + strategy synthesis)\n"
                "   [FLOW:analysis_only]  — analysis/report request; no debate needed\n"
                "                           (run analysis room, then straight to synthesis)\n"
                "   [FLOW:strategy_only]  — follow-up or revision; analysis already done\n"
                "                           (skip analysis room, go straight to strategy room)\n"
                "   [FLOW:direct]         — reply immediately without any room; answer the\n"
                "                           question directly yourself. Use when the request\n"
                "                           does not need macro/technical data, debate, or\n"
                "                           strategy synthesis, only use your memory or your own knowledge. Examples:\n"
                "                             • Greeting / small talk (chào, cảm ơn, ok)\n"
                "                             • Definition / concept (RS, MA20, P/E là gì)\n"
                "                             • Bot / system status (bot ổn không, có lệnh mở)\n"
                "                             • Static lookup (HPG thuộc ngành nào, giờ mở cửa)\n"
                "                             • Health / error check (có lỗi gì, status vận hành)\n"
                "                           For [FLOW:direct], start with the tag and reply\n"
                "                           concisely (1-5 bullets) right after it.\n\n"
                "2. Either:\n"
                "   (A) Issue a clear analysis directive for the chosen flow, OR\n"
                "   (B) If genuinely ambiguous, ask 1-2 clarifying questions.\n"
                "       In that case MUST start with [NEEDS CLARIFICATION].\n\n"
                "ALWAYS include the [FLOW:xxx] tag at the very start of your response.\n"
                "You do NOT need to get info to analysis so do not need any stock market tool call here"
            )
            text = await _invoke(leader_agent, prompt, node_name="leader_intake")
            # Parse flow type
            flow_match = re.search(r"\[FLOW:(full|analysis_only|strategy_only|direct)\]", text, re.IGNORECASE)
            flow_type  = flow_match.group(1).lower() if flow_match else "full"
            # Auto-demote safety net: if leader chose full/analysis_only but the
            # directive text has no ticker and no analysis verb, demote to direct.
            # Catches over-routing of greetings / definitions / status checks.
            if (
                settings.INTAKE_AUTO_DEMOTE
                and flow_type in ("full", "analysis_only")
                and not _looks_like_analysis_request(text)
            ):
                logger.info(
                    "[INTAKE] auto-demote %s→direct (no ticker/verb in directive). question='%s'",
                    flow_type, question[:80],
                )
                flow_type = "direct"
            needs_clarif = "[NEEDS CLARIFICATION]" in text or "[CẦN LÀM RÕ]" in text
            logger.info(
                "[INTAKE] flow=%s needs_clarification=%s question='%s'",
                flow_type, needs_clarif, question[:80],
            )
            if not flow_match:
                logger.warning("[INTAKE] flow tag missing — defaulted to 'full'. question='%s'", question[:80])
            return {
                "leader_intake":       text,
                "needs_clarification": needs_clarif,
                "flow_type":           flow_type,
                "debate_round":        0,
                "debate_complete":     False,
                "debate_transcript":   "",
                "debate_summary":      "",
                "bull_last":           "",
                "bear_last":           "",
                "arbitration_result":  "",
                "synthesis_round":     0,
                "review_approved":     False,
            }

        async def node_lead_analysis(state: TradingState) -> dict:
            """
            Analysis room coordinator:
            1. Decide routing — which analysts are needed (both / macro-only / technical-only)
            2. Run selected analysts concurrently via asyncio.gather
            3. Synthesize their outputs into one clean brief for the strategy room
            """
            question  = state.get("question", "")
            directive = state.get("leader_intake", "")

            # --- Step 1: routing decision (fast, no tools) ---
            routing_prompt = (
                f"User question: {question}\n\nLeader directive:\n{directive}\n\n"
                "Decide which specialist analyses are needed.\n"
                "Reply with EXACTLY one of (nothing else on that line):\n"
                "  BOTH          — macro context AND chart/price data needed\n"
                "  MACRO_ONLY    — purely macro/fundamental question, no chart needed\n"
                "  TECHNICAL_ONLY — purely chart/price question, macro not relevant\n"
                "Then add one sentence justification."
            )
            routing_text = (await _invoke(lead_analysis_agent, routing_prompt, node_name="lead_analysis_routing")).upper()
            run_macro = "MACRO_ONLY" in routing_text or "BOTH" in routing_text
            run_tech  = "TECHNICAL_ONLY" in routing_text or "BOTH" in routing_text
            if not run_macro and not run_tech:          # fallback: run both
                run_macro = run_tech = True

            logger.info(
                "LeadAnalysis routing: macro=%s technical=%s | question='%s'",
                run_macro, run_tech, question[:60],
            )

            # --- Step 2: build sub-prompts and run concurrently ---
            history = state.get("history", "")
            _hist   = f"Prior conversation context:\n{history}\n\n" if history else ""

            # Step 2b: if previous verification found data gaps, brief lead_analysis to fill them first
            verify_notes = state.get("analysis_verify_notes", "")
            gap_fill_addendum = ""
            gap_fill_macro_trace = ""
            gap_fill_tech_trace = ""
            if verify_notes:
                gap_fill_prompt = (
                    f"User question: {question}\n\n"
                    f"Previous analysis was rejected by the data verification room due to the following issues:\n"
                    f"{verify_notes}\n\n"
                    "Please use tools to re-fetch the missing/incorrect data. "
                    "Clearly state [Source: <tool>, <date>] after each figure. "
                    "Only provide the data points that need to be supplemented, no further analysis is required."
                )
                gap_fill_addendum, gap_fill_trace = await _invoke_with_trace(
                    lead_analysis_agent, gap_fill_prompt, node_name="lead_analysis_gap_fill"
                )
                # Split the gap-fill trace by tool category so the next
                # analysis_verify cycle sees the new tool calls under the
                # correct analyst. Without this split, the verifier would
                # read an empty macro/tech trace on the next cycle and keep
                # failing even though data was just fetched.
                gap_fill_macro_trace, gap_fill_tech_trace = _split_trace_by_domain(gap_fill_trace)
                logger.info(
                    "[ANALYSIS] gap-fill complete (verify_count=%d, macro_calls=%d, tech_calls=%d)",
                    state.get("analysis_verify_count", 0),
                    0 if gap_fill_macro_trace == "(no tool calls made)" else gap_fill_macro_trace.count("\n") + 1,
                    0 if gap_fill_tech_trace == "(no tool calls made)" else gap_fill_tech_trace.count("\n") + 1,
                )

            macro_prompt = (
                f"Original question: {question}\n\n"
                f"{_hist}"
                f"Leader directive:\n{directive}\n\n"
                "Task: Collect and analyze relevant macro factors "
                "(interest rates, FX, foreign capital flows, CPI, etc.) for the question above."
                + (f"\n\nGap-fill data (additional data already fetched):\n{gap_fill_addendum}" if gap_fill_addendum else "")
            )
            tech_prompt = (
                f"Original question: {question}\n\n"
                f"{_hist}"
                f"Leader directive:\n{directive}\n\n"
                "Task: Collect price/volume data and perform technical analysis "
                "(patterns, S/R levels, indicators, entry/exit) for the question above."
                + (f"\n\nGap-fill data (additional data already fetched):\n{gap_fill_addendum}" if gap_fill_addendum else "")
            )

            coros = []
            if run_macro:
                coros.append(_invoke_with_trace(macro_agent, macro_prompt, node_name="macro_analyst"))
            if run_tech:
                coros.append(_invoke_with_trace(tech_agent, tech_prompt, node_name="technical_analyst"))

            results = await asyncio.gather(*coros)

            idx = 0
            macro_text, macro_trace = results[idx] if run_macro else ("Macro analysis not needed for this question.", "(skipped)")
            if run_macro:
                idx += 1
            tech_text, tech_trace  = results[idx] if run_tech  else ("Technical analysis not needed for this question.", "(skipped)")

            # Merge any gap-fill tool calls (from step 2b) into the per-analyst
            # trace so the next analysis_verify cycle can see them. Without
            # this, the gap-fill calls happen in lead_analysis_agent (not the
            # macro/tech agents), so the existing macro/tech trace would stay
            # empty on the next cycle and the verifier would re-fail.
            if gap_fill_macro_trace and gap_fill_macro_trace != "(no tool calls made)":
                prefix = macro_trace if macro_trace and macro_trace != "(no tool calls made)" else ""
                if prefix and not prefix.endswith("\n"):
                    prefix += "\n"
                macro_trace = prefix + gap_fill_macro_trace
            if gap_fill_tech_trace and gap_fill_tech_trace != "(no tool calls made)":
                prefix = tech_trace if tech_trace and tech_trace != "(no tool calls made)" else ""
                if prefix and not prefix.endswith("\n"):
                    prefix += "\n"
                tech_trace = prefix + gap_fill_tech_trace

            # --- Step 3: synthesis brief for strategy room ---
            synthesis_prompt = (
                f"User question: {question}\n\n"
                f"MacroAnalyst result:\n{macro_text}\n\n"
                f"TechnicalAnalyst result:\n{tech_text}\n\n"
                "Synthesize the above two results into a professional brief (800-1,000 words) "
                "keeping all important figures (price, %, volume, billion VND value). "
                "for the strategy room. Clearly state if macro and technical analysis contradict each other. "
                "End with a '➡️ FOCUS FOR STRATEGY ROOM:' section with 1-2 key points."
            )
            brief_text = await _invoke(lead_analysis_agent, synthesis_prompt, node_name="lead_analysis_synthesis")

            return {
                "macro_analysis":        macro_text,
                "technical_analysis":    tech_text,
                "macro_tool_trace":      macro_trace,
                "tech_tool_trace":       tech_trace,
                "lead_analysis":         brief_text,
                "analysis_verify_notes": "",   # reset notes; set by node_analysis_verify if issues found
            }

        async def node_analysis_verify(state: TradingState) -> dict:
            """Verify that analyst outputs contain sourced, dated data points.

            Uses lead_analysis_agent to audit macro_analysis + technical_analysis.
            If all data is properly cited → [VERIFIED].
            If gaps found → [DATA_ISSUES] with specific list; triggers a retry.
            After MAX_ANALYSIS_VERIFY_RETRIES retries, proceeds regardless with warnings.
            """
            macro_text   = state.get("macro_analysis", "")
            tech_text    = state.get("technical_analysis", "")
            macro_trace  = state.get("macro_tool_trace", "(no trace)")
            tech_trace   = state.get("tech_tool_trace", "(no trace)")
            verify_count = state.get("analysis_verify_count", 0)

            verify_prompt = (
                f"You are the HEAD OF ANALYSIS checking the work of 2 analysts. Current date: {settings.CURRENT_DATE}\n\n"
                "TASK: Check if each analyst followed the process correctly — based entirely on the actual list of tool calls and analysis results below. "
                "DO NOT call any additional tools. DO NOT re-verify the figures yourself.\n\n"
                "=== MACRO ANALYST — ACTUAL TOOL CALLS ===\n"
                f"{macro_trace}\n\n"
                "=== MACRO ANALYST — ANALYSIS RESULTS ===\n"
                f"{macro_text}\n\n"
                "=== TECHNICAL ANALYST — ACTUAL TOOL CALLS ===\n"
                f"{tech_trace}\n\n"
                "=== TECHNICAL ANALYST — ANALYSIS RESULTS ===\n"
                f"{tech_text}\n\n"
                "CHECK THE FOLLOWING CRITERIA (based only on what is seen above):\n\n"
                "[A] WERE ENOUGH TOOLS CALLED?\n"
                "  • MacroAnalyst: must call at least 1 tool for foreign capital flow, 1 tool for interest rates/macro\n"
                "  • TechnicalAnalyst: must call at least 1 tool for price/quote, 1 tool for volume or indicators\n"
                "  • If a tool returns an error/empty → the analyst must try an alternative; if not → error\n\n"
                "[B] WERE TOOLS CALLED CORRECTLY?\n"
                "  • Are the date/ticker parameters consistent with the original question\n"
                "  • If a tool returns a known error (e.g., ticker not found, API limit) → was another tool used as a fallback\n\n"
                "[C] DOES THE DATA MATCH THE CONCLUSION?\n"
                "  • Do the figures in the analysis results appear in the tool results\n"
                "  • If an analyst provides figures but there is no corresponding tool call → suspect hallucination\n\n"
                "[D] IS THE DATA DATE APPROPRIATE?\n"
                "  • Data older than 3 days vs the current date → needs update\n\n"
                "OUTPUT:\n"
                "• If all criteria A-D are met:\n"
                "  → Start with: [VERIFIED]\n"
                "  → 1-line summary: how many tools were called, results are okay.\n\n"
                "• If there are issues:\n"
                "  → Start with: [DATA_ISSUES]\n"
                "  → List concisely in this format:\n"
                "     • [MACRO/TECHNICAL][A/B/C/D] <specific issue description>\n"
                "       → Redo: <specify exactly which tool to call or which parameter to fix>\n"
                "  Only list actual issues — do not fabricate issues not present in the trace."
            )

            text = await _invoke(lead_analysis_agent, verify_prompt, node_name="analysis_verify")
            verified = text.strip().upper().startswith("[VERIFIED]")
            new_count = verify_count + 1

            if verified:
                logger.info("[VERIFY] data verified on cycle %d", new_count)
                return {"analysis_verify_count": new_count, "analysis_verify_notes": ""}

            # Strip tag, store notes for retry or warning injection
            notes = re.sub(r"^\[DATA_ISSUES\]\s*", "", text.strip(), flags=re.IGNORECASE).strip()
            logger.warning("[VERIFY] data issues found (cycle=%d): %s", new_count, notes[:200])

            if new_count > settings.MAX_ANALYSIS_VERIFY_RETRIES:
                # Exhausted retries — inject warning into lead_analysis brief and proceed
                warning_header = (
                    f"⚠️ **Data Warning (checked {new_count} times, issues remain):**\n"
                    f"{notes}\n\n"
                    "---\n"
                )
                amended_brief = warning_header + state.get("lead_analysis", "")
                logger.warning("[VERIFY] max retries exhausted — proceeding with warnings injected into brief")
                return {
                    "analysis_verify_count": new_count,
                    "analysis_verify_notes": "",       # clear so routing proceeds forward
                    "lead_analysis": amended_brief,
                }

            return {"analysis_verify_count": new_count, "analysis_verify_notes": notes}

        async def node_bull_argument(state: TradingState) -> dict:
            round_num = state.get("debate_round", 0) + 1
            debate_transcript = state.get("debate_transcript", "")
            context = (
                f"Original question: {state.get('question', '')}\n\n"
                f"--- Analysis team brief ---\n"
                f"{state.get('lead_analysis', state.get('macro_analysis', 'N/A'))}\n\n"
            )
            if debate_transcript:
                context += (
                    "--- Debate transcript so far ---\n"
                    f"{debate_transcript}\n\n"
                )
            context += (
                f"This is round {round_num}/{settings.MAX_DEBATE_ROUNDS}.\n"
                "Present your BULLISH case based on the data above. "
                "If Bear has already spoken in the transcript, you MUST respond to Bear's strongest open points first before adding any new argument. "
                "Do not repeat your own earlier points unless you are directly defending them."
            )
            bull_text = await _invoke(bull_agent, context, node_name="bull_argument")
            transcript = debate_transcript.strip()
            if transcript:
                transcript += "\n\n"
            transcript += f"## Round {round_num} — Bull\n{bull_text.strip()}"
            return {
                "bull_last": bull_text,
                "debate_round": round_num,
                "debate_transcript": transcript,
            }

        async def node_bear_argument(state: TradingState) -> dict:
            round_num = state.get("debate_round", 1)
            debate_transcript = state.get("debate_transcript", "")
            context = (
                f"Original question: {state.get('question', '')}\n\n"
                f"--- Analysis team brief ---\n"
                f"{state.get('lead_analysis', state.get('macro_analysis', 'N/A'))}\n\n"
            )
            if debate_transcript:
                context += (
                    "--- Debate transcript so far ---\n"
                    f"{debate_transcript}\n\n"
                )
            context += (
                f"You are now replying in round {round_num}/{settings.MAX_DEBATE_ROUNDS}.\n"
                "Counter Bull's argument and present your BEARISH case / downside risks. "
                "You MUST respond to Bull's strongest open points in the transcript before introducing new arguments. "
                "Do not repeat your own earlier points unless you are directly defending them."
            )
            bear_text = await _invoke(bear_agent, context, node_name="bear_argument")
            transcript = debate_transcript.strip()
            if transcript:
                transcript += "\n\n"
            transcript += f"## Round {round_num} — Bear\n{bear_text.strip()}"
            return {
                "bear_last": bear_text,
                "debate_transcript": transcript,
            }

        async def node_arbitration(state: TradingState) -> dict:
            round_num = state.get("debate_round", 1)
            debate_transcript = state.get("debate_transcript", "")
            prompt = (
                f"Original question: {state.get('question', '')}\n\n"
                f"Round {round_num}/{settings.MAX_DEBATE_ROUNDS}.\n\n"
                f"=== FULL DEBATE TRANSCRIPT ===\n{debate_transcript or '(empty)'}\n\n"
                f"=== LATEST ROUND SNAPSHOT ===\n"
                f"BULL:\n{state.get('bull_last', '')}\n\n"
                f"BEAR:\n{state.get('bear_last', '')}\n\n"
                "As ARBITRATOR:\n"
                "- Evaluate whether NEW arguments were raised or just repetition.\n"
                "- Identify the strongest unresolved disagreement, if any.\n"
                "- TO CONTINUE: start with [CONTINUE DEBATE] + the specific unresolved point that both sides must address next.\n"
                "- TO END: start with [END DEBATE] + concise reasoning.\n"
                f"If max rounds reached ({settings.MAX_DEBATE_ROUNDS}) or no new arguments remain → MUST end."
            )
            text = await _invoke(leader_agent, prompt, node_name="arbitration")
            transcript = debate_transcript.strip()
            if transcript:
                transcript += "\n\n"
            transcript += f"## Round {round_num} — Arbitration\n{text.strip()}"
            forced_end = round_num >= settings.MAX_DEBATE_ROUNDS
            is_done = (
                "[END DEBATE]" in text
                or "[KẾT THÚC TRANH LUẬN]" in text  # backward compat
                or forced_end
            )
            debate_summary = ""
            if is_done:
                summary_prompt = (
                    f"Original question: {state.get('question', '')}\n\n"
                    f"=== Analysis team brief ===\n{state.get('lead_analysis', state.get('macro_analysis', 'N/A'))}\n\n"
                    f"=== Full debate transcript ===\n{transcript}\n\n"
                    f"=== Final arbitration result ===\n{text}\n\n"
                    "Briefly summarize the debate results for the strategy room and future follow-ups. "
                    "Must include 4 short parts:\n"
                    "1. Strongest Bull case\n"
                    "2. Strongest Bear case\n"
                    "3. Arbitrator's final point\n"
                    "4. Action implications / conditions to monitor\n"
                    "Keep it concise, prioritizing points that drive action."
                )
                total = _retries + 1
                last_exc: Exception | None = None
                for attempt in range(total):
                    try:
                        resp = await asyncio.wait_for(
                            leader_llm.ainvoke([HumanMessage(content=summary_prompt)]),
                            timeout=_timeout,
                        )
                        debate_summary = (resp.content or "").strip()
                        break
                    except asyncio.TimeoutError as exc:
                        last_exc = exc
                        logger.warning("[DEBATE] summary timeout attempt=%d/%d", attempt + 1, total)
                    except Exception as exc:
                        if _is_transient_error(exc):
                            last_exc = exc
                            logger.warning("[DEBATE] summary transient attempt=%d/%d error=%s", attempt + 1, total, exc)
                        else:
                            logger.warning("[DEBATE] summary failed: %s", exc)
                            break
                    if attempt < _retries:
                        await asyncio.sleep(_retry_delay)
                if not debate_summary and last_exc is not None:
                    logger.warning("[DEBATE] summary unavailable after retries: %s", last_exc)
                    debate_summary = text.strip()
                elif not debate_summary:
                    debate_summary = text.strip()
                logger.info("[DEBATE] summary_created=%s", bool(debate_summary))
            logger.info(
                "[DEBATE] round=%d/%d decision=%s forced=%s transcript_chars=%d summary_chars=%d",
                round_num,
                settings.MAX_DEBATE_ROUNDS,
                "END" if is_done else "CONTINUE",
                forced_end,
                len(transcript),
                len(debate_summary),
            )
            return {
                "arbitration_result": text,
                "debate_complete": is_done,
                "debate_transcript": transcript,
                "debate_summary": debate_summary,
            }

        async def node_strategy_synthesis(state: TradingState) -> dict:
            round_num = state.get("synthesis_round", 0) + 1
            feedback  = state.get("review_feedback", "")
            flow_type = state.get("flow_type", "full")

            has_debate = bool(state.get("bull_last") or state.get("bear_last"))
            has_analysis = bool(state.get("lead_analysis") or state.get("macro_analysis"))
            portfolio_context = _build_portfolio_context(
                state.get("question", ""),
                state.get("lead_analysis", ""),
                state.get("macro_analysis", ""),
                state.get("technical_analysis", ""),
            )

            prompt = f"User question: {state.get('question', '')}\n\n"
            prompt += f"=== PORTFOLIO CONTEXT ===\n{portfolio_context}\n\n"
            prompt += (
                "Portfolio-aware decision rules:\n"
                "- If user has no position: focus on entry conditions, starter size, invalidation, and why waiting may be better.\n"
                "- If user is already holding: give explicit action for the existing position first.\n"
                "- If user is holding and overweight: address concentration risk before any add recommendation.\n"
                "- If user is holding and asking about losses: do NOT default to averaging down without strong confirmation.\n\n"
            )

            if has_analysis:
                prompt += (
                    f"=== ANALYSIS TEAM BRIEF ===\n{state.get('lead_analysis', '')}\n\n"
                    f"=== MACRO (full) ===\n{state.get('macro_analysis', 'N/A')}\n\n"
                    f"=== TECHNICAL (full) ===\n{state.get('technical_analysis', 'N/A')}\n\n"
                )
            else:
                hist = state.get('history', '')
                if hist:
                    prompt += f"=== CONVERSATION HISTORY ===\n{hist}\n\n"

            if has_debate:
                debate_summary = state.get("debate_summary", "").strip()
                if debate_summary:
                    prompt += f"=== STRATEGY DEBATE SUMMARY ===\n{debate_summary}\n\n"
                else:
                    prompt += (
                        f"=== STRATEGY DEBATE ===\n"
                        f"Bull case:\n{state.get('bull_last', 'N/A')}\n\n"
                        f"Bear case:\n{state.get('bear_last', 'N/A')}\n\n"
                        f"Arbitration:\n{state.get('arbitration_result', 'N/A')}\n\n"
                    )
                if state.get("debate_transcript") and not debate_summary:
                    prompt += f"=== DEBATE TRANSCRIPT ===\n{state.get('debate_transcript', '')}\n\n"

            if feedback:
                prompt += (
                    f"=== LEADER'S REVISION REQUEST (attempt {round_num}) ===\n"
                    f"{feedback}\n\n"
                    "Address ALL points above before rewriting.\n\n"
                )

            prompt += (
                "As Strategy Room Head, write the most appropriate response given the available inputs.\n"
                "Use the tools to fetch any missing data before writing.\n"
                "End with: [SYNTHESIS COMPLETE]"
            )
            logger.info("[PORTFOLIO] context=%s", portfolio_context.replace("\n", " | ")[:400])
            logger.info(
                "[SYNTHESIS] attempt=%d/%d flow=%s has_debate=%s has_analysis=%s has_feedback=%s",
                round_num, settings.MAX_SYNTHESIS_ROUNDS, flow_type, has_debate, has_analysis, bool(feedback),
            )
            draft = await _invoke(lead_strategy_agent, prompt, node_name="strategy_synthesis")
            return {"synthesis_draft": draft, "synthesis_round": round_num, "portfolio_context": portfolio_context}

        async def node_leader_review(state: TradingState) -> dict:
            question         = state.get("question", "")
            draft            = state.get("synthesis_draft", "")
            synthesis_round  = state.get("synthesis_round", 1)
            portfolio_context = state.get("portfolio_context", "")
            review_prompt = (
                f"User's original question: \"{question}\"\n\n"
                f"Portfolio context inferred for this question:\n{portfolio_context or 'Portfolio context unavailable'}\n\n"
                f"Strategy Room synthesis (attempt {synthesis_round}/{settings.MAX_SYNTHESIS_ROUNDS}):\n"
                f"{draft}\n\n"
                "You are a senior investment expert doing a final quality review before this report reaches the user.\n\n"
                "PORTFOLIO-AWARE CHECKS (important when portfolio context is present):\n"
                "  • Does the report clearly say whether the user already holds the ticker or not?\n"
                "  • If the user already holds it, does the recommendation act on the CURRENT position first instead of giving only generic entry advice?\n"
                "  • If a current avg price / % NAV / stop-loss is available, does the recommendation use it correctly?\n"
                "  • If the holding state is overweight, does the report mention concentration risk before suggesting any add?\n"
                "  • If the user is holding and under pressure / in loss, does the report avoid reflexive average-down advice without strong confirmation?\n\n"
                "STEP 1 — Infer what the question actually requires:\n"
                "  Based on the original question, determine what a complete answer looks like:\n"
                "  • Specific ticker with trading intent → needs entry price, stop-loss, R/R ratio\n"
                "  • Market or sector overview → needs macro context + outlook; entry price not required\n"
                "  • Pure macro question → focus on macro factors; no trade recommendation needed\n"
                "  • Portfolio strategy → needs allocation guidance and overall risk management\n"
                "  • Other → derive the appropriate expectations yourself\n\n"
                "STEP 2 — Assess quality against those expectations:\n"
                "  For each section present in the report, ask:\n"
                "  • Does every argument have concrete evidence (numbers, named patterns, named indicators, dates)?\n"
                "  • Are risks quantified (%, price levels, conditions) — not just listed?\n"
                "  • Is the conclusion actionable — does the reader know exactly what to do next?\n"
                "  • Is there any content that is generic filler with no supporting evidence?\n\n"
                "STEP 3 — Decision:\n\n"
                "If the report meets the expectations for this type of question and quality is sufficient:\n"
                "  → Output: [APPROVED]\n"
                "  → Rewrite the full report with tighter, more professional language if needed.\n\n"
                "If NOT acceptable:\n"
                "  → Output: [REVISION NEEDED]\n"
                "  → Briefly explain: what this question type requires, and where the report falls short.\n"
                "  → List at most 5 specific issues in this format:\n"
                "     • [Section] Issue: <description> → Needs: <exactly what is missing>\n"
                "  → Prioritize issues that most affect the user's decision."
            )
            text = await _invoke(leader_agent, review_prompt, node_name="leader_review")
            approved = "[APPROVED]" in text[:80]
            if approved:
                final = re.sub(r"\[APPROVED\]\s*", "", text, count=1).strip()
                logger.info("[REVIEW] outcome=APPROVED attempt=%d question='%s'", synthesis_round, question[:80])
                return {"final_answer": final, "review_approved": True, "review_feedback": ""}
            # Max rounds exhausted — accept draft as-is to avoid infinite loop
            if synthesis_round >= settings.MAX_SYNTHESIS_ROUNDS:
                logger.warning(
                    "[REVIEW] outcome=MAX_ROUNDS_EXHAUSTED attempt=%d — using last draft. question='%s'",
                    synthesis_round, question[:80],
                )
                return {"final_answer": draft, "review_approved": True}
            feedback = re.sub(r"\[REVISION NEEDED\]\s*", "", text, count=1).strip()
            logger.warning(
                "[REVIEW] outcome=REVISION_NEEDED attempt=%d question='%s'",
                synthesis_round, question[:80],
            )
            return {"review_feedback": feedback, "review_approved": False}

        async def node_memory_save(state: TradingState) -> dict:
            """
            After every completed session, persist 5 independent artifacts in parallel:

            1. Session review  (memory/sessions/YYYY-MM-DD_<slug>.md)
            2. Portfolio       (memory/portfolio/AGENTS.md  — only when a trade is made)
            3. Trading plan    (memory/trading_plan/AGENTS.md — only when strategy evolves)
            4. Skill           (memory/skills/<cat>/<name>/SKILL.md — reusable workflows only)
            5. Report file     (reports/ — only when user explicitly requested one)

            Uses raw leader_llm (no deepagents overhead) since these tasks need only
            LLM reasoning, not tools or injected memory.
            All 5 tasks run concurrently via asyncio.gather.
            """
            question     = state.get("question", "")
            final_answer = state.get("final_answer", "")
            today_iso    = date.today().strftime("%Y-%m-%d")
            slug         = re.sub(r"[^a-z0-9]+", "_", question[:40].lower()).strip("_")

            # Read memory files upfront (sync I/O — fast)
            portfolio_content    = (MEMORY_ROOT / "portfolio"    / "AGENTS.md").read_text(encoding="utf-8")
            trading_plan_content = (MEMORY_ROOT / "trading_plan" / "AGENTS.md").read_text(encoding="utf-8")

            # Raw LLM helper — no deepagents wrapper, lighter than leader_agent
            async def _llm(prompt: str) -> str:
                total = _retries + 1
                last_exc: Exception | None = None
                for attempt in range(total):
                    try:
                        resp = await asyncio.wait_for(
                            leader_llm.ainvoke([HumanMessage(content=prompt)]),
                            timeout=_timeout,
                        )
                        return (resp.content or "").strip()
                    except asyncio.TimeoutError as exc:
                        last_exc = exc
                        logger.warning("Memory _llm: timeout attempt %d/%d", attempt + 1, total)
                    except Exception as exc:
                        if _is_transient_error(exc):
                            last_exc = exc
                            logger.warning("Memory _llm: transient error attempt %d/%d: %s", attempt + 1, total, exc)
                        else:
                            logger.warning("Memory task LLM call failed: %s", exc)
                            return ""
                    if attempt < _retries:
                        await asyncio.sleep(_retry_delay)
                logger.warning("Memory _llm: all %d attempts failed: %s", total, last_exc)
                return ""

            # --- Task 1: extract session lessons ---
            async def _task_lessons() -> str:
                debate_notes = state.get('debate_summary', '').strip()
                if not debate_notes:
                    debate_notes = (
                        f"Bull arguments:\n{state.get('bull_last', '')[:800]}\n\n"
                        f"Bear arguments:\n{state.get('bear_last', '')[:800]}"
                    )
                return await _llm(
                    f"Session topic: {question}\n\n"
                    f"Final answer summary:\n{final_answer[:1500]}\n\n"
                    f"Debate conclusion:\n{debate_notes}\n\n"
                    "Extract 3–5 CONCISE lessons/insights from this session for future reference.\n"
                    "Format each lesson as a single line starting with '- '.\n"
                    "Focus on: what worked, risks identified, key data points,\n"
                    "and any decision made (buy/sell/hold + ticker + price if applicable).\n"
                    "Keep the total under 400 words."
                )

            # --- Task 2: portfolio update ---
            async def _task_portfolio() -> str:
                return await _llm(
                    f"Current portfolio:\n{portfolio_content}\n\n"
                    f"Final recommendation from this session:\n{final_answer[:2000]}\n\n"
                    "Based on the recommendation above, produce an UPDATED portfolio file.\n"
                    "Rules:\n"
                    "- BUY a ticker: add or update that line.\n"
                    "- SELL / EXIT: remove that ticker line.\n"
                    "- HOLD / WAIT / no trade: output exactly: [NO CHANGE]\n"
                    "- Keep all other existing positions unchanged.\n"
                    "- Format each position as:\n"
                    "  - <TICKER>: <SHARES> shares @ avg <PRICE> | <PCT>% NAV | SL: <SL_PRICE>\n"
                    "Output ONLY the updated file content (starting with '# Current Portfolio'),\n"
                    "or output [NO CHANGE] if nothing changed."
                )

            # --- Task 3: trading plan update ---
            async def _task_trading_plan() -> str:
                return await _llm(
                    f"Current trading plan:\n{trading_plan_content}\n\n"
                    f"Session topic: {question}\n\n"
                    f"Final answer / recommendation:\n{final_answer[:2000]}\n\n"
                    "Determine if any part of the trading plan needs updating based on this session.\n"
                    "Consider updating if:\n"
                    "- Market outlook changed (new macro data, sentiment shift)\n"
                    "- A ticker was added to or removed from the Watchlist\n"
                    "- Entry/exit rules were refined based on what happened\n"
                    "- A new investment theme emerged or an old theme was abandoned\n"
                    "- User expressed a new preference or hard rule\n"
                    "If changes are needed: output the FULL updated file content\n"
                    "  (starting with '# Trading Plan — Living Strategy Document').\n"
                    "If nothing meaningful changed: output exactly: [NO CHANGE]"
                )

            # --- Task 4: skill derivation (deepagent-based) ---
            # Use a dedicated deepagent that can read full content of existing skills
            # before deciding UPDATE vs CREATE. This prevents the previous limitation
            # where the LLM only saw 1-line descriptions and could overwrite/dup skills.
            _skill_agent = self._get_skill_agent()
            _skill_prompt = (
                f"Session topic: {question}\n\n"
                f"Final answer summary:\n{final_answer[:1500]}\n\n"
                "Decide if a REUSABLE multi-step WORKFLOW emerged from this session.\n"
                "A SKILL IS: a step-by-step procedure useful for MANY future sessions.\n"
                "NOT a skill: ticker-specific facts, one-time lessons, single trade decisions.\n\n"
                "Workflow:\n"
                "1. ls /memory/skills/ — see all categories (shared | analysis | strategy).\n"
                "2. For categories of interest: ls /memory/skills/<category>/ — see existing skills.\n"
                "3. Read full content of any skill whose description looks RELATED. "
                "Do NOT decide UPDATE without reading the full SKILL.md.\n"
                "4. Decide: no_skill | update (existing) | create (new).\n"
                "5. If update/create: write_file the full SKILL.md to the right path.\n"
                "6. Return the structured decision — no prose."
            )

            async def _task_skill() -> str:
                """Run the skill-curator deepagent and return text in legacy format
                (SKILL_ACTION / SKILL_CATEGORY / --- / name / description / --- / body)
                so the downstream parser at the bottom of node_memory_save still works.
                """
                # Fast path: skip deepagent on trivial sessions (greeting, [FLOW:direct])
                # to save 5-15s of latency on every short exchange.
                if not final_answer or len(final_answer) < 200:
                    return "[NO SKILL]"
                if state.get("flow_type") == "direct":
                    return "[NO SKILL]"

                try:
                    result = await asyncio.wait_for(
                        _skill_agent.ainvoke({"messages": [HumanMessage(content=_skill_prompt)]}),
                        timeout=_timeout,
                    )
                    decision = result["structured_response"]
                except asyncio.TimeoutError:
                    logger.warning("Skill agent timed out after %ds", _timeout)
                    return "[NO SKILL]"
                except Exception as exc:
                    logger.warning("Skill agent failed: %s", exc)
                    return "[NO SKILL]"

                # Normalize decision (Pydantic model from response_format)
                action   = (getattr(decision, "action", "") or "").lower()
                category = (getattr(decision, "category", "") or "").lower()
                name     = (getattr(decision, "name", "") or "").strip()
                content  = (getattr(decision, "content", "") or "").strip()

                if action in ("", "no_skill", "skip") or not content:
                    logger.info("Skill decision: no_skill (rationale=%s)",
                                getattr(decision, "rationale", "")[:120])
                    return "[NO SKILL]"

                if category not in ("shared", "analysis", "strategy"):
                    logger.warning("Skill decision: invalid category=%r", category)
                    return "[NO SKILL]"

                if not name:
                    logger.warning("Skill decision: missing name")
                    return "[NO SKILL]"

                # The deepagent should have already written the file via write_file.
                # Verify on disk; if the agent forgot, write it ourselves from the
                # structured response (better than silently dropping the skill).
                skill_path = MEMORY_ROOT / "skills" / category / name / "SKILL.md"
                if not skill_path.exists():
                    skill_path.parent.mkdir(parents=True, exist_ok=True)
                    skill_path.write_text(content, encoding="utf-8")
                    logger.info("Skill %s: fallback write to %s", action, skill_path)
                else:
                    logger.info("Skill %s: agent wrote to %s", action, skill_path)

                logger.info(
                    "Skill %s: /memory/skills/%s/%s — %s",
                    action, category, name,
                    getattr(decision, "rationale", "")[:120],
                )

                # Return legacy text format so the parser below this function
                # (regex over SKILL_ACTION / SKILL_CATEGORY / name:) keeps working
                # without modification.
                return (
                    f"SKILL_ACTION: {action.upper()}\n"
                    f"SKILL_CATEGORY: {category}\n"
                    "---\n"
                    f"name: {name}\n"
                    f"description: {getattr(decision, 'description', '')}\n"
                    "---\n"
                    f"{content}"
                )

            # --- Task 5: report save decision (uses bind_tools, not raw text) ---
            async def _task_report_decision() -> list:
                decision_llm = leader_llm.bind_tools([self._save_report_tool])
                total = _retries + 1
                last_exc: Exception | None = None
                for attempt in range(total):
                    try:
                        resp = await asyncio.wait_for(
                            decision_llm.ainvoke([
                                HumanMessage(content=(
                                    f'User\'s original message: "{question}"\n\n'
                                    "Decide: did the user explicitly ask to CREATE, SAVE, or EXPORT "
                                    "a report / analysis file?\n"
                                    "If YES — call save_report with a descriptive title and the final "
                                    "answer as content.\n"
                                    "If NO — respond with just: SKIP\n\n"
                                    f"Final answer to include in report:\n{final_answer}"
                                ))
                            ]),
                            timeout=_timeout,
                        )
                        return getattr(resp, "tool_calls", None) or []
                    except asyncio.TimeoutError as exc:
                        last_exc = exc
                        logger.warning("Report decision: timeout attempt %d/%d", attempt + 1, total)
                    except Exception as exc:
                        if _is_transient_error(exc):
                            last_exc = exc
                            logger.warning("Report decision: transient error attempt %d/%d: %s", attempt + 1, total, exc)
                        else:
                            logger.warning("Report decision task failed: %s", exc)
                            return []
                    if attempt < _retries:
                        await asyncio.sleep(_retry_delay)
                logger.warning("Report decision: all %d attempts failed: %s", total, last_exc)
                return []

            # Run all 5 tasks concurrently
            raw = await asyncio.gather(
                _task_lessons(),
                _task_portfolio(),
                _task_trading_plan(),
                _task_skill(),
                _task_report_decision(),
                return_exceptions=True,
            )

            def _get(idx: int, default):
                r = raw[idx]
                return default if isinstance(r, BaseException) else r

            lessons_text      = _get(0, "")
            portfolio_text    = _get(1, "")
            trading_plan_text = _get(2, "")
            skill_text        = _get(3, "")
            report_calls      = _get(4, [])

            try:
                # 1. Session review file
                session_file = MEMORY_ROOT / "sessions" / f"{today_iso}_{slug}.md"
                session_file.write_text(
                    f"# Session Review — {today_iso}\n\n"
                    f"**Topic:** {question}\n\n"
                    f"## Lessons Learned\n\n{lessons_text}\n",
                    encoding="utf-8",
                )

                # 2. Portfolio update
                if portfolio_text and "[NO CHANGE]" not in portfolio_text:
                    (MEMORY_ROOT / "portfolio" / "AGENTS.md").write_text(portfolio_text, encoding="utf-8")
                    logger.info("Portfolio updated: %s", question[:60])

                # 3. Trading plan update
                if trading_plan_text and "[NO CHANGE]" not in trading_plan_text:
                    (MEMORY_ROOT / "trading_plan" / "AGENTS.md").write_text(trading_plan_text, encoding="utf-8")
                    logger.info("Trading plan updated: %s", question[:60])

                # 4. Auto-derived skill (CREATE or UPDATE)
                if skill_text and "[NO SKILL]" not in skill_text and "SKILL_CATEGORY:" in skill_text:
                    action_match   = re.search(r"^SKILL_ACTION:\s*(CREATE|UPDATE)", skill_text, re.MULTILINE | re.IGNORECASE)
                    category_match = re.search(r"^SKILL_CATEGORY:\s*(shared|analysis|strategy)", skill_text, re.MULTILINE | re.IGNORECASE)
                    # Strip action/category header lines, keep from first "---" onward
                    skill_content = re.sub(r"^SKILL_ACTION:.*\n?", "", skill_text, flags=re.MULTILINE)
                    skill_content = re.sub(r"^SKILL_CATEGORY:.*\n?", "", skill_content, flags=re.MULTILINE).strip()
                    action   = action_match.group(1).upper()   if action_match   else "CREATE"
                    category = category_match.group(1).lower() if category_match else ""
                    if category in ("shared", "analysis", "strategy"):
                        name_match = re.search(r"^name:\s*(.+)$", skill_content, re.MULTILINE)
                        if name_match:
                            skill_name = name_match.group(1).strip()
                            skill_dir  = MEMORY_ROOT / "skills" / category / skill_name
                            skill_dir.mkdir(parents=True, exist_ok=True)
                            (skill_dir / "SKILL.md").write_text(skill_content.strip(), encoding="utf-8")
                            logger.info("%s skill: /memory/skills/%s/%s", action, category, skill_name)

                logger.info("Session memory written: %s", session_file)

                # 5. Report save (agent-decided)
                for tc in report_calls:
                    if tc["name"] == "save_report":
                        self._save_report_tool.invoke(tc["args"])
                        logger.info("Report saved: %s", tc["args"].get("title", ""))

            except Exception as exc:
                logger.warning("Failed to write session memory files: %s", exc)
            return {}

        # --- Routing conditions ---

        def route_after_intake(state: TradingState) -> str:
            if state.get("needs_clarification"):
                return "__end__"
            flow = state.get("flow_type", "full")
            if flow == "direct":
                return "__end__"          # leader answered inline; skip all rooms
            if flow == "strategy_only":
                return "strategy_synthesis"
            return "lead_analysis"  # full or analysis_only

        def route_after_analysis(state: TradingState) -> str:
            return "analysis_verify"  # always verify before proceeding

        def route_after_verify(state: TradingState) -> str:
            notes = state.get("analysis_verify_notes", "")
            count = state.get("analysis_verify_count", 0)
            if notes and count <= settings.MAX_ANALYSIS_VERIFY_RETRIES:
                return "lead_analysis"  # retry with gap-fill
            # Verified OR exhausted — proceed to strategy
            flow = state.get("flow_type", "full")
            return "strategy_synthesis" if flow == "analysis_only" else "bull_argument"

        def route_after_arbitration(state: TradingState) -> Literal["strategy_synthesis", "bull_argument"]:
            return "strategy_synthesis" if state.get("debate_complete") else "bull_argument"

        def route_after_review(state: TradingState) -> Literal["memory_save", "strategy_synthesis"]:
            return "memory_save" if state.get("review_approved") else "strategy_synthesis"

        # --- Build graph ---

        g = StateGraph(TradingState)
        g.add_node("leader_intake",      node_leader_intake)
        g.add_node("lead_analysis",      node_lead_analysis)
        g.add_node("analysis_verify",    node_analysis_verify)
        g.add_node("bull_argument",      node_bull_argument)
        g.add_node("bear_argument",      node_bear_argument)
        g.add_node("arbitration",        node_arbitration)
        g.add_node("strategy_synthesis", node_strategy_synthesis)
        g.add_node("leader_review",      node_leader_review)
        g.add_node("memory_save",        node_memory_save)

        g.add_edge(START, "leader_intake")
        g.add_conditional_edges(
            "leader_intake", route_after_intake,
            {"__end__": END, "lead_analysis": "lead_analysis", "strategy_synthesis": "strategy_synthesis"},
        )
        g.add_conditional_edges(
            "lead_analysis", route_after_analysis,
            {"analysis_verify": "analysis_verify"},
        )
        g.add_conditional_edges(
            "analysis_verify", route_after_verify,
            {"lead_analysis": "lead_analysis", "bull_argument": "bull_argument", "strategy_synthesis": "strategy_synthesis"},
        )
        g.add_edge("bull_argument",      "bear_argument")
        g.add_edge("bear_argument",      "arbitration")
        g.add_conditional_edges("arbitration",   route_after_arbitration)
        g.add_edge("strategy_synthesis", "leader_review")
        g.add_conditional_edges("leader_review",  route_after_review)
        g.add_edge("memory_save",        END)

        return g.compile()

    # -------------------------------------------------------------------------
    # Public streaming API
    # -------------------------------------------------------------------------

    async def astream(self, inputs: dict) -> AsyncIterator[tuple[str, str]]:
        """
        Run the graph and yield (event_type, text) pairs for each completed node.

        event_type matches keys in NODE_LABELS, plus:
          - "needs_clarification" : leader wants user input
          - "status"              : progress notification while a node is running
          - "error"               : workflow error
        """
        # Status message shown when a node STARTS (before its result arrives)
        _NODE_STATUS: dict[str, str] = {
            "leader_intake":      "📋 *Leader* is receiving the request...",
            "lead_analysis":      "🔬 *Analysis Room* is gathering data (Macro ∥ Technical)...",
            "analysis_verify":    "🔍 *Data Verifier* is checking figures...",
            "bull_argument":      "🐂 *BullAnalyst* is arguing...",
            "bear_argument":      "🐻 *BearAnalyst* is rebutting...",
            "arbitration":        "⚖️ *Leader* is arbitrating the debate...",
            "strategy_synthesis": "📝 *Strategy Room* is synthesizing the trading plan...",
            "leader_review":      "✅ *Leader* is reviewing the final result...",
            "memory_save":        "💾 Saving memory...",
        }

        state: TradingState = {
            "question":    inputs.get("question", ""),
            "history":     inputs.get("history", ""),
            "session_key": inputs.get("session_key", ""),
        }

        # Pin session_key into ContextVar so every tool call in this request
        # carries the same session tag → join trading_team.log ↔ tools_debug.log
        _active_session.set(inputs.get("session_key", "-"))

        try:
            async for stream_type, chunk in self._graph.astream(
                state, stream_mode=["updates", "debug"]
            ):
                # ── Debug events: node is STARTING → emit status immediately ──
                if stream_type == "debug":
                    if isinstance(chunk, dict) and chunk.get("type") == "task":
                        node_name = chunk.get("payload", {}).get("name", "")
                        status_msg = _NODE_STATUS.get(node_name)
                        if status_msg:
                            yield "status", status_msg
                    continue

                # ── Updates events: node has FINISHED → emit its content ──
                for node_name, updates in chunk.items():
                    if node_name == "__end__":
                        continue

                    # Determine text to emit
                    text = ""
                    if node_name == "leader_intake":
                        text = updates.get("leader_intake", "")
                        event_type = (
                            "needs_clarification"
                            if updates.get("needs_clarification")
                            else "leader_intake"
                        )
                    elif node_name == "lead_analysis":
                        # Emit the synthesized brief; macro/technical are in state for context
                        text = updates.get("lead_analysis", "")
                        event_type = node_name
                    elif node_name == "bull_argument":
                        text = updates.get("bull_last", "")
                        event_type = node_name
                    elif node_name == "bear_argument":
                        text = updates.get("bear_last", "")
                        event_type = node_name
                    elif node_name == "arbitration":
                        text = updates.get("arbitration_result", "")
                        event_type = node_name
                    elif node_name == "strategy_synthesis":
                        text = updates.get("synthesis_draft", "")
                        event_type = node_name
                    elif node_name == "leader_review":
                        if updates.get("review_approved"):
                            text = updates.get("final_answer", "")
                            event_type = "leader_review"
                        else:
                            text = updates.get("review_feedback", "")
                            event_type = "leader_review_revision"
                    elif node_name in ("memory_save", "analysis_verify"):
                        # Silent background nodes — no text to stream to the user
                        continue
                    else:
                        continue

                    if text:
                        yield event_type, text

        except asyncio.TimeoutError as exc:
            logger.error("[GRAPH_ERROR] type=TimeoutError question='%s'", inputs.get("question", "")[:80])
            yield "error", f"❌ Workflow error: timeout — {exc}"
        except Exception as exc:
            logger.exception("[GRAPH_ERROR] type=%s question='%s' error=%s", type(exc).__name__, inputs.get("question", "")[:80], exc)
            yield "error", f"❌ Workflow error: {exc}"
