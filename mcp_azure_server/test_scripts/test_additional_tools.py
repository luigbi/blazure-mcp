#!/usr/bin/env python3
"""
Test file for Additional Azure MCP tools not covered by other test files.

Tests the following tools:
- get_recommendations
- export_resources_graphml
- get_resource_detailed_info
- get_network_watchers_topology
- get_monitoring_and_diagnostics
- get_resource_locks
- get_rbac_assignments
- get_resource_dependencies_advanced
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
    get_recommendations,
    export_resources_graphml,
    get_resource_detailed_info,
    get_network_watchers_topology,
    get_monitoring_and_diagnostics,
    get_resource_locks,
    get_rbac_assignments,
    get_resource_dependencies_advanced
)

async def test_additional_tools(export_data=False):
    """Test all additional Azure MCP tools not covered by other test files."""
    
    print("🔧 Testing Additional Azure MCP Tools")
    print("=" * 55)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/additional")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_recommendations", get_recommendations, {}),
        ("get_resource_detailed_info", get_resource_detailed_info, {}),
        ("get_network_watchers_topology", get_network_watchers_topology, {}),
        ("get_monitoring_and_diagnostics", get_monitoring_and_diagnostics, {}),
        ("get_resource_locks", get_resource_locks, {}),
        ("get_rbac_assignments", get_rbac_assignments, {}),
        ("get_resource_dependencies_advanced", get_resource_dependencies_advanced, {}),
        ("export_resources_graphml", export_resources_graphml, {}),
        ("export_resources_graphml (with network)", export_resources_graphml, {"include_network": True}),
        ("export_resources_graphml (with dependencies)", export_resources_graphml, {"include_dependencies": True}),
    ]
    
    results = {}
    exported_files = []
    
    for test_name, tool_func, params in tests:
        print(f"\n⚙️  Testing {test_name}...")
        
        try:
            if params:
                result = await tool_func(**params)
            else:
                result = await tool_func()
            
            # Parse JSON to validate format, but handle non-JSON responses
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                # If not valid JSON, wrap the string response
                parsed_result = {"message": result, "type": "string_response"}
            
            # Check for errors
            if isinstance(parsed_result, dict) and parsed_result.get("error"):
                print(f"❌ {test_name} failed: {parsed_result.get('message', 'Unknown error')}")
                results[test_name] = "FAILED"
            elif isinstance(parsed_result, dict) and parsed_result.get("type") == "string_response":
                # Handle string responses (like error messages or status updates)
                message = parsed_result.get("message", "")
                if "error" in message.lower() or "failed" in message.lower():
                    print(f"❌ {test_name} failed: {message}")
                    results[test_name] = "FAILED"
                else:
                    print(f"✅ {test_name} succeeded (string response)")
                    results[test_name] = "PASSED"
                    
                    # Export string response if requested
                    if export_data and export_dir:
                        filename = f"{test_name.replace(' ', '_').replace('(', '').replace(')', '').lower()}.json"
                        filepath = export_dir / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(parsed_result, f, indent=2, ensure_ascii=False)
                        exported_files.append(str(filepath))
                        print(f"   💾 Exported to: {filename}")
                    print(f"   📝 Response: {message[:100]}{'...' if len(message) > 100 else ''}")
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
                        item_count = len(parsed_result["data"]["rows"])
                        print(f"   📊 Found {item_count} items")
                    elif "value" in parsed_result:
                        print(f"   📊 Found {len(parsed_result['value'])} items")
                        
                        # Show specific insights for different tools
                        if test_name == "get_recommendations":
                            recommendations = parsed_result["value"]
                            categories = {}
                            for rec in recommendations:
                                category = rec.get("properties", {}).get("category", "Unknown")
                                categories[category] = categories.get(category, 0) + 1
                            if categories:
                                cat_str = ", ".join([f"{k}: {v}" for k, v in categories.items()])
                                print(f"   💡 Categories: {cat_str}")
                        
                        elif test_name == "get_rbac_assignments":
                            assignments = parsed_result["value"]
                            roles = {}
                            for assignment in assignments:
                                role_name = assignment.get("properties", {}).get("roleDefinitionId", "").split("/")[-1]
                                if role_name:
                                    roles[role_name] = roles.get(role_name, 0) + 1
                            if roles:
                                top_roles = sorted(roles.items(), key=lambda x: x[1], reverse=True)[:3]
                                roles_str = ", ".join([f"{r}: {c}" for r, c in top_roles])
                                print(f"   🔐 Top roles: {roles_str}")
                        
                        elif test_name == "get_resource_locks":
                            locks = parsed_result["value"]
                            lock_types = {}
                            for lock in locks:
                                lock_level = lock.get("properties", {}).get("level", "Unknown")
                                lock_types[lock_level] = lock_types.get(lock_level, 0) + 1
                            if lock_types:
                                types_str = ", ".join([f"{t}: {c}" for t, c in lock_types.items()])
                                print(f"   🔒 Lock types: {types_str}")
                    
                    elif "graphml" in parsed_result or "xml" in str(parsed_result).lower():
                        print(f"   📈 GraphML/XML export generated successfully")
                    
                    elif "nodes" in parsed_result and "edges" in parsed_result:
                        nodes = len(parsed_result.get("nodes", []))
                        edges = len(parsed_result.get("edges", []))
                        print(f"   📊 Network topology: {nodes} nodes, {edges} connections")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Additional Tools Test Summary")
    print("=" * 40)
    
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
        print("🎉 All additional Azure MCP tools are working correctly!")
        print("🔧 Extended functionality is operational.")
    else:
        print("⚠️  Some additional tools need attention.")
        print("🔧 This may limit advanced features and capabilities.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Additional Azure MCP Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Additional Azure MCP Tools Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/additional/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test advanced tools: recommendations, GraphML export, RBAC, locks, etc.\n")
    
    try:
        results = asyncio.run(test_additional_tools(export_data=args.export))
        
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
