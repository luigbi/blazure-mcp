import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to find mcp_azure_server
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_azure_server.server import (
    get_virtual_machines_detailed,
    get_app_services_detailed,
    get_databases_detailed,
    get_storage_accounts_detailed,
    get_network_security_groups_detailed,
    get_resource_group_details,
    get_resource_dependencies_advanced
)

async def test_individual_functions():
    """Test each detailed function individually to identify the problematic one."""
    print("Testing individual detailed functions...")
    
    functions_to_test = [
        ("Virtual Machines Detailed", get_virtual_machines_detailed),
        ("App Services Detailed", get_app_services_detailed),
        ("Databases Detailed", get_databases_detailed),
        ("Storage Accounts Detailed", get_storage_accounts_detailed),
        ("Network Security Groups Detailed", get_network_security_groups_detailed),
        ("Resource Group Details", get_resource_group_details),
        ("Resource Dependencies Advanced", get_resource_dependencies_advanced),
    ]
    
    for name, func in functions_to_test:
        try:
            print(f"\n{'='*50}")
            print(f"Testing: {name}")
            result = await func()
            
            if result.startswith("Error"):
                print(f"❌ {name} FAILED: {result[:200]}...")
            else:
                print(f"✅ {name} SUCCESS: {len(result)} characters returned")
                
        except Exception as e:
            print(f"❌ {name} EXCEPTION: {str(e)}")
    
    print(f"\n{'='*50}")
    print("Individual function testing completed!")

if __name__ == "__main__":
    asyncio.run(test_individual_functions())
