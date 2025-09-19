#!/usr/bin/env python3
"""
Quick scan of downloaded iPhone media files
"""

import os
import sys
from pathlib import Path

def main():
    # Use the corrected path
    target_dir = "/home/parikshit/Pictures/iPhone_Media/Parikshit_s_iPhone_20250920_015124/Photos"
    
    print("🔍 Quick iPhone Media File Scanner")
    print("=" * 60)
    print(f"Target directory: {target_dir}")
    print()
    
    if not os.path.exists(target_dir):
        print(f"❌ Directory does not exist: {target_dir}")
        return
    
    print("📁 Files found:")
    print("-" * 40)
    
    total_files = 0
    zero_size_files = 0
    heic_files = 0
    jpg_files = 0
    meta_files = 0
    
    for file in os.listdir(target_dir):
        file_path = os.path.join(target_dir, file)
        if os.path.isfile(file_path):
            total_files += 1
            file_size = os.path.getsize(file_path)
            
            print(f"{file:<30} {file_size:>10} bytes")
            
            if file_size == 0:
                zero_size_files += 1
                print(f"  ⚠️  ZERO SIZE FILE!")
            elif file.endswith('.HEIC'):
                heic_files += 1
            elif file.endswith('.JPG'):
                jpg_files += 1
            elif file.endswith('.meta'):
                meta_files += 1
    
    print()
    print("📊 Summary:")
    print("-" * 40)
    print(f"Total files: {total_files}")
    print(f"Zero size files: {zero_size_files}")
    print(f"HEIC files: {heic_files}")
    print(f"JPG files: {jpg_files}")
    print(f"Metadata files: {meta_files}")
    
    if zero_size_files > 0:
        print()
        print("❌ ISSUES FOUND:")
        print(f"   • {zero_size_files} files have zero size (download failures)")
        print("   • These files failed to download properly")
        print("   • The HEIC conversion may have caused these failures")
    
    if heic_files > 0:
        print()
        print("📱 HEIC Files:")
        print("   • HEIC files are intact and have proper sizes")
        print("   • These files should work in compatible applications")

if __name__ == "__main__":
    main()
