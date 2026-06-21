"""
LangChain Trading Team — Entry Point
---------------------------------------
Run from workspace root:
    python -m langgraph.langchain_trading_team.main                  # default: all channels
    python -m langgraph.langchain_trading_team.main --channel api    # API only (for testing)
    python -m langgraph.langchain_trading_team.main --channel telegram
    python -m langgraph.langchain_trading_team.main --channel all    # Telegram + API

Configuration (env vars):
    TRADING_API_KEY               : LLM API key
    TRADING_MODEL                 : Model name (default: gpt-4.1)
    TRADING_BASE_URL              : LLM API base URL
    TRADING_TELEGRAM_TOKEN        : Telegram bot token
    TRADING_RESPONSE_LANGUAGE     : Agent response language (default: Vietnamese)
    TRADING_API_HOST              : API server host (default: 0.0.0.0)
    TRADING_API_PORT              : API server port (default: 8000)
    TRADING_API_SERVER_KEY        : Bearer token for API auth (empty = no auth)
    MCP_MEMORY_URL                : Memory MCP URL
    MCP_RIVAL_SEARCH_URL          : Search MCP URL
    MCP_STOCK_SCRIPT              : Path to stock_mcp_server.py
"""
import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn

# Ensure the package directory is in sys.path so absolute imports
# (like `from config import ...`) work when run as a module from outside.
_pkg_dir = Path(__file__).parent.resolve()
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

logger = logging.getLogger("trading_team.main")


async def _startup(channel: str) -> None:
    from config import settings, setup_logging
    from tool.mcp_tools import ToolRegistry
    from workflow.graph import TradingTeamGraph

    # Initialise logging first
    setup_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)

    logger.info("=== LangChain Trading Team starting (channel=%s) ===", channel)
    logger.info("Model   : %s", settings.MODEL_NAME)
    logger.info("Base URL: %s", settings.BASE_URL)
    logger.info("Language: %s", settings.RESPONSE_LANGUAGE)

    # 1. Load MCP tools
    registry = ToolRegistry(
        stock_script_path=settings.MCP_STOCK_SCRIPT,
        memory_url=settings.MCP_MEMORY_URL,
        rival_search_url=settings.MCP_RIVAL_SEARCH_URL,
    )
    await registry.load()

    # 2. Build LangGraph workflow
    logger.info("Building LangGraph workflow...")
    workflow = TradingTeamGraph(registry)

    # Signal handling
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _on_signal(signame: str) -> None:
        logger.info("Received %s — initiating graceful shutdown...", signame)
        stop_event.set()

    for sig, name in ((signal.SIGINT, "SIGINT"), (signal.SIGTERM, "SIGTERM")):
        loop.add_signal_handler(sig, _on_signal, name)

    tasks: list[asyncio.Task] = []

    # 3a. Telegram channel
    if channel in ("telegram", "all"):
        from channel.telegram_channel import TelegramChannel
        tg = TelegramChannel(workflow)
        tg_app = tg.build_app()
        tasks.append(asyncio.create_task(_run_telegram(tg_app, stop_event)))
        logger.info("Telegram channel scheduled.")

    # 3b. API channel
    if channel in ("api", "all"):
        from channel.api_channel import APIChannel
        api = APIChannel(workflow)
        tasks.append(asyncio.create_task(
            _run_api(api.app, settings.API_HOST, settings.API_PORT, stop_event)
        ))
        logger.info(
            "API channel scheduled on http://%s:%s", settings.API_HOST, settings.API_PORT
        )

    if not tasks:
        raise ValueError(f"Unknown channel: {channel!r}. Use 'telegram', 'api', or 'all'.")

    # 4. Self-improvement scheduler (background, non-blocking)
    from self_improvement.scheduler import start_scheduler_async
    await start_scheduler_async()

    # Wait until a signal fires, then cancel all tasks
    await stop_event.wait()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.remove_signal_handler(sig)

    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# Channel runners
# ---------------------------------------------------------------------------

async def _run_telegram(app, stop_event: asyncio.Event) -> None:
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot is ready.")
        await stop_event.wait()
        await app.updater.stop()
        await app.stop()


async def _run_api(fastapi_app, host: str, port: int, stop_event: asyncio.Event) -> None:
    config = uvicorn.Config(
        fastapi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)

    async def _shutdown_watcher():
        await stop_event.wait()
        server.should_exit = True

    watcher = asyncio.create_task(_shutdown_watcher())
    await server.serve()
    watcher.cancel()
    logger.info("API server stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from config import settings
    parser = argparse.ArgumentParser(description="LangChain Trading Team")
    parser.add_argument(
        "--channel",
        choices=["telegram", "api", "all"],
        default=settings.DEFAULT_CHANNEL,
        help=f"Which channel(s) to start (default: {settings.DEFAULT_CHANNEL})",
    )
    args = parser.parse_args()

    try:
        asyncio.run(_startup(args.channel))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

