#!/usr/bin/env python3
"""
Test file for Azure Billing and Cost Management tools.

Tests the following tools:
- get_cost_analysis
- get_budgets
- get_u    print("This will test cost analysis, budgets, usage details, and pricing tools.\n")age_details
- get_price_sheet
- get_subscription_details
- get_azure_advisor_detailed
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
    get_cost_analysis,
    get_budgets,
    get_usage_details,
    get_price_sheet,
    get_subscription_details,
    get_azure_advisor_detailed
)

async def test_billing_tools(export_data=False):
    """Test all billing and cost management related tools."""
    
    print("💰 Testing Azure Billing and Cost Management Tools")
    print("=" * 60)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/billing")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_subscription_details", get_subscription_details, {}),
        ("get_cost_analysis (MonthToDate)", get_cost_analysis, {"timeframe": "MonthToDate"}),
        ("get_cost_analysis (with grouping)", get_cost_analysis, {"timeframe": "MonthToDate", "group_by": "ResourceGroup"}),
        ("get_budgets", get_budgets, {}),
        ("get_usage_details", get_usage_details, {}),
        ("get_price_sheet", get_price_sheet, {}),
        ("get_azure_advisor_detailed", get_azure_advisor_detailed, {}),
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
                        cost_count = len(parsed_result["data"]["rows"])
                        print(f"   � Found {cost_count} billing records")
                    elif "value" in parsed_result:
                        print(f"   💰 Found {len(parsed_result['value'])} billing items")
                        
                        # Show specific insights for different tools
                        if test_name == "get_budgets":
                            budgets = parsed_result["value"]
                            active_budgets = sum(1 for budget in budgets if budget.get("properties", {}).get("amount", 0) > 0)
                            if active_budgets > 0:
                                print(f"   📊 Found {active_budgets} active budgets")
                        
                        elif test_name == "get_azure_advisor_detailed":
                            recommendations = parsed_result["value"]
                            cost_recommendations = sum(1 for rec in recommendations if rec.get("properties", {}).get("category") == "Cost")
                            if cost_recommendations > 0:
                                print(f"   💡 Found {cost_recommendations} cost optimization recommendations")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Billing Tools Test Summary")
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
        print("🎉 All billing tools are working correctly!")
    else:
        print("⚠️  Some billing tools need attention.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Azure Billing and Cost Management Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Azure Billing Tools Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/billing/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test cost analysis, budgets, usage details, and pricing tools.\n")
    
    try:
        results = asyncio.run(test_billing_tools(export_data=args.export))
        
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
