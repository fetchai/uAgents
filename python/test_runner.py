#!/usr/bin/env python3
"""
Test runner script for uAgents components.

This script runs all the test suites and provides a summary.
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all test suites."""
    python_path = ":".join([
        str(Path(__file__).parent / "src"),
        str(Path(__file__).parent / "uagents-core"),
        str(Path(__file__).parent / "uagents-adapter" / "src"),
        str(Path(__file__).parent / "uagents-ai-engine" / "src"),
    ])
    
    test_commands = [
        {
            "name": "Adapter Integration Tests",
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/test_adapter_integration.py", "-v"
            ],
            "cwd": Path(__file__).parent
        },
        {
            "name": "AI Engine Message Tests",
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/test_ai_engine_messages.py", "-v"
            ],
            "cwd": Path(__file__).parent / "uagents-ai-engine"
        },
        {
            "name": "Common Adapter Tests",
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/test_common_adapter.py", "-v"
            ],
            "cwd": Path(__file__).parent / "uagents-adapter"
        },
        {
            "name": "MCP Adapter Tests",
            "cmd": [
                sys.executable, "-m", "pytest", 
                "tests/test_mcp_adapter.py", "-v"
            ],
            "cwd": Path(__file__).parent / "uagents-adapter"
        }
    ]
    
    results = []
    
    for test_suite in test_commands:
        print(f"\n{'='*60}")
        print(f"Running: {test_suite['name']}")
        print(f"{'='*60}")
        
        env = {"PYTHONPATH": python_path}
        
        try:
            result = subprocess.run(
                test_suite["cmd"],
                cwd=test_suite["cwd"],
                env={**dict(subprocess.os.environ), **env},
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            results.append({
                "name": test_suite["name"],
                "passed": result.returncode == 0,
                "output": result.stdout
            })
            
        except Exception as e:
            print(f"Error running {test_suite['name']}: {e}")
            results.append({
                "name": test_suite["name"],
                "passed": False,
                "output": str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for result in results:
        status = "✓ PASSED" if result["passed"] else "✗ FAILED"
        print(f"{status}: {result['name']}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)