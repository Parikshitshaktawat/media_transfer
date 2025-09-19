#!/usr/bin/env python3
"""
iPhone Media Transfer Launcher
Simple launcher script with dependency checking
"""

import sys
import os
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    # Check Python packages
    required_packages = ['PIL', 'psutil']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    # Check system commands
    system_commands = ['idevice_id', 'ifuse']
    for cmd in system_commands:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            missing.append(cmd)
    
    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies and try again.")
        print("See README.md for installation instructions.")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("iPhone Media Transfer")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Import and run main application
    try:
        from main import main as run_app
        print("Starting application...")
        run_app()
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Make sure all files are in the correct location.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
