#!/usr/bin/env python3
"""
Test file for Azure Detailed Resource Information tools.

Tests the following tools:
- get_network_security_groups_detailed
- get_load_balancers_detailed
- get_virtual_machines_detailed
- get_app_services_detailed
- get_databases_detailed
- get_storage_accounts_detailed
- get_key_vaults_detailed
- get_resource_group_details
"""

import asyncio
import json
import sys
import os
import argparse
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_azure_server.server import (
    get_network_security_groups_detailed,
    get_load_balancers_detailed,
    get_virtual_machines_detailed,
    get_app_services_detailed,
    get_databases_detailed,
    get_storage_accounts_detailed,
    get_key_vaults_detailed,
    get_resource_group_details
)

async def test_detailed_resource_tools(export_data=False):
    """Test all detailed resource information tools."""
    
    print("🔍 Testing Azure Detailed Resource Information Tools")
    print("=" * 65)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/detailed")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_resource_group_details", get_resource_group_details, {}),
        ("get_virtual_machines_detailed", get_virtual_machines_detailed, {}),
        ("get_app_services_detailed", get_app_services_detailed, {}),
        ("get_databases_detailed", get_databases_detailed, {}),
        ("get_storage_accounts_detailed", get_storage_accounts_detailed, {}),
        ("get_key_vaults_detailed", get_key_vaults_detailed, {}),
        ("get_network_security_groups_detailed", get_network_security_groups_detailed, {}),
        ("get_load_balancers_detailed", get_load_balancers_detailed, {}),
    ]
    
    results = {}
    exported_files = []
    
    for test_name, tool_func, params in tests:
        print(f"\n� Testing {test_name}...")
        
        try:
            if params:
                result = await tool_func(**params)
            else:
                result = await tool_func()
            
            # Parse JSON to validate format
            parsed_result = json.loads(result)
            
            # Check for errors
            if isinstance(parsed_result, dict) and parsed_result.get("error"):
                print(f"❌ {test_name} failed: {parsed_result.get('message', 'Unknown error')}")
                results[test_name] = "FAILED"
            else:
                print(f"✅ {test_name} succeeded")
                results[test_name] = "PASSED"
                
                # Export data if requested
                if export_data and export_dir:
                    filename = f"{test_name.replace(' ', '_').replace('(', '').replace(')', '').lower()}.json"
                    filepath = export_dir / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(parsed_result, f, indent=2, ensure_ascii=False)
                    exported_files.append(str(filepath))
                    print(f"   💾 Exported to: {filename}")
                
                # Show summary of data received
                if isinstance(parsed_result, dict):
                    if "data" in parsed_result and "rows" in parsed_result["data"]:
                        resource_count = len(parsed_result["data"]["rows"])
                        print(f"   � Found {resource_count} detailed resources")
                    elif "value" in parsed_result:
                        print(f"   � Found {len(parsed_result['value'])} detailed items")
                        
                        # Show specific details for resource groups
                        if test_name == "get_resource_group_details":
                            rg_names = [rg.get('name', 'Unknown') for rg in parsed_result['value'][:3]]
                            print(f"   � Resource Groups: {', '.join(rg_names)}...")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Detailed Resource Information Test Summary")
    print("=" * 50)
    
    passed = sum(1 for status in results.values() if status == "PASSED")
    total = len(results)
    
    for test_name, status in results.items():
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {test_name}: {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if export_data and exported_files:
        print(f"\n📦 Exported {len(exported_files)} files:")
        for filepath in exported_files:
            print(f"   📄 {filepath}")
    
    if passed == total:
        print("🎉 All detailed resource tools are working correctly!")
    else:
        print("⚠️  Some detailed resource tools need attention.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Azure Detailed Resource Information Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Azure Detailed Resource Information Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/detailed/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test detailed queries for VMs, databases, storage, networking, etc.\n")
    
    try:
        results = asyncio.run(test_detailed_resource_tools(export_data=args.export))
        
        # Exit with appropriate code
        passed = sum(1 for status in results.values() if status == "PASSED")
        total = len(results)
        
        if passed == total:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        sys.exit(3)
