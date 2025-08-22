#!/usr/bin/env python3
"""
Debug script for get_security_center_alerts function.
"""

import asyncio
import json
import sys
import os

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_azure_server.server import get_security_center_alerts

async def debug_security_alerts():
    """Debug the get_security_center_alerts function."""
    
    print("🔍 Testing get_security_center_alerts function...")
    print("=" * 60)
    
    try:
        result = await get_security_center_alerts()
        
        # Parse JSON to validate format
        parsed_result = json.loads(result)
        
        # Check for errors
        if isinstance(parsed_result, dict) and parsed_result.get("error"):
            print(f"❌ Function failed: {parsed_result.get('error')}")
            if "details" in parsed_result:
                print(f"   Details: {parsed_result['details']}")
            return False
        else:
            print(f"✅ Function succeeded")
            
            # Show summary of data received
            if isinstance(parsed_result, dict):
                if "total_alerts" in parsed_result:
                    total = parsed_result["total_alerts"]
                    print(f"   📊 Found {total} security alerts")
                    
                    if "alerts_by_severity" in parsed_result:
                        severity_counts = parsed_result["alerts_by_severity"]
                        if severity_counts:
                            print(f"   📈 Severity breakdown: {severity_counts}")
                        
                    if "critical_alerts" in parsed_result:
                        critical = len(parsed_result["critical_alerts"])
                        if critical > 0:
                            print(f"   ⚠️  Critical/High severity alerts: {critical}")
                        else:
                            print(f"   ✨ No critical alerts (good!)")
                else:
                    print(f"   📄 Raw result structure: {list(parsed_result.keys())}")
            
            return True
                
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {str(e)}")
        print(f"   Raw result: {result[:200]}...")
        return False
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting debug test for get_security_center_alerts...")
    print("This will help identify the specific issue.\n")
    
    try:
        success = asyncio.run(debug_security_alerts())
        
        if success:
            print("\n🎉 Security alerts function is working correctly!")
        else:
            print("\n⚠️  Security alerts function has issues that need attention.")
            
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug test failed: {str(e)}")
