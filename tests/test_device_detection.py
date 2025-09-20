#!/usr/bin/env python3
"""
Test iPhone Device Detection
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_device_detection():
    """Test the device detection functionality"""
    print("🔍 Testing iPhone Device Detection")
    print("=" * 40)
    
    try:
        from modules.device_manager import DeviceManager
        
        # Create device manager
        dm = DeviceManager()
        
        # Test dependency check
        print("1. Checking dependencies...")
        deps_ok = dm.check_dependencies()
        print(f"   Dependencies: {'✅ OK' if deps_ok else '❌ Missing'}")
        
        # Test device detection
        print("\n2. Detecting devices...")
        devices = dm.detect_devices()
        
        if devices:
            print(f"   Found {len(devices)} device(s):")
            for i, device in enumerate(devices, 1):
                print(f"   {i}. {device['name']}")
                if device.get('status') == 'needs_trust':
                    print(f"      Status: ⚠️  Needs Trust")
                else:
                    print(f"      UDID: {device['udid']}")
                    print(f"      Model: {device['model']}")
        else:
            print("   ❌ No devices found")
        
        # Test USB detection
        print("\n3. Checking USB connection...")
        import subprocess
        result = subprocess.run(["lsusb"], capture_output=True, text=True)
        if "Apple" in result.stdout:
            print("   ✅ Apple device detected via USB")
        else:
            print("   ❌ No Apple device found via USB")
        
        print("\n" + "=" * 40)
        if devices:
            if any(device.get('status') == 'needs_trust' for device in devices):
                print("⚠️  iPhone detected but needs to be trusted")
                print("\n📋 NEXT STEPS:")
                print("1. Make sure your iPhone is UNLOCKED")
                print("2. Disconnect and reconnect the USB cable")
                print("3. When prompted, tap 'Trust This Computer' on your iPhone")
                print("4. Enter your iPhone passcode")
                print("5. Run this test again")
            else:
                print("✅ iPhone detected and ready to use!")
        else:
            print("❌ No iPhone detected")
            print("\n📋 TROUBLESHOOTING:")
            print("1. Connect your iPhone via USB")
            print("2. Make sure your iPhone is unlocked")
            print("3. Try a different USB cable/port")
            print("4. Run: python fix_iphone_detection.py")
        
        return len(devices) > 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_device_detection()
    sys.exit(0 if success else 1)
