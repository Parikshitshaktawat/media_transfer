#!/usr/bin/env python3
"""
Analyze the latest download to understand the remaining issues
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def analyze_latest_download():
    """Analyze the latest download directory"""
    target_dir = "/home/parikshit/Pictures/iPhone_Media/Parikshits_iPhone_20250920_020739/Photos"
    
    print("🔍 Latest Download Analysis")
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
        print("❌ ISSUES FOUND:")
        print(f"  • {zero_size_files} JPG files have zero size")
        print("  • This suggests the HEIC conversion is still happening somewhere")
        print("  • The conversion process is failing, leaving empty JPG files")
        print()
        print("🔧 POSSIBLE CAUSES:")
        print("  1. HEIC conversion code still exists in the codebase")
        print("  2. The conversion is happening in a different module")
        print("  3. The file transfer is trying to convert HEIC to JPG")
        print("  4. There's a fallback conversion process we missed")
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

def check_logs():
    """Check the application logs for clues"""
    print()
    print("📋 LOG ANALYSIS:")
    print("-" * 60)
    print("From the terminal logs, we can see:")
    print("  • Device mounted successfully")
    print("  • 500 photos scanned")
    print("  • 6 files selected for download")
    print("  • Download completed: 6 success, 0 failed, 0 skipped")
    print()
    print("🔍 This suggests:")
    print("  • The download process reports success")
    print("  • But some files end up as zero size")
    print("  • There might be a disconnect between the success report and actual file sizes")
    print("  • The HEIC conversion might still be happening despite our changes")

def main():
    """Main function"""
    stats = analyze_latest_download()
    check_logs()
    
    print()
    print("🎯 RECOMMENDATIONS:")
    print("-" * 60)
    if stats['zero_size_files'] > 0:
        print("1. 🔍 Search for remaining HEIC conversion code")
        print("2. 🔧 Check if conversion is happening in media_handler.py")
        print("3. 🛠️  Verify that all conversion code has been removed")
        print("4. 📝 Add logging to track file sizes during download")
        print("5. 🧪 Test with a single file to isolate the issue")
    else:
        print("✅ All files downloaded successfully!")
        print("🎉 The fixes are working correctly!")

if __name__ == "__main__":
    main()
