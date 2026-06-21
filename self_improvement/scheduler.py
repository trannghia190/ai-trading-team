"""
Self-Improvement Scheduler — entry point for periodic analysis.

Uses APScheduler (AsyncIOScheduler) to fire every SI_SCHEDULE_HOURS hours.

Before each run:
  1. Check for a pending fix (pending.json) — if present, SKIP.
  2. Collect evidence.
  3. Run analyzer graph.
  4. If a fix was committed → set pending state.

Also provides a one-shot `run_once()` for testing/manual trigger.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("trading_team.si.scheduler")


async def run_once(notify_fn=None) -> None:
    """Single self-improvement cycle.

    Args:
        notify_fn: optional async callable(str) — if provided, sends status
                   messages back to the caller (e.g. Telegram command).
                   When None (scheduled run), stays silent on noise.
    """
    async def _notify(msg: str) -> None:
        if notify_fn:
            try:
                await notify_fn(msg)
            except Exception:
                pass

    from . import config as cfg
    from .collector import collect, mark_sessions_reviewed
    from .memory import get_pending, set_pending, ensure_memory_dirs
    from .analyzer import run_analysis

    ensure_memory_dirs()

    # --- Guard: skip if a fix is already waiting for merge approval ---
    pending = get_pending()
    if pending:
        msg = (
            f"⏸ Đang có fix chờ merge — bỏ qua lần chạy này.\n"
            f"Branch: `{pending['branch']}`\n"
            f"Dùng /si_approve hoặc /si_reject trước."
        )
        logger.info("SI: pending fix found (branch=%s). Skipping.", pending["branch"])
        await _notify(msg)
        return

    # --- Collect evidence ---
    evidence = collect()
    if evidence.is_empty():
        logger.info("SI: no new evidence to analyse.")
        await _notify("ℹ️ Không có log lỗi hay session mới — không có gì để phân tích.")
        return

    logger.info("SI: starting analysis run. Evidence: %s", evidence.summary())
    await _notify(f"🔬 Phân tích: {evidence.summary()}...")

    # --- Analyse ---
    try:
        final = await asyncio.wait_for(
            run_analysis(evidence),
            timeout=cfg.SI_RUN_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("SI: analysis run timed out after %ds", cfg.SI_RUN_TIMEOUT)
        await _notify(
            f"❌ SI run timed out after {cfg.SI_RUN_TIMEOUT // 60} minutes — "
            "no changes committed."
        )
        return
    except Exception as exc:
        logger.error("SI: analysis run failed: %s", exc)
        await _notify(f"❌ SI run thất bại: {exc}")
        return

    # --- Post-run bookkeeping ---
    session_names = [name for name, _ in evidence.sessions]
    if session_names:
        mark_sessions_reviewed(session_names)

    if final.commit_result and final.commit_result.success:
        set_pending(
            branch=final.commit_result.branch,
            summary=final.problem_summary,
        )
        logger.info("SI: fix branch created: %s", final.commit_result.branch)
        # node_notify already sent the full Telegram message
    elif final.verdict in ("bug", "improvement", "mixed"):
        logger.warning("SI: actionable but no branch created. error=%s", final.error)
        await _notify(f"⚠️ Phân tích có vấn đề cần sửa nhưng không tạo được branch.\nLỗi: {final.error}")
    else:
        logger.info("SI: verdict=noise — nothing to do.")
        await _notify("✅ Phân tích xong — không phát hiện bug hay cải tiến cần thiết.")


def start_scheduler(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """
    Start APScheduler inside the running event loop.
    Call this AFTER the asyncio loop is running (i.e. from within an async context).
    """
    from . import config as cfg

    if not cfg.SCHEDULE_ENABLED:
        logger.info("SI scheduler disabled (SI_ENABLED=false).")
        return

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        logger.warning(
            "apscheduler not installed — self-improvement scheduler disabled. "
            "Install with: pip install apscheduler"
        )
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_once,
        "interval",
        hours=cfg.SCHEDULE_HOURS,
        id="self_improvement",
        replace_existing=True,
        max_instances=1,       # never overlap
    )
    scheduler.start()
    logger.info(
        "SI scheduler started. Interval: every %dh. Next run: %s",
        cfg.SCHEDULE_HOURS,
        scheduler.get_job("self_improvement").next_run_time,
    )


async def start_scheduler_async() -> None:
    """Async wrapper — call from an async startup function."""
    start_scheduler()
