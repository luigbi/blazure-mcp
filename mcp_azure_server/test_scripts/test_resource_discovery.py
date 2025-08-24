#!/usr/bin/env python3
"""
Test file for Azure Resource Discovery and Architecture tools.

Tests the following tools:
- get_all_resources
- get_network_topology
- g    print("This will test resource discovery, network topology, and architecture analysis tools.\n")t_compute_resources
- get_storage_resources
- get_resource_dependencies
- get_resource_hierarchy
- get_network_connections
- get_comprehensive_architecture_data
"""

import asyncio
import json
import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to Python path to find mcp_azure_server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_azure_server.server import (
    get_all_resources,
    get_network_topology,
    get_compute_resources,
    get_storage_resources,
    get_resource_dependencies,
    get_resource_hierarchy,
    get_network_connections,
    get_comprehensive_architecture_data
)

async def test_resource_discovery_tools(export_data=False):
    """Test all resource discovery and architecture analysis tools."""
    
    print("🏗️  Testing Azure Resource Discovery and Architecture Tools")
    print("=" * 70)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/resources")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_all_resources", get_all_resources, {}),
        ("get_compute_resources", get_compute_resources, {}),
        ("get_storage_resources", get_storage_resources, {}),
        ("get_network_topology", get_network_topology, {}),
        ("get_network_connections", get_network_connections, {}),
        ("get_resource_hierarchy", get_resource_hierarchy, {}),
        ("get_resource_dependencies", get_resource_dependencies, {}),
        ("get_comprehensive_architecture_data", get_comprehensive_architecture_data, {}),
    ]
    
    results = {}
    exported_files = []
    
    for test_name, tool_func, params in tests:
        print(f"\n🔍 Testing {test_name}...")
        
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
                        print(f"   🏗️  Found {resource_count} resources")
                        
                        # Show resource type breakdown for specific tools
                        if test_name == "get_all_resources":
                            rows = parsed_result["data"]["rows"]
                            resource_types = {}
                            for row in rows[:10]:  # Sample first 10
                                if len(row) > 1:
                                    res_type = row[1] if row[1] else "Unknown"
                                    resource_types[res_type] = resource_types.get(res_type, 0) + 1
                            if resource_types:
                                top_types = sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3]
                                types_str = ", ".join([f"{t}: {c}" for t, c in top_types])
                                print(f"   📊 Top types: {types_str}")
                    
                    elif "value" in parsed_result:
                        print(f"   🏗️  Found {len(parsed_result['value'])} architecture items")
                        
                        # Show specific insights for comprehensive architecture
                        if test_name == "get_comprehensive_architecture_data":
                            arch_data = parsed_result["value"]
                            if isinstance(arch_data, list) and arch_data:
                                print(f"   🎯 Comprehensive architecture analysis completed")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Resource Discovery Test Summary")
    print("=" * 45)
    
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
        print("🎉 All resource discovery tools are working correctly!")
        print("🏗️  Your Azure architecture analysis is operational.")
    else:
        print("⚠️  Some resource discovery tools need attention.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Azure Resource Discovery and Architecture Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Azure Resource Discovery Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/resources/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test resource discovery, network topology, and architecture analysis tools.\n")
    
    try:
        results = asyncio.run(test_resource_discovery_tools(export_data=args.export))
        
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
