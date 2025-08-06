#!/usr/bin/env python3

"""
Direct test of the MCP Server CLI
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cli_help():
    """Test CLI help command"""
    print("Testing CLI help command...")
    
    try:
        from mcp_server.__main__ import cli
        
        # Simulate command line arguments
        sys.argv = ['mcp_server', '--help']
        
        # This should print help and exit
        cli()
        
    except SystemExit as e:
        if e.code == 0:
            print("✅ CLI help command works")
            return True
        else:
            print(f"❌ CLI help command failed with exit code: {e.code}")
            return False
    except Exception as e:
        print(f"❌ CLI help command failed with error: {e}")
        return False

def test_cli_version():
    """Test CLI version command"""
    print("Testing CLI version command...")
    
    try:
        from mcp_server.__main__ import cli
        
        # Simulate command line arguments
        sys.argv = ['mcp_server', '--version']
        
        # This should print version and exit
        cli()
        
    except SystemExit as e:
        if e.code == 0:
            print("✅ CLI version command works")
            return True
        else:
            print(f"❌ CLI version command failed with exit code: {e.code}")
            return False
    except Exception as e:
        print(f"❌ CLI version command failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 MCP Server CLI Direct Test\n")
    
    success = True
    success &= test_cli_help()
    success &= test_cli_version()
    
    if success:
        print("\n🎉 All CLI tests passed!")
        exit(0)
    else:
        print("\n❌ Some CLI tests failed!")
        exit(1)
