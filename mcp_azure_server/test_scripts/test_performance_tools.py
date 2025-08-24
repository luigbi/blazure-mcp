#!/usr/bin/env python3
"""
Test file for Azure Performance Monitoring and Optimization tools.

Tests the following tools:
- get_unused_resources
- get_vm_performance_metrics
- get_storage_performance_metrics
- get_database_performance_metrics
- get_activity_log_analysis
- get_resource_utilization_summary
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
    get_unused_resources,
    get_vm_performance_metrics,
    get_storage_performance_metrics,
    get_database_performance_metrics,
    get_activity_log_analysis,
    get_resource_utilization_summary
)

async def test_performance_tools(export_data=False):
    """Test all performance monitoring and optimization tools."""
    
    print("⚡ Testing Azure Performance Monitoring & Optimization Tools")
    print("=" * 70)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/performance")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_unused_resources", get_unused_resources, {}),
        ("get_resource_utilization_summary", get_resource_utilization_summary, {}),
        ("get_activity_log_analysis", get_activity_log_analysis, {}),
        ("get_vm_performance_metrics", get_vm_performance_metrics, {}),
        ("get_storage_performance_metrics", get_storage_performance_metrics, {}),
        ("get_database_performance_metrics", get_database_performance_metrics, {}),
    ]
    
    results = {}
    exported_files = []
    
    for test_name, tool_func, params in tests:
        print(f"\n📊 Testing {test_name}...")
        
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
                        metric_count = len(parsed_result["data"]["rows"])
                        print(f"   📈 Found {metric_count} performance metrics/items")
                    elif "value" in parsed_result:
                        print(f"   📈 Found {len(parsed_result['value'])} performance items")
                    
                    # Show specific insights for unused resources
                    if test_name == "get_unused_resources":
                        if "data" in parsed_result and "rows" in parsed_result["data"]:
                            unused_count = len(parsed_result["data"]["rows"])
                            if unused_count > 0:
                                print(f"   💡 Found {unused_count} potentially unused resources")
                            else:
                                print(f"   ✨ No unused resources detected (good optimization!)")
                    
                    # Show activity log insights
                    if test_name == "get_activity_log_analysis":
                        if "data" in parsed_result and "rows" in parsed_result["data"]:
                            activities = len(parsed_result["data"]["rows"])
                            print(f"   📅 Analyzed {activities} recent activities")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Performance Monitoring Test Summary")
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
        print("🎉 All performance monitoring tools are working correctly!")
        print("💡 Use these tools to optimize resource utilization and costs.")
    else:
        print("⚠️  Some performance monitoring tools need attention.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Azure Performance Monitoring and Optimization Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Azure Performance Monitoring Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/performance/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test performance metrics, unused resources, and optimization tools.\n")
    
    try:
        results = asyncio.run(test_performance_tools(export_data=args.export))
        
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
