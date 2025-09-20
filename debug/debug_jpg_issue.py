#!/usr/bin/env python3
"""
Debug JPG file creation issue
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_jpg_issue():
    """Debug the JPG file creation issue"""
    print("🔍 Debug JPG File Creation Issue")
    print("=" * 80)
    
    # Check the latest download directory
    latest_dir = "/home/parikshit/Pictures/iPhone_Media/Parikshits_iPhone_20250920_021502/Photos"
    
    if not os.path.exists(latest_dir):
        print(f"❌ Directory does not exist: {latest_dir}")
        return
    
    print(f"📁 Checking directory: {latest_dir}")
    print()
    
    # List all files with details
    files = os.listdir(latest_dir)
    print(f"📊 Found {len(files)} files:")
    print("-" * 60)
    
    jpg_files = []
    heic_files = []
    meta_files = []
    
    for file in files:
        file_path = os.path.join(latest_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            ext = os.path.splitext(file)[1].lower()
            
            if ext == '.jpg':
                jpg_files.append({'name': file, 'size': size})
                if size == 0:
                    print(f"❌ {file}: {size} bytes (ZERO SIZE)")
                else:
                    print(f"✅ {file}: {size:,} bytes")
            elif ext == '.heic':
                heic_files.append({'name': file, 'size': size})
                print(f"✅ {file}: {size:,} bytes (HEIC)")
            elif ext == '.meta':
                meta_files.append({'name': file, 'size': size})
                print(f"📄 {file}: {size} bytes (metadata)")
            else:
                print(f"📄 {file}: {size} bytes (other)")
    
    print()
    print("📊 Summary:")
    print("-" * 60)
    print(f"JPG files: {len(jpg_files)}")
    print(f"HEIC files: {len(heic_files)}")
    print(f"Metadata files: {len(meta_files)}")
    
    # Analyze JPG files
    zero_size_jpg = [f for f in jpg_files if f['size'] == 0]
    valid_jpg = [f for f in jpg_files if f['size'] > 0]
    
    print(f"\n🔍 JPG File Analysis:")
    print(f"  Zero size: {len(zero_size_jpg)}")
    print(f"  Valid size: {len(valid_jpg)}")
    
    if zero_size_jpg:
        print(f"\n❌ Zero-size JPG files:")
        for f in zero_size_jpg:
            print(f"  • {f['name']}: {f['size']} bytes")
    
    if valid_jpg:
        print(f"\n✅ Valid JPG files:")
        for f in valid_jpg:
            print(f"  • {f['name']}: {f['size']:,} bytes")
    
    # Check if there are any JPG files in the source
    print(f"\n🔍 Checking source files...")
    print("This will help us understand if JPG files exist on the device")
    
    # Look for any JPG files in the mounted device
    try:
        from modules.device_manager import DeviceManager
        device_manager = DeviceManager()
        
        # Get mounted devices
        devices = device_manager.detect_devices()
        if devices:
            device = devices[0]
            mount_path = device_manager.mount_device(device['udid'])
            if mount_path:
                print(f"📱 Device mounted at: {mount_path}")
                
                # Look for JPG files in the mounted device
                jpg_count = 0
                for root, dirs, files in os.walk(mount_path):
                    for file in files:
                        if file.lower().endswith('.jpg'):
                            jpg_count += 1
                            if jpg_count <= 5:  # Show first 5
                                file_path = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(file_path)
                                    print(f"  📄 {file}: {size:,} bytes")
                                except:
                                    print(f"  📄 {file}: (error reading size)")
                
                print(f"📊 Found {jpg_count} JPG files on device")
                
                # Unmount device
                device_manager.unmount_device(device['udid'])
            else:
                print("❌ Failed to mount device")
        else:
            print("❌ No devices found")
            
    except Exception as e:
        print(f"❌ Error checking device: {e}")

def main():
    """Main function"""
    debug_jpg_issue()

if __name__ == "__main__":
    main()
