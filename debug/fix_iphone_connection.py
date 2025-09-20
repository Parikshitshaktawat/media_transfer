#!/usr/bin/env python3
"""
iPhone Connection Fix Script
Helps troubleshoot and fix iPhone connection issues
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True, result.stdout
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 {description} - Error: {str(e)}")
        return False, str(e)

def check_iphone_connected():
    """Check if iPhone is connected via USB"""
    print("📱 Checking if iPhone is connected...")
    success, output = run_command("lsusb | grep -i apple", "Check for Apple device")
    if success and "Apple" in output:
        print(f"✅ iPhone detected: {output.strip()}")
        return True
    else:
        print("❌ No iPhone detected. Please connect your iPhone via USB.")
        return False

def check_idevice_tools():
    """Check if idevice tools are working"""
    print("🔧 Checking idevice tools...")
    success, output = run_command("idevice_id -l", "Test idevice_id command")
    if success:
        print("✅ idevice_id is working")
        return True
    else:
        print("❌ idevice_id failed - this is normal if no device is trusted")
        return False

def check_user_groups():
    """Check if user is in plugdev group"""
    print("👤 Checking user groups...")
    success, output = run_command("groups", "Check user groups")
    if success and "plugdev" in output:
        print("✅ User is in plugdev group")
        return True
    else:
        print("❌ User not in plugdev group")
        return False

def check_udev_rules():
    """Check if udev rules exist"""
    print("📋 Checking udev rules...")
    success, output = run_command("ls -la /etc/udev/rules.d/39-libimobiledevice.rules", "Check udev rules file")
    if success:
        print("✅ udev rules exist")
        return True
    else:
        print("❌ udev rules missing")
        return False

def main():
    """Main troubleshooting function"""
    print("🔍 iPhone Connection Troubleshooter")
    print("=" * 50)
    
    # Step 1: Check if iPhone is connected
    if not check_iphone_connected():
        print("\n📋 SOLUTION:")
        print("1. Connect your iPhone via USB cable")
        print("2. Make sure the cable is working (try charging)")
        print("3. Try a different USB port")
        print("4. Try a different USB cable")
        return False
    
    # Step 2: Check user groups
    if not check_user_groups():
        print("\n📋 SOLUTION:")
        print("Run these commands:")
        print("sudo usermod -a -G plugdev $USER")
        print("newgrp plugdev")
        print("Then restart the application")
        return False
    
    # Step 3: Check udev rules
    if not check_udev_rules():
        print("\n📋 SOLUTION:")
        print("Run this command to create udev rules:")
        print("sudo tee /etc/udev/rules.d/39-libimobiledevice.rules > /dev/null << 'EOF'")
        print('SUBSYSTEM=="usb", ATTR{idVendor}=="05ac", MODE="0666", GROUP="plugdev"')
        print("EOF")
        print("sudo udevadm control --reload-rules")
        print("sudo udevadm trigger")
        return False
    
    # Step 4: Test idevice tools
    idevice_working = check_idevice_tools()
    
    print("\n" + "=" * 50)
    if idevice_working:
        print("✅ iPhone connection should be working!")
        print("\n📋 NEXT STEPS:")
        print("1. Make sure your iPhone is UNLOCKED")
        print("2. When prompted on iPhone, tap 'Trust This Computer'")
        print("3. Enter your iPhone passcode if asked")
        print("4. Run the application: python main.py")
        print("5. Click 'Refresh Devices' in the application")
    else:
        print("⚠️  iPhone connection needs attention")
        print("\n📋 TROUBLESHOOTING STEPS:")
        print("1. UNLOCK your iPhone completely")
        print("2. Disconnect and reconnect the USB cable")
        print("3. When iPhone asks, tap 'Trust This Computer'")
        print("4. Enter your iPhone passcode")
        print("5. Wait 10 seconds, then try again")
        print("6. If still not working, restart both iPhone and computer")
    
    return True

if __name__ == "__main__":
    main()
