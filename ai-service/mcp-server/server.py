#!/usr/bin/env python3
"""MCP Server startup script."""

import asyncio
import os
import signal
import structlog
from mcp_protocol import MCPServer

logger = structlog.get_logger()


async def main():
    """Start MCP server."""
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8765"))
    
    server = MCPServer(host=host, port=port)
    
    try:
        await server.start_server()
        logger.info(f"MCP server running on {host}:{port}")
        
        # Keep server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
    finally:
        await server.stop_server()


if __name__ == "__main__":
    asyncio.run(main())