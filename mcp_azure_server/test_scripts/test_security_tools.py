#!/usr/bin/env python3
"""
Test file for Azure Security Monitoring and Threat Detection tools.

Tests the following tools:
- get_security_center_alerts
- get_security_assessments
- get_defender_for_cloud_status
- get_key_vault_security_status
- get_network_security_analysis
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
    get_security_center_alerts,
    get_security_assessments,
    get_defender_for_cloud_status,
    get_key_vault_security_status,
    get_network_security_analysis
)

async def test_security_tools(export_data=False):
    """Test all security monitoring and threat detection tools."""
    
    print("🔒 Testing Azure Security Monitoring & Threat Detection Tools")
    print("=" * 70)
    
    # Create export directory if needed
    export_dir = None
    if export_data:
        export_dir = Path("export/security")
        export_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Export directory: {export_dir}")
    
    tests = [
        ("get_security_center_alerts", get_security_center_alerts, {}),
        ("get_security_assessments", get_security_assessments, {}),
        ("get_defender_for_cloud_status", get_defender_for_cloud_status, {}),
        ("get_key_vault_security_status", get_key_vault_security_status, {}),
        ("get_network_security_analysis", get_network_security_analysis, {}),
    ]
    
    results = {}
    exported_files = []
    
    for test_name, tool_func, params in tests:
        print(f"\n🛡️  Testing {test_name}...")
        
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
                
                # Show summary of security data received
                if isinstance(parsed_result, dict):
                    if "data" in parsed_result and "rows" in parsed_result["data"]:
                        security_items = len(parsed_result["data"]["rows"])
                        print(f"   🔍 Found {security_items} security items")
                    elif "value" in parsed_result:
                        print(f"   🔍 Found {len(parsed_result['value'])} security items")
                    
                    # Show specific security insights
                    if test_name == "get_security_center_alerts":
                        if "value" in parsed_result:
                            alerts = parsed_result["value"]
                            high_severity = sum(1 for alert in alerts if alert.get("properties", {}).get("severity") == "High")
                            if high_severity > 0:
                                print(f"   ⚠️  Found {high_severity} high-severity alerts!")
                            else:
                                print(f"   ✨ No high-severity alerts (good security posture)")
                    
                    elif test_name == "get_security_assessments":
                        if "value" in parsed_result:
                            assessments = parsed_result["value"]
                            unhealthy = sum(1 for assessment in assessments 
                                          if assessment.get("properties", {}).get("status", {}).get("code") == "Unhealthy")
                            if unhealthy > 0:
                                print(f"   ⚠️  Found {unhealthy} unhealthy security assessments")
                            else:
                                print(f"   ✨ All security assessments are healthy")
                    
                    elif test_name == "get_network_security_analysis":
                        if "data" in parsed_result and "rows" in parsed_result["data"]:
                            nsgs = len(parsed_result["data"]["rows"])
                            print(f"   🌐 Analyzed {nsgs} network security groups")
                
        except json.JSONDecodeError as e:
            print(f"❌ {test_name} failed: Invalid JSON response - {str(e)}")
            results[test_name] = "JSON_ERROR"
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
            results[test_name] = "EXCEPTION"
    
    # Summary
    print(f"\n📋 Security Monitoring Test Summary")
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
        print("🎉 All security monitoring tools are working correctly!")
        print("🔒 Your Azure environment security monitoring is operational.")
    else:
        print("⚠️  Some security monitoring tools need attention.")
        print("🚨 This could impact your ability to detect security threats.")
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Azure Security Monitoring and Threat Detection Tools")
    parser.add_argument("--export", action="store_true", help="Export test results to files")
    args = parser.parse_args()
    
    print("Starting Azure Security Monitoring Test Suite...")
    if args.export:
        print("Export mode: ON - Results will be saved to export/security/")
    else:
        print("Export mode: OFF - Use --export to save results to files")
    print("This will test security alerts, assessments, and threat detection tools.\n")
    
    try:
        results = asyncio.run(test_security_tools(export_data=args.export))
        
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
