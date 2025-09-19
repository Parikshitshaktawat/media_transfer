#!/usr/bin/env python3
"""
Test script to debug JPG file copying issues
Mounts device and copies JPG files directly to test directory
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from modules.device_manager import DeviceManager
from modules.media_handler import MediaHandler

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_jpg_copy():
    """Test copying JPG files directly from mounted device"""
    print("🔍 JPG File Copy Test")
    print("=" * 80)
    
    # Create test directory
    test_dir = "/home/parikshit/projects/media_transfer/test_jpg_files"
    os.makedirs(test_dir, exist_ok=True)
    print(f"📁 Test directory: {test_dir}")
    
    try:
        # Initialize device manager
        device_manager = DeviceManager()
        print("\n🔌 Detecting devices...")
        
        # Detect devices
        devices = device_manager.detect_devices()
        if not devices:
            print("❌ No devices found")
            return False
        
        print(f"✅ Found {len(devices)} device(s)")
        
        # Mount first device
        device = devices[0]
        print(f"\n📱 Mounting device: {device['name']}")
        
        mount_path = device_manager.mount_device(device['udid'])
        if not mount_path:
            print("❌ Failed to mount device")
            return False
        
        print(f"✅ Device mounted at: {mount_path}")
        
        # Initialize media handler
        media_handler = MediaHandler()
        
        # Find JPG files on the device
        print(f"\n🔍 Scanning for JPG files in: {mount_path}")
        
        # Look for JPG files in common iPhone photo directories
        jpg_files = []
        for root, dirs, files in os.walk(mount_path):
            for file in files:
                if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    jpg_files.append({
                        'path': file_path,
                        'name': file,
                        'size': file_size
                    })
                    print(f"  📄 Found JPG: {file} ({file_size:,} bytes)")
        
        if not jpg_files:
            print("❌ No JPG files found on device")
            return False
        
        print(f"\n📊 Found {len(jpg_files)} JPG files")
        
        # Test copying first 3 JPG files
        test_files = jpg_files[:3]
        print(f"\n🧪 Testing copy of {len(test_files)} JPG files:")
        print("-" * 60)
        
        for i, jpg_file in enumerate(test_files, 1):
            source_path = jpg_file['path']
            filename = jpg_file['name']
            source_size = jpg_file['size']
            dest_path = os.path.join(test_dir, filename)
            
            print(f"\n📋 Test {i}: {filename}")
            print(f"  Source: {source_path}")
            print(f"  Source size: {source_size:,} bytes")
            print(f"  Destination: {dest_path}")
            
            try:
                # Copy file using shutil.copy2
                print(f"  🔄 Copying file...")
                shutil.copy2(source_path, dest_path)
                
                # Verify copy
                if os.path.exists(dest_path):
                    dest_size = os.path.getsize(dest_path)
                    print(f"  ✅ File copied successfully")
                    print(f"  📊 Destination size: {dest_size:,} bytes")
                    
                    if source_size == dest_size:
                        print(f"  ✅ Size match: {source_size:,} = {dest_size:,}")
                    else:
                        print(f"  ❌ Size mismatch: {source_size:,} ≠ {dest_size:,}")
                    
                    # Check if file is readable
                    try:
                        with open(dest_path, 'rb') as f:
                            first_bytes = f.read(10)
                            print(f"  📄 First 10 bytes: {first_bytes.hex()}")
                            if first_bytes.startswith(b'\xff\xd8'):
                                print(f"  ✅ Valid JPG header detected")
                            else:
                                print(f"  ❌ Invalid JPG header")
                    except Exception as e:
                        print(f"  ❌ Error reading file: {e}")
                        
                else:
                    print(f"  ❌ Destination file not created")
                    
            except Exception as e:
                print(f"  ❌ Error copying file: {e}")
        
        # List all files in test directory
        print(f"\n📁 Files in test directory:")
        print("-" * 60)
        for file in os.listdir(test_dir):
            file_path = os.path.join(test_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  📄 {file}: {size:,} bytes")
        
        # Unmount device
        print(f"\n🔌 Unmounting device...")
        device_manager.unmount_device(device['udid'])
        print(f"✅ Device unmounted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_test_results():
    """Analyze the test results"""
    test_dir = "/home/parikshit/projects/media_transfer/test_jpg_files"
    
    print(f"\n📊 Test Results Analysis:")
    print("=" * 80)
    
    if not os.path.exists(test_dir):
        print("❌ Test directory not found")
        return
    
    files = os.listdir(test_dir)
    if not files:
        print("❌ No files in test directory")
        return
    
    print(f"📁 Found {len(files)} files in test directory:")
    print("-" * 60)
    
    total_size = 0
    zero_size_files = 0
    
    for file in files:
        file_path = os.path.join(test_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            total_size += size
            
            if size == 0:
                zero_size_files += 1
                print(f"  ❌ {file}: {size} bytes (ZERO SIZE)")
            else:
                print(f"  ✅ {file}: {size:,} bytes")
    
    print(f"\n📊 Summary:")
    print(f"  Total files: {len(files)}")
    print(f"  Zero size files: {zero_size_files}")
    print(f"  Total size: {total_size:,} bytes")
    
    if zero_size_files > 0:
        print(f"\n❌ ISSUES FOUND:")
        print(f"  • {zero_size_files} files have zero size")
        print(f"  • This indicates a problem with the copy process")
        print(f"  • Need to investigate further")
    else:
        print(f"\n✅ ALL FILES COPIED SUCCESSFULLY!")
        print(f"  • No zero-size files")
        print(f"  • All files have proper sizes")

def main():
    """Main function"""
    print("🧪 JPG File Copy Test Script")
    print("=" * 80)
    print("This script will:")
    print("1. Mount the iPhone device")
    print("2. Find JPG files on the device")
    print("3. Copy them directly to test directory")
    print("4. Analyze the results")
    print()
    
    # Run the test
    success = test_jpg_copy()
    
    if success:
        # Analyze results
        analyze_test_results()
        
        print(f"\n🎯 Next Steps:")
        print("1. Check the test directory for copied files")
        print("2. Verify file sizes and integrity")
        print("3. Compare with the main application results")
        print("4. Identify the root cause of zero-size files")
    else:
        print(f"\n❌ Test failed - check the logs above")

if __name__ == "__main__":
    main()
