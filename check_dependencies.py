#!/usr/bin/env python3
"""
Dependency Checker for iPhone Media Transfer
Checks if all required dependencies are installed
"""

import sys
import subprocess
import os

def check_system_dependencies():
    """Check system dependencies"""
    print("Checking system dependencies...")
    
    dependencies = {
        'idevice_id': False,
        'ifuse': False,
        'ffmpeg': False
    }
    
    for cmd in dependencies.keys():
        try:
            if cmd == 'idevice_id':
                # idevice_id returns 255 when no devices connected, which is OK
                result = subprocess.run([cmd, '-l'], capture_output=True, text=True, timeout=5)
                dependencies[cmd] = result.returncode in [0, 255]
            else:
                if cmd == 'ffmpeg':
                    result = subprocess.run([cmd, '-version'], capture_output=True, text=True, timeout=5)
                else:
                    result = subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5)
                dependencies[cmd] = result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            dependencies[cmd] = False
    
    return dependencies

def check_python_dependencies():
    """Check Python dependencies"""
    print("Checking Python dependencies...")
    
    dependencies = {
        'PIL': False,
        'psutil': False
    }
    
    for package in dependencies.keys():
        try:
            __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False
    
    return dependencies

def print_results(system_deps, python_deps):
    """Print dependency check results"""
    print("\n" + "="*50)
    print("DEPENDENCY CHECK RESULTS")
    print("="*50)
    
    print("\nSystem Dependencies:")
    for dep, status in system_deps.items():
        status_icon = "✓" if status else "✗"
        print(f"  {status_icon} {dep}")
    
    print("\nPython Dependencies:")
    for dep, status in python_deps.items():
        status_icon = "✓" if status else "✗"
        print(f"  {status_icon} {dep}")
    
    # Check if all dependencies are available
    all_system_ok = all(system_deps.values())
    all_python_ok = all(python_deps.values())
    
    print("\n" + "="*50)
    if all_system_ok and all_python_ok:
        print("✅ ALL DEPENDENCIES ARE INSTALLED!")
        print("You can now run the iPhone Media Transfer application.")
        return True
    else:
        print("❌ SOME DEPENDENCIES ARE MISSING!")
        print_installation_instructions(system_deps, python_deps)
        return False

def print_installation_instructions(system_deps, python_deps):
    """Print installation instructions for missing dependencies"""
    print("\nINSTALLATION INSTRUCTIONS:")
    print("-" * 30)
    
    # Check system
    import platform
    if platform.system() == "Linux":
        print("\nFor Ubuntu/Debian:")
        print("sudo apt update")
        
        missing_system = [dep for dep, status in system_deps.items() if not status]
        if missing_system:
            if 'idevice_id' in missing_system or 'ifuse' in missing_system:
                print("sudo apt install libimobiledevice6 libimobiledevice-utils ifuse")
            if 'ffmpeg' in missing_system:
                print("sudo apt install ffmpeg")
        
        missing_python = [dep for dep, status in python_deps.items() if not status]
        if missing_python:
            print("sudo apt install python3-pil python3-psutil")
    
    elif platform.system() == "Darwin":  # macOS
        print("\nFor macOS:")
        print("brew install libimobiledevice ifuse ffmpeg")
        print("pip install pillow psutil")
    
    else:
        print("\nPlease install the required dependencies manually:")
        print("- libimobiledevice and ifuse for device access")
        print("- Python packages: pillow, psutil")
        print("- Optional: ffmpeg for video thumbnails")

def main():
    """Main function"""
    print("iPhone Media Transfer - Dependency Checker")
    print("="*50)
    
    # Check dependencies
    system_deps = check_system_dependencies()
    python_deps = check_python_dependencies()
    
    # Print results
    success = print_results(system_deps, python_deps)
    
    if success:
        print("\nTo run the application:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
    else:
        print("\nPlease install the missing dependencies and run this check again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
