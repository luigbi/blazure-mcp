import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to find mcp_azure_server
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_azure_server.server import (
    get_all_resources, 
    get_network_topology, 
    get_compute_resources, 
    get_storage_resources,
    get_resource_dependencies,
    get_resource_hierarchy,
    get_network_connections,
    export_resources_graphml,
    get_virtual_machines_detailed,
    get_app_services_detailed,
    get_databases_detailed,
    get_storage_accounts_detailed,
    get_network_security_groups_detailed,
    get_load_balancers_detailed,
    get_resource_group_details,
    get_comprehensive_architecture_data,
    get_resource_dependencies_advanced
)

# Create export directory
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(EXPORT_DIR, exist_ok=True)

async def test_resource_discovery():
    """Test Azure resource discovery functions."""
    print("Testing Azure Resource Discovery...")
    
    # Helper function to export results to text files
    def export_result(filename, result):
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(result))
        print(f"Exported to: {filepath}")
    
    try:
        print("\n" + "="*70)
        print("1. Getting all resources...")
        all_resources = await get_all_resources()
        print("✓ All resources retrieved")
        export_result("all_resources.json", all_resources)
        
        print("\n" + "="*70)
        print("2. Getting network topology...")
        network_topology = await get_network_topology()
        print("✓ Network topology retrieved")
        export_result("network_topology.json", network_topology)
        
        print("\n" + "="*70)
        print("3. Getting compute resources...")
        compute_resources = await get_compute_resources()
        print("✓ Compute resources retrieved")
        export_result("compute_resources.json", compute_resources)
        
        print("\n" + "="*70)
        print("4. Getting storage resources...")
        storage_resources = await get_storage_resources()
        print("✓ Storage resources retrieved")
        export_result("storage_resources.json", storage_resources)
        
        print("\n" + "="*70)
        print("5. Getting resource dependencies...")
        dependencies = await get_resource_dependencies()
        print("✓ Resource dependencies retrieved")
        export_result("resource_dependencies.json", dependencies)
        
        print("\n" + "="*70)
        print("6. Getting resource hierarchy...")
        hierarchy = await get_resource_hierarchy()
        print("✓ Resource hierarchy retrieved")
        export_result("resource_hierarchy.json", hierarchy)
        
        print("\n" + "="*70)
        print("7. Getting network connections...")
        connections = await get_network_connections()
        print("✓ Network connections retrieved")
        export_result("network_connections.json", connections)
        
        print("\n" + "="*70)
        print("8. Exporting GraphML format...")
        graphml_export = await export_resources_graphml(include_network=True, include_dependencies=True)
        print("✓ GraphML export completed")
        export_result("resources_graphml.json", graphml_export)
        
        print("\n" + "="*70)
        print("9. Getting detailed VM information...")
        vm_detailed = await get_virtual_machines_detailed()
        print("✓ Detailed VM information retrieved")
        export_result("vm_detailed.json", vm_detailed)
        
        print("\n" + "="*70)
        print("10. Getting detailed App Services information...")
        app_detailed = await get_app_services_detailed()
        print("✓ Detailed App Services information retrieved")
        export_result("app_services_detailed.json", app_detailed)
        
        print("\n" + "="*70)
        print("11. Getting detailed database information...")
        db_detailed = await get_databases_detailed()
        print("✓ Detailed database information retrieved")
        export_result("databases_detailed.json", db_detailed)
        
        print("\n" + "="*70)
        print("12. Getting detailed storage account information...")
        storage_detailed = await get_storage_accounts_detailed()
        print("✓ Detailed storage account information retrieved")
        export_result("storage_detailed.json", storage_detailed)
        
        print("\n" + "="*70)
        print("13. Getting detailed NSG information...")
        nsg_detailed = await get_network_security_groups_detailed()
        print("✓ Detailed NSG information retrieved")
        export_result("nsg_detailed.json", nsg_detailed)
        
        print("\n" + "="*70)
        print("14. Getting resource group details...")
        rg_details = await get_resource_group_details()
        print("✓ Resource group details retrieved")
        export_result("resource_group_details.json", rg_details)
        
        print("\n" + "="*70)
        print("15. Getting comprehensive architecture data...")
        comprehensive_data = await get_comprehensive_architecture_data()
        print("✓ Comprehensive architecture data retrieved")
        export_result("comprehensive_architecture.json", comprehensive_data)
        
        print("\n" + "="*70)
        print("✅ All resource discovery tests completed successfully!")
        print(f"Results exported to: {EXPORT_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during resource discovery testing: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_resource_discovery())
