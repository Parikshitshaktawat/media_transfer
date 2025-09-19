#!/usr/bin/env python3
"""
Test script to verify all modules work correctly
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from modules.config import Config
        print("✓ Config module imported successfully")
    except Exception as e:
        print(f"✗ Config module failed: {e}")
        return False
    
    try:
        from modules.utils import setup_logging, format_file_size
        print("✓ Utils module imported successfully")
    except Exception as e:
        print(f"✗ Utils module failed: {e}")
        return False
    
    try:
        from modules.device_manager import DeviceManager
        print("✓ DeviceManager module imported successfully")
    except Exception as e:
        print(f"✗ DeviceManager module failed: {e}")
        return False
    
    try:
        from modules.media_handler import MediaHandler
        print("✓ MediaHandler module imported successfully")
    except Exception as e:
        print(f"✗ MediaHandler module failed: {e}")
        return False
    
    try:
        from modules.file_transfer import FileTransfer
        print("✓ FileTransfer module imported successfully")
    except Exception as e:
        print(f"✗ FileTransfer module failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of modules"""
    print("\nTesting basic functionality...")
    
    try:
        from modules.config import Config
        config = Config()
        config.load()
        print("✓ Config loading works")
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False
    
    try:
        from modules.utils import format_file_size, get_safe_filename
        size_str = format_file_size(1024 * 1024)
        safe_name = get_safe_filename("test file.jpg")
        print("✓ Utils functions work")
    except Exception as e:
        print(f"✗ Utils functions failed: {e}")
        return False
    
    try:
        from modules.device_manager import DeviceManager
        dm = DeviceManager()
        deps_ok = dm.check_dependencies()
        print(f"✓ DeviceManager created (dependencies: {'OK' if deps_ok else 'Missing'})")
    except Exception as e:
        print(f"✗ DeviceManager failed: {e}")
        return False
    
    try:
        from modules.media_handler import MediaHandler
        mh = MediaHandler()
        print("✓ MediaHandler created")
    except Exception as e:
        print(f"✗ MediaHandler failed: {e}")
        return False
    
    try:
        from modules.file_transfer import FileTransfer
        ft = FileTransfer()
        print("✓ FileTransfer created")
    except Exception as e:
        print(f"✗ FileTransfer failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("iPhone Media Transfer - Module Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        sys.exit(1)
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Functionality tests failed")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("The modular application is ready to use.")
    print("\nTo run the application:")
    print("  python main.py")
    print("  or")
    print("  python run.py")

if __name__ == "__main__":
    main()
