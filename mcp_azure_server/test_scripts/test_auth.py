import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to find mcp_azure_server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_azure_server.server import get_azure_token

async def test_authentication():
    """Test Azure authentication."""
    print("Testing Azure authentication...")
    
    # Check if environment variables are set
    required_vars = [
        "AZURE_BILLING_TENANT_ID",
        "AZURE_BILLING_CLIENT_ID", 
        "AZURE_BILLING_CLIENT_SECRET",
        "AZURE_BILLING_SUBSCRIPTION_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    found_vars = [var for var in required_vars if os.environ.get(var)]
    if found_vars:
        print(f"Environment variables: {', '.join(found_vars)}")


    # Test getting token
    token = await get_azure_token()
    if token:
        print("✓ Successfully authenticated with Azure")
        print(f"Token length: {len(token)} characters")
        return True
    else:
        print("✗ Failed to authenticate with Azure")
        return False

if __name__ == "__main__":
    asyncio.run(test_authentication())