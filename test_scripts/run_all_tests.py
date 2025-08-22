#!/usr/bin/env python3
"""
Master test runner for all Azure MCP tools.

This script runs all individual test suites and provides a comprehensive overview
of the Azure MCP server functionality.

Test Suites:
- Billing & Cost Management Tools
- Resource Discovery Tools  
- Performance Monitoring Tools
- Security Monitoring Tools
- Detailed Resource Information Tools
"""

import asyncio
import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_test_file(test_file, export_data=False):
    """Run a test file and return the result."""
    print(f"\n🚀 Running {test_file}...")
    print("=" * 60)
    
    try:
        # Build command with export flag if needed
        cmd = [sys.executable, test_file]
        if export_data:
            cmd.append("--export")
        
        # Set environment to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per test suite
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Return status
        if result.returncode == 0:
            return "PASSED"
        else:
            return f"FAILED (exit code: {result.returncode})"
            
    except subprocess.TimeoutExpired:
        print(f"❌ {test_file} timed out after 5 minutes")
        return "TIMEOUT"
    except Exception as e:
        print(f"❌ Error running {test_file}: {str(e)}")
        return "ERROR"

def main():
    """Run all test suites."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Master test runner for all Azure MCP tools")
    parser.add_argument("--export", action="store_true", 
                       help="Enable export mode for all test suites (saves data to export/ folders)")
    args = parser.parse_args()
    
    print("🧪 Azure MCP Server - Comprehensive Test Suite")
    print("=" * 55)
    if args.export:
        print("🎯 Export Mode: ON - All test results will be saved to export/ folders")
    else:
        print("🎯 Export Mode: OFF - Use --export to save test results to files")
    print("Testing all Azure billing, resource, performance, and security tools\n")
    
    # Define test files in order of execution
    test_files = [
        "test_billing_tools.py",
        "test_resource_discovery.py", 
        "test_detailed_resources.py",
        "test_performance_tools.py",
        "test_security_tools.py",
        "test_additional_tools.py"
    ]
    
    # Check if all test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {', '.join(missing_files)}")
        print("Please ensure all test files are present before running the master test.")
        return 1
    
    # Run each test suite
    results = {}
    
    for test_file in test_files:
        result = run_test_file(test_file, export_data=args.export)
        results[test_file] = result
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 MASTER TEST SUITE SUMMARY")
    print("=" * 70)
    
    passed_suites = 0
    total_suites = len(test_files)
    
    for test_file, status in results.items():
        status_icon = "✅" if status == "PASSED" else "❌"
        suite_name = test_file.replace("test_", "").replace("_", " ").replace(".py", "").title()
        print(f"{status_icon} {suite_name}: {status}")
        
        if status == "PASSED":
            passed_suites += 1
    
    print(f"\n📊 Overall Result: {passed_suites}/{total_suites} test suites passed")
    
    if args.export:
        print(f"\n📦 Export Summary:")
        export_folders = ["export/billing/", "export/resources/", "export/detailed/", 
                         "export/performance/", "export/security/"]
        existing_folders = [folder for folder in export_folders if Path(folder).exists()]
        if existing_folders:
            print(f"   📁 Data exported to: {', '.join(existing_folders)}")
            # Count total files
            total_files = 0
            for folder in existing_folders:
                total_files += len(list(Path(folder).glob("*.json")))
            print(f"   📄 Total files exported: {total_files}")
        else:
            print(f"   ⚠️  No export folders found - tests may have failed")
    
    if passed_suites == total_suites:
        print("\n🎉 SUCCESS: All Azure MCP tools are working correctly!")
        print("✨ Your Azure MCP server is ready for production use.")
        print("\nCapabilities verified:")
        print("  💰 Billing & Cost Management")
        print("  🏗️  Resource Discovery & Architecture")
        print("  📊 Performance Monitoring & Optimization")
        print("  🔒 Security Monitoring & Threat Detection")
        print("  🔍 Detailed Resource Information")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total_suites - passed_suites} test suite(s) failed")
        print("Some Azure MCP tools may not be working correctly.")
        print("Please check the individual test outputs above for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test suite interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Master test suite failed: {str(e)}")
        sys.exit(3)
