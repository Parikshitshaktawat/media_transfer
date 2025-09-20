#!/usr/bin/env python3
"""
Advanced iPhone Detection Fix
Comprehensive solution for iPhone detection issues
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description, timeout=10):
    """Run a command and return the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
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

def check_usb_permissions():
    """Check USB device permissions"""
    print("🔍 Checking USB device permissions...")
    success, output = run_command("ls -la /dev/bus/usb/001/", "Check USB device permissions")
    if success:
        print("USB device info:")
        print(output)
        return True
    return False

def restart_usb_services():
    """Restart USB services"""
    print("🔄 Restarting USB services...")
    commands = [
        "sudo modprobe -r usb_storage",
        "sudo modprobe usb_storage",
        "sudo udevadm control --reload-rules",
        "sudo udevadm trigger"
    ]
    
    for cmd in commands:
        success, output = run_command(cmd, f"Running: {cmd}")
        if not success:
            print(f"Warning: {cmd} failed")

def try_alternative_detection():
    """Try alternative detection methods"""
    print("🔍 Trying alternative detection methods...")
    
    # Method 1: Try with different timeout
    success, output = run_command("timeout 30 idevice_id -l", "Try with longer timeout", 35)
    if success:
        return True
    
    # Method 2: Try ideviceinfo directly
    success, output = run_command("ideviceinfo", "Try ideviceinfo command")
    if success:
        return True
    
    # Method 3: Try with verbose output
    success, output = run_command("idevice_id -l -v", "Try with verbose output")
    if success:
        return True
    
    return False

def check_iphone_state():
    """Check iPhone state and provide instructions"""
    print("📱 iPhone State Check")
    print("=" * 30)
    
    print("Please check the following on your iPhone:")
    print("1. Is your iPhone UNLOCKED? (not just the lock screen)")
    print("2. Is your iPhone showing 'Trust This Computer' dialog?")
    print("3. Did you tap 'Trust' and enter your passcode?")
    print("4. Is your iPhone in the Photos app or any other app?")
    print("5. Try closing all apps and going to the home screen")
    
    print("\nIf you see 'Trust This Computer' dialog:")
    print("- Tap 'Trust'")
    print("- Enter your iPhone passcode")
    print("- Wait 10 seconds")
    
    print("\nIf you DON'T see the trust dialog:")
    print("- Go to Settings > General > Reset > Reset Location & Privacy")
    print("- Disconnect and reconnect the USB cable")
    print("- The trust dialog should appear")

def try_force_pairing():
    """Try to force pairing with the device"""
    print("🔗 Attempting to force pairing...")
    
    # Get the device ID from USB
    success, output = run_command("lsusb | grep Apple", "Get Apple device info")
    if success:
        print(f"Found Apple device: {output.strip()}")
        
        # Try to pair with the device
        success, output = run_command("idevicepair pair", "Try to pair device")
        if success:
            print("✅ Pairing successful!")
            return True
        else:
            print("❌ Pairing failed")
    
    return False

def main():
    """Main troubleshooting function"""
    print("🔍 Advanced iPhone Detection Troubleshooter")
    print("=" * 60)
    
    # Step 1: Check USB permissions
    check_usb_permissions()
    
    # Step 2: Check iPhone state
    check_iphone_state()
    
    print("\n" + "=" * 60)
    print("🔧 TRYING TECHNICAL FIXES...")
    print("=" * 60)
    
    # Step 3: Restart USB services
    restart_usb_services()
    
    # Step 4: Try alternative detection
    if try_alternative_detection():
        print("✅ iPhone detected with alternative method!")
        return True
    
    # Step 5: Try force pairing
    if try_force_pairing():
        print("✅ iPhone paired successfully!")
        return True
    
    # Step 6: Final recommendations
    print("\n" + "=" * 60)
    print("📋 FINAL RECOMMENDATIONS")
    print("=" * 60)
    
    print("If the iPhone is still not detected, try these steps:")
    print("\n1. COMPLETE iPhone Reset:")
    print("   - Go to iPhone Settings > General > Reset > Reset Location & Privacy")
    print("   - Disconnect USB cable")
    print("   - Wait 10 seconds")
    print("   - Reconnect USB cable")
    print("   - When prompted, tap 'Trust This Computer'")
    print("   - Enter your iPhone passcode")
    
    print("\n2. COMPUTER Restart:")
    print("   - Restart your computer")
    print("   - After restart, connect iPhone")
    print("   - Trust the computer when prompted")
    
    print("\n3. ALTERNATIVE Cable/Port:")
    print("   - Try a different USB cable")
    print("   - Try a different USB port")
    print("   - Try a USB 2.0 port instead of USB 3.0")
    
    print("\n4. iPhone Restart:")
    print("   - Restart your iPhone")
    print("   - After restart, connect to computer")
    print("   - Trust the computer when prompted")
    
    print("\n5. Check iPhone iOS Version:")
    print("   - Make sure your iPhone is running iOS 7 or later")
    print("   - Older iOS versions may not work")
    
    print("\n6. Try Different Computer:")
    print("   - Test on a different computer if possible")
    print("   - This will help determine if it's a computer or iPhone issue")
    
    return False

if __name__ == "__main__":
    main()
