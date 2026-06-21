"""
Telegram Channel — LangChain Trading Team
-------------------------------------------
Single bot. Users chat 1-on-1 with the bot via DM.
Bot runs the LangGraph workflow and streams per-node results back to the chat.

Run:
    cd /Users/trannghia/workspace/ag-agentchat
    python -m langgraph.langchain_trading_team.main
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from telegram import BotCommand, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import settings
from workflow.graph import TradingTeamGraph

logger = logging.getLogger("trading_team.telegram")


# =============================================================================
# Session store (in-memory)
# =============================================================================

class SessionStore:
    def __init__(self, timeout: int = settings.SESSION_TIMEOUT) -> None:
        self._sessions: dict[int, dict] = {}
        self._timeout = timeout

    def get(self, user_id: int) -> dict:
        now = time.time()
        s = self._sessions.get(user_id)
        if s is None or (now - s.get("last_active", 0)) > self._timeout:
            s = {"history": [], "last_active": now}
            self._sessions[user_id] = s
        return s

    def touch(self, user_id: int) -> None:
        self._sessions.setdefault(user_id, {"history": [], "last_active": 0})["last_active"] = time.time()

    def append(self, user_id: int, role: str, text: str) -> None:
        s = self.get(user_id)
        s["history"].append({"role": role, "text": text})
        s["history"] = s["history"][-10:]
        self.touch(user_id)

    def format_history(self, user_id: int) -> str:
        s = self.get(user_id)
        lines = [
            ("User" if t["role"] == "user" else "Leader") + ": " + t["text"][:300]
            for t in s["history"]
        ]
        return "\n".join(lines)

    def reset(self, user_id: int) -> None:
        self._sessions[user_id] = {"history": [], "last_active": time.time()}


# =============================================================================
# TelegramChannel
# =============================================================================

class TelegramChannel:
    """Single-bot Telegram channel backed by a LangGraph TradingTeamGraph."""

    _NODE_LABELS: dict[str, str] = {
        "leader_intake":            "📋 *Leader*",
        "needs_clarification":      "❓ *Leader needs clarification*",
        "lead_analysis":            "🔬 *Analysis Room* (Macro ∥ Technical)",
        "bull_argument":            "🐂 *BullAnalyst*",
        "bear_argument":            "🐻 *BearAnalyst*",
        "arbitration":              "⚖️ *Leader (Arbitrator)*",
        "strategy_synthesis":       "🧠 *Strategy Room*",
        "leader_review":            "✅ *Final Answer*",
        "leader_review_revision":   "🔄 *Leader (Revision Request)*",
        "synthesis":                "✅ *Final Summary*",  # backward compat
        "error":                    "❌ *Error*",
    }

    def __init__(self, workflow: TradingTeamGraph) -> None:
        self._workflow = workflow
        self._sessions = SessionStore()
        self._active_tasks: dict[int, asyncio.Task] = {}
        self._task_start_times: dict[int, float] = {}

    # -------------------------------------------------------------------------
    # Telegram Application setup
    # -------------------------------------------------------------------------

    async def _post_init(self, application: Application) -> None:
        """This method will run once immediately after the bot is successfully initialized."""
        commands = [
            BotCommand("reset", "Reset current session (cancel active task)"),
            BotCommand("status", "View current status"),
            BotCommand("sync_memory", "Sync portfolio & trading plan from MCP memory"),
            BotCommand("si_status", "Check SI task status"),
            BotCommand("si_approve", "Approve SI task"),
            BotCommand("si_reject", "Reject SI task"),
            BotCommand("si_run", "Run SI process"),
            BotCommand("si_compress_skills", "Compress SI skills")
        ]
        # Call Telegram API to update the command menu
        await application.bot.set_my_commands(commands)
        logger.info("Updated Telegram bot commands.")

    def build_app(self) -> Application:
        app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .concurrent_updates(True)
            .post_shutdown(self._post_shutdown)
            .post_init(self._post_init)
            .build()
        )
        app.add_handler(CommandHandler("reset", self._cmd_reset))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("sync_memory", self._cmd_sync_memory))
        app.add_handler(CommandHandler("si_status", self._cmd_si_status))
        app.add_handler(CommandHandler("si_approve", self._cmd_si_approve))
        app.add_handler(CommandHandler("si_reject", self._cmd_si_reject))
        app.add_handler(CommandHandler("si_run", self._cmd_si_run))
        app.add_handler(CommandHandler("si_compress_skills", self._cmd_si_compress_skills))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        return app

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------

    async def _post_shutdown(self, application: Application) -> None:
        for task in list(self._active_tasks.values()):
            if not task.done():
                task.cancel()
        self._active_tasks.clear()
        logger.info("Graceful shutdown complete.")

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    async def _cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if not self._is_allowed(user_id):
            return
        task = self._active_tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()
        self._sessions.reset(user_id)
        await self._send(context.bot, update, "✅ Session has been reset.")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if not self._is_allowed(user_id):
            return
        task = self._active_tasks.get(user_id)
        if task and not task.done():
            elapsed = int(time.time() - self._task_start_times.get(user_id, time.time()))
            m, s = divmod(elapsed, 60)
            await self._send(context.bot, update, f"⏳ Processing: {m}m{s}s. Use /reset to cancel.")
        else:
            await self._send(context.bot, update, "✅ No active task.")

    async def _cmd_sync_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/sync_memory — pull latest portfolio & trading plan from MCP memory and overwrite local files."""
        if not self._is_allowed(update.effective_user.id):
            return
        await self._send(context.bot, update, "🔄 Syncing portfolio & trading plan from MCP memory...")
        async def _run():
            import datetime
            from ..tool.mcp_tools import _call_http
            from ..tool.memory_layer import MEMORY_ROOT
            from ..config import settings

            errors: list[str] = []
            # Search within the last 30 days to get recent data only
            after_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

            # --- Portfolio ---
            try:
                portfolio_raw = await _call_http(
                    settings.MCP_MEMORY_URL,
                    "memory_search",
                    {"query": "current active portfolio", "limit": 5, "after": after_date},
                )
                if portfolio_raw and not portfolio_raw.startswith("[Tool Error]"):
                    portfolio_path = MEMORY_ROOT / "portfolio" / "AGENTS.md"
                    portfolio_path.write_text(
                        f"# Current Portfolio\n\n{portfolio_raw.strip()}\n",
                        encoding="utf-8",
                    )
                    logger.info("sync_memory: portfolio updated from MCP")
                else:
                    errors.append(f"Portfolio: {portfolio_raw}")
            except Exception as exc:
                errors.append(f"Portfolio error: {exc}")

            # --- Trading Plan ---
            try:
                plan_raw = await _call_http(
                    settings.MCP_MEMORY_URL,
                    "memory_search",
                    {"query": "active trading plan market outlook watchlist entry exit rules capital allocation", "limit": 10, "after": after_date},
                )
                if plan_raw and not plan_raw.startswith("[Tool Error]"):
                    plan_path = MEMORY_ROOT / "trading_plan" / "AGENTS.md"
                    plan_path.write_text(
                        f"# Trading Plan — Living Strategy Document\n\n{plan_raw.strip()}\n",
                        encoding="utf-8",
                    )
                    logger.info("sync_memory: trading plan updated from MCP")
                else:
                    errors.append(f"Trading plan: {plan_raw}")
            except Exception as exc:
                errors.append(f"Trading plan error: {exc}")

            if errors:
                await self._send(context.bot, update, "⚠️ Sync completed with errors:\n" + "\n".join(errors))
            else:
                await self._send(context.bot, update, "✅ Sync successful — portfolio and trading plan updated from MCP memory.")

        asyncio.create_task(_run())

    # -------------------------------------------------------------------------
    # Self-Improvement commands
    # -------------------------------------------------------------------------

    async def _cmd_si_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current pending self-improvement fix, if any."""
        if not self._is_allowed(update.effective_user.id):
            return
        from ..self_improvement.memory import get_pending
        pending = get_pending()
        if pending:
            msg = (
                f"🔧 *Pending SI fix*\n\n"
                f"Branch: `{pending['branch']}`\n"
                f"Summary: {pending['summary']}\n"
                f"Created: {pending.get('created_at', '?')}\n\n"
                f"`/si_approve <lesson>` — mark as merged, record lesson\n"
                f"`/si_reject <reason>` — discard branch"
            )
        else:
            msg = "✅ No pending SI fix. Use `/si_run` to trigger manually."
        await self._send(context.bot, update, msg)

    async def _cmd_si_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/si_approve [lesson] — mark pending fix as merged, record lesson."""
        if not self._is_allowed(update.effective_user.id):
            return
        from ..self_improvement.memory import get_pending, clear_pending
        pending = get_pending()
        if not pending:
            await self._send(context.bot, update, "ℹ️ No pending SI fix to approve.")
            return
        lesson = " ".join(context.args) if context.args else ""
        branch = pending["branch"]
        clear_pending(outcome="approved", lesson=lesson)
        await self._send(
            context.bot, update,
            f"✅ *SI fix approved*\n\nBranch `{branch}` marked as merged.\n"
            f"Merge manually:\n`git checkout master && git merge --no-ff {branch}`"
        )

    async def _cmd_si_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/si_reject [reason] — discard pending fix, record reason."""
        if not self._is_allowed(update.effective_user.id):
            return
        from ..self_improvement.memory import get_pending, clear_pending
        import subprocess
        from ..self_improvement import config as si_cfg
        pending = get_pending()
        if not pending:
            await self._send(context.bot, update, "ℹ️ No pending SI fix to reject.")
            return
        reason = " ".join(context.args) if context.args else "rejected by user"
        branch = pending["branch"]
        clear_pending(outcome=f"rejected: {reason}", lesson=reason)
        try:
            subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=str(si_cfg.REPO_DIR), capture_output=True,
            )
        except Exception:
            pass
        await self._send(
            context.bot, update,
            f"🗑️ *SI fix rejected*\n\nBranch `{branch}` discarded.\nReason: {reason}"
        )

    async def _cmd_si_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/si_run — trigger one self-improvement cycle immediately."""
        if not self._is_allowed(update.effective_user.id):
            return
        await self._send(context.bot, update, "🔍 Starting self-improvement run...")
        async def _run():
            try:
                from ..self_improvement.scheduler import run_once
                async def _notify(msg: str):
                    await self._send(context.bot, update, msg)
                await run_once(notify_fn=_notify)
            except Exception as exc:
                logger.error("si_run error: %s", exc)
                await self._send(context.bot, update, f"❌ SI run failed: {exc}")
        asyncio.create_task(_run())

    async def _cmd_si_compress_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/si_compress_skills — merge duplicates, drop obsolete skills."""
        if not self._is_allowed(update.effective_user.id):
            return
        await self._send(context.bot, update, "🗜 Analysing skills library — this may take a moment...")
        async def _run():
            try:
                from ..self_improvement.skill_consolidator import consolidate
                result = await consolidate()
                summary = result.summary()
                for chunk in _split(f"*Skill consolidation complete*\n\n{summary}", settings.TELEGRAM_MAX_LENGTH):
                    await self._send(context.bot, update, chunk)
            except Exception as exc:
                logger.error("si_compress_skills error: %s", exc)
                await self._send(context.bot, update, f"❌ Consolidation failed: {exc}")
        asyncio.create_task(_run())

    # -------------------------------------------------------------------------
    # Message handler
    # -------------------------------------------------------------------------

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        user_message = update.message.text or ""

        if not self._is_allowed(user_id):
            await self._send(context.bot, update, "⛔ You are not authorised to use this bot.")
            return

        if user_id in self._active_tasks and not self._active_tasks[user_id].done():
            elapsed = int(time.time() - self._task_start_times.get(user_id, time.time()))
            m, s = divmod(elapsed, 60)
            await self._send(
                context.bot, update,
                f"⏳ Already processing a request ({m}m{s}s).\nUse /reset to cancel and start over.",
            )
            return

        self._sessions.append(user_id, "user", user_message)

        thinking_msg = await self._send(context.bot, update, "🤔 Analysing...")

        async def run_task() -> None:
            inputs = {
                "question":    user_message,
                "history":     self._sessions.format_history(user_id),
                "session_key": str(user_id),
            }
            final_text = ""
            status_msg_id = thinking_msg.message_id if thinking_msg else None

            try:
                async for event_type, text in self._workflow.astream(inputs):
                    if not text:
                        continue

                    # ── Status event: node just STARTED → update thinking msg ──
                    if event_type == "status":
                        try:
                            if status_msg_id:
                                await context.bot.edit_message_text(
                                    chat_id=update.effective_chat.id,
                                    message_id=status_msg_id,
                                    text=text,
                                )
                        except Exception:
                            pass
                        continue

                    # Update the "thinking" message with current status
                    status_label = self._NODE_LABELS.get(event_type, "")
                    status_text = f"{status_label}\n\n{text}" if status_label else text

                    # Update thinking message to show current phase
                    if event_type in ("lead_analysis",
                                      "bull_argument", "bear_argument",
                                      "arbitration"):
                        # Update thinking message with current phase label
                        try:
                            phase_names = {
                                "lead_analysis":       "🔬 Analysis Room is analyzing (Macro ∥ Technical)...",
                                "bull_argument":       "🐂 BullAnalyst arguing...",
                                "bear_argument":       "🐻 BearAnalyst rebutting...",
                                "arbitration":         "⚖️ Leader evaluating debate...",
                            }
                            if status_msg_id:
                                await context.bot.edit_message_text(
                                    chat_id=update.effective_chat.id,
                                    message_id=status_msg_id,
                                    text=phase_names.get(event_type, "⏳ Processing..."),
                                )
                        except Exception:
                            pass

                        for chunk in _split(status_text, settings.TELEGRAM_MAX_LENGTH):
                            await self._send_raw(context.bot, update, chunk)
                            await asyncio.sleep(settings.MESSAGE_DELAY)

                    elif event_type in ("leader_intake", "needs_clarification"):
                        try:
                            if status_msg_id:
                                await context.bot.edit_message_text(
                                    chat_id=update.effective_chat.id,
                                    message_id=status_msg_id,
                                    text="📋 Leader processing...",
                                )
                        except Exception:
                            pass
                        for chunk in _split(status_text, settings.TELEGRAM_MAX_LENGTH):
                            await self._send_raw(context.bot, update, chunk)
                            await asyncio.sleep(settings.MESSAGE_DELAY)

                        if event_type == "needs_clarification":
                            self._sessions.append(user_id, "assistant", text[:500])
                            return  # Wait for user to reply

                        # For [FLOW:direct] responses, leader_intake IS the final
                        # answer — there are no later nodes. Capture it so the
                        # session history contains both the user question and
                        # the leader's reply; otherwise the next turn's leader
                        # has no context to reference. For full/analysis_only/
                        # strategy_only flows, leader_review will overwrite
                        # final_text later, so this stays correct.
                        final_text = text

                    elif event_type == "strategy_synthesis":
                        # Draft — update status message only; do not send yet (may be revised)
                        try:
                            if status_msg_id:
                                await context.bot.edit_message_text(
                                    chat_id=update.effective_chat.id,
                                    message_id=status_msg_id,
                                    text="🧠 Strategy Room is synthesizing...",
                                )
                        except Exception:
                            pass

                    elif event_type == "leader_review_revision":
                        # Leader requested a revision — update status, send feedback briefly
                        try:
                            if status_msg_id:
                                await context.bot.edit_message_text(
                                    chat_id=update.effective_chat.id,
                                    message_id=status_msg_id,
                                    text="🔄 Leader requested a draft revision...",
                                )
                        except Exception:
                            pass

                    elif event_type == "leader_review":
                        # Approved final answer
                        final_text = text
                        for chunk in _split(status_text, settings.TELEGRAM_MAX_LENGTH):
                            await self._send_raw(context.bot, update, chunk)
                            await asyncio.sleep(settings.MESSAGE_DELAY)

                    elif event_type == "synthesis":  # backward compat
                        final_text = text
                        for chunk in _split(status_text, settings.TELEGRAM_MAX_LENGTH):
                            await self._send_raw(context.bot, update, chunk)
                            await asyncio.sleep(settings.MESSAGE_DELAY)

                    elif event_type == "error":
                        await self._send_raw(context.bot, update, status_text)

            except asyncio.CancelledError:
                await self._send_raw(context.bot, update, "🛑 Task cancelled.")
            except Exception as exc:
                logger.exception("Task error for user %s: %s", user_id, exc)
                await self._send_raw(context.bot, update, f"❌ Error: {exc}")
            finally:
                # Delete thinking message
                try:
                    if status_msg_id:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id,
                            message_id=status_msg_id,
                        )
                except Exception:
                    pass
                self._active_tasks.pop(user_id, None)
                self._task_start_times.pop(user_id, None)
                if final_text:
                    self._sessions.append(user_id, "assistant", final_text[:500])

        task = asyncio.create_task(run_task())
        self._active_tasks[user_id] = task
        self._task_start_times[user_id] = time.time()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _is_allowed(self, user_id: int) -> bool:
        if not settings.ALLOWED_USER_IDS:
            return True
        return user_id in settings.ALLOWED_USER_IDS

    async def _send(self, bot, update: Update, text: str):
        try:
            return await bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode="Markdown",
            )
        except TelegramError:
            try:
                return await bot.send_message(chat_id=update.effective_chat.id, text=text)
            except TelegramError as exc:
                logger.error("Failed to send message: %s", exc)
                return None

    async def _send_raw(self, bot, update: Update, text: str):
        try:
            return await bot.send_message(chat_id=update.effective_chat.id, text=text)
        except TelegramError as exc:
            logger.error("Failed to send message: %s", exc)
            return None


# =============================================================================
# Utility
# =============================================================================

def _split(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        idx = text.rfind("\n", 0, max_len)
        if idx == -1:
            idx = max_len
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return chunks
