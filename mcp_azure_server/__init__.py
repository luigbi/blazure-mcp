"""Azure MCP Server - Connect to Azure API through MCP."""

import sys
import os
from . import server

__version__ = "0.1.0"

def main():
    """Main entry point for the package."""
    print("Starting Azure MCP server...", file=sys.stderr)
    
    # Check if environment variables are set before starting
    required_vars = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID", 
        "AZURE_CLIENT_SECRET",
        "AZURE_SUBSCRIPTION_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        print("Some Azure tools may not function properly.", file=sys.stderr)
    
    try:
        server.mcp.run(transport='stdio')
    except Exception as e:
        print(f"Error starting MCP server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
