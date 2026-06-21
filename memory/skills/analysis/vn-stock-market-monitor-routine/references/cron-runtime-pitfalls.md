# Cron Runtime Pitfalls

When running market monitors via scheduled cron jobs, MCP tools may sometimes fail to inject or be missing from `Trading Team tools`. If this happens, do not fall back to web scraping.

## Workaround 2: Direct CLI Invocation (vnstock_wrapper)

When Python imports or async logic within `execute_code` are too cumbersome, use the terminal to call the compatibility CLI directly. This is often more reliable for simple data retrieval.

```bash
# Set path to the virtualenv python
VENV_PYTHON="/Users/trannghia/workspace/ag-agentchat/.venv/bin/python"
WRAPPER_PATH="/Users/trannghia/workspace/ag-agentchat/mcp/stock_mcp/vnstock_wrapper.py"

# Examples
$VENV_PYTHON $WRAPPER_PATH indicators HPG SSI TCB
$VENV_PYTHON $WRAPPER_PATH exchange-rate
$VENV_PYTHON $WRAPPER_PATH overview VNINDEX
```

This bypasses the MCP server layer entirely and hits the underlying logic providers (vnstock, finpath, etc.) directly. Use this if tools starting with `mcp_stock_mcp_` are missing from your toolset.

## Workaround 3: FastMCP In-Memory Execution (Advanced)

If standard tool calls like `mcp_stock_mcp_get_finpath_market_breadth` fail or are absent, bypass the MCP transport by directly invoking the local FastMCP server within `execute_code`:

```python
import sys
import asyncio
import json

# Adjust path to the stock_mcp repository
sys.path.append("/Users/trannghia/workspace/ag-agentchat/mcp/stock_mcp")
from stock_mcp_server import mcp

async def fetch_all():
    data = {}
    # Fetch all mandatory monitor data in one pass
    tools_to_run = [
        ("breadth", "get_finpath_market_breadth", {}),
        ("sector", "get_finpath_sector_overview", {}),
        ("price", "get_price_data", {"symbols": "VNINDEX,VN30,HNXINDEX,HNXUPCOMINDEX"}),
        ("vn30f", "get_index_futures_overview", {"days": 5}),
        ("fbuy", "get_finpath_market_top", {"criteria": "foreign_buy"}),
        ("fsell", "get_finpath_market_top", {"criteria": "foreign_sell"})
    ]
    
    for key, name, args in tools_to_run:
        try:
            res = await mcp._tool_manager.call_tool(name, args)
            data[key] = res[0].text if isinstance(res, list) else str(res)
        except Exception as e:
            data[f"{key}_error"] = str(e)
            
    print(json.dumps(data, ensure_ascii=False))

asyncio.run(fetch_all())
```

This guarantees access to the mandatory structured data path, ensuring the routine completes successfully even in degraded cron environments.