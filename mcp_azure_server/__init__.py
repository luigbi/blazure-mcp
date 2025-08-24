"""Azure Billing MCP Server - Connect to Azure Billing API through MCP."""

import sys
from . import server

__version__ = "0.1.0"

def main():
    """Main entry point for the package."""
    print("Starting BLAzure MCP server...", file=sys.stderr)
    server.mcp.run()

if __name__ == "__main__":
    main()
