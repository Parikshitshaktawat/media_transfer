#!/usr/bin/env python3
"""
Analyze the latest download after applying fixes
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def analyze_latest_download():
    """Analyze the latest download directory"""
    target_dir = "/home/parikshit/Pictures/iPhone_Media/Parikshits_iPhone_20250920_021502/Photos"
    
    print("🔍 Latest Download Analysis (After Fixes)")
    print("=" * 80)
    print(f"Target directory: {target_dir}")
    print()
    
    if not os.path.exists(target_dir):
        print(f"❌ Directory does not exist: {target_dir}")
        return
    
    print("📁 Files found:")
    print("-" * 60)
    
    total_files = 0
    zero_size_files = 0
    heic_files = 0
    jpg_files = 0
    meta_files = 0
    successful_files = 0
    
    file_details = []
    
    for file in os.listdir(target_dir):
        file_path = os.path.join(target_dir, file)
        if os.path.isfile(file_path):
            total_files += 1
            file_size = os.path.getsize(file_path)
            
            file_info = {
                'name': file,
                'size': file_size,
                'type': 'unknown'
            }
            
            if file.endswith('.HEIC'):
                heic_files += 1
                file_info['type'] = 'HEIC'
                if file_size > 0:
                    successful_files += 1
                    print(f"✅ {file:<30} {file_size:>10,} bytes (HEIC - SUCCESS)")
                else:
                    print(f"❌ {file:<30} {file_size:>10,} bytes (HEIC - FAILED)")
            elif file.endswith('.JPG'):
                jpg_files += 1
                file_info['type'] = 'JPG'
                if file_size > 0:
                    successful_files += 1
                    print(f"✅ {file:<30} {file_size:>10,} bytes (JPG - SUCCESS)")
                else:
                    zero_size_files += 1
                    print(f"❌ {file:<30} {file_size:>10,} bytes (JPG - ZERO SIZE)")
            elif file.endswith('.meta'):
                meta_files += 1
                file_info['type'] = 'metadata'
                print(f"📄 {file:<30} {file_size:>10,} bytes (metadata)")
            else:
                print(f"📄 {file:<30} {file_size:>10,} bytes (other)")
            
            file_details.append(file_info)
    
    print()
    print("📊 Summary:")
    print("-" * 60)
    print(f"Total files: {total_files}")
    print(f"Successful files: {successful_files}")
    print(f"Zero size files: {zero_size_files}")
    print(f"HEIC files: {heic_files}")
    print(f"JPG files: {jpg_files}")
    print(f"Metadata files: {meta_files}")
    
    print()
    print("🔍 Detailed Analysis:")
    print("-" * 60)
    
    # Analyze HEIC files
    heic_success = [f for f in file_details if f['type'] == 'HEIC' and f['size'] > 0]
    heic_failed = [f for f in file_details if f['type'] == 'HEIC' and f['size'] == 0]
    
    print(f"HEIC Files:")
    print(f"  ✅ Successful: {len(heic_success)}")
    for f in heic_success:
        print(f"    • {f['name']}: {f['size']:,} bytes")
    if heic_failed:
        print(f"  ❌ Failed: {len(heic_failed)}")
        for f in heic_failed:
            print(f"    • {f['name']}: {f['size']} bytes")
    
    # Analyze JPG files
    jpg_success = [f for f in file_details if f['type'] == 'JPG' and f['size'] > 0]
    jpg_failed = [f for f in file_details if f['type'] == 'JPG' and f['size'] == 0]
    
    print(f"\nJPG Files:")
    print(f"  ✅ Successful: {len(jpg_success)}")
    for f in jpg_success:
        print(f"    • {f['name']}: {f['size']:,} bytes")
    if jpg_failed:
        print(f"  ❌ Failed: {len(jpg_failed)}")
        for f in jpg_failed:
            print(f"    • {f['name']}: {f['size']} bytes")
    
    print()
    print("🔍 Root Cause Analysis:")
    print("-" * 60)
    
    if zero_size_files > 0:
        print("❌ ISSUES STILL PERSIST:")
        print(f"  • {zero_size_files} JPG files still have zero size")
        print("  • This means the HEIC conversion is still happening somewhere")
        print("  • The pillow_heif removal didn't fix the issue")
        print()
        print("🔧 POSSIBLE CAUSES:")
        print("  1. HEIC conversion code still exists in another module")
        print("  2. The conversion is happening in the file transfer process")
        print("  3. There's a different conversion mechanism we missed")
        print("  4. The issue is in the media scanning process")
        print("  5. PIL is still trying to convert HEIC files somewhere")
    else:
        print("✅ NO ISSUES FOUND!")
        print("  • All files downloaded successfully")
        print("  • No zero-size files")
        print("  • HEIC conversion has been properly removed")
    
    # Check if there are any HEIC files that should have been converted
    original_heic = [f for f in file_details if f['type'] == 'HEIC' and f['size'] > 0]
    if original_heic:
        print()
        print("📱 HEIC Files (Original Format):")
        print("  • These files are saved in their original HEIC format")
        print("  • This is correct behavior - no conversion should happen")
        print("  • HEIC files work in compatible applications")
    
    return {
        'total_files': total_files,
        'successful_files': successful_files,
        'zero_size_files': zero_size_files,
        'heic_files': heic_files,
        'jpg_files': jpg_files,
        'meta_files': meta_files
    }

def check_remaining_conversion_code():
    """Check for any remaining HEIC conversion code"""
    print()
    print("🔍 CHECKING FOR REMAINING CONVERSION CODE:")
    print("-" * 60)
    
    # Check for any remaining conversion code
    import subprocess
    result = subprocess.run(['grep', '-r', '-i', 'convert.*heic\\|heic.*convert\\|pillow.*heif', '/home/parikshit/projects/media_transfer/modules'], 
                          capture_output=True, text=True)
    
    if result.stdout:
        print("❌ Found remaining conversion code:")
        print(result.stdout)
    else:
        print("✅ No conversion code found in modules")
    
    # Check for any JPG file creation
    result2 = subprocess.run(['grep', '-r', '-i', '\\.jpg\\|\\.JPG', '/home/parikshit/projects/media_transfer/modules'], 
                           capture_output=True, text=True)
    
    if result2.stdout:
        print("\n📄 Found JPG references:")
        print(result2.stdout)
    else:
        print("\n✅ No JPG file creation found")

def suggest_next_steps():
    """Suggest next steps to fix the issue"""
    print()
    print("🎯 NEXT STEPS TO FIX THE ISSUE:")
    print("-" * 60)
    print("1. 🔍 Search for any remaining HEIC conversion code")
    print("2. 🔧 Check if conversion is happening in file_transfer.py")
    print("3. 🛠️  Look for PIL image processing that might create JPG files")
    print("4. 📝 Add logging to track where JPG files are being created")
    print("5. 🧪 Test with a single HEIC file to isolate the issue")
    print("6. 🔄 Check if the issue is in the media scanning process")

def main():
    """Main function"""
    stats = analyze_latest_download()
    check_remaining_conversion_code()
    suggest_next_steps()
    
    print()
    print("📋 SUMMARY:")
    print("-" * 60)
    if stats['zero_size_files'] > 0:
        print(f"❌ {stats['zero_size_files']} files still have zero size")
        print("🔧 The HEIC conversion issue persists despite our fixes")
        print("🎯 Need to investigate further to find the root cause")
    else:
        print("✅ All files downloaded successfully!")
        print("🎉 The fixes are working correctly!")

if __name__ == "__main__":
    main()
