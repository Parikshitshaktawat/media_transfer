#!/usr/bin/env python3
"""
Comprehensive analysis of downloaded iPhone media files and issues
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

def normalize_device_name(device_name):
    """Normalize device name by removing special characters"""
    # Replace apostrophes and other special characters with underscores
    normalized = re.sub(r"['\"`]", "_", device_name)
    # Replace spaces with underscores
    normalized = re.sub(r"\s+", "_", normalized)
    # Remove any other special characters except underscores and alphanumeric
    normalized = re.sub(r"[^\w_]", "", normalized)
    return normalized

def analyze_download_issues():
    """Analyze downloaded files and identify issues"""
    print("🔍 iPhone Media Download Analysis")
    print("=" * 80)
    
    # Base directory
    base_dir = "/home/parikshit/Pictures/iPhone_Media"
    
    if not os.path.exists(base_dir):
        print(f"❌ Base directory does not exist: {base_dir}")
        return
    
    print(f"📁 Scanning base directory: {base_dir}")
    print()
    
    # Find all iPhone directories
    iphone_dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and "iPhone" in item:
            iphone_dirs.append(item)
    
    print(f"📱 Found {len(iphone_dirs)} iPhone directories:")
    for dir_name in iphone_dirs:
        print(f"   • {dir_name}")
    print()
    
    # Analyze each directory
    total_issues = 0
    for dir_name in iphone_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        print(f"🔍 Analyzing: {dir_name}")
        print("-" * 60)
        
        # Check Photos directory
        photos_dir = os.path.join(dir_path, "Photos")
        if os.path.exists(photos_dir):
            photos_issues = analyze_media_directory(photos_dir, "Photos")
            total_issues += photos_issues
        else:
            print("   ❌ Photos directory not found")
        
        # Check Videos directory
        videos_dir = os.path.join(dir_path, "Videos")
        if os.path.exists(videos_dir):
            videos_issues = analyze_media_directory(videos_dir, "Videos")
            total_issues += videos_issues
        else:
            print("   ❌ Videos directory not found")
        
        print()
    
    # Summary
    print("📋 SUMMARY")
    print("=" * 80)
    print(f"Total issues found: {total_issues}")
    
    if total_issues > 0:
        print()
        print("🔧 RECOMMENDED FIXES:")
        print("1. Fix directory naming to avoid special characters")
        print("2. Remove HEIC conversion to prevent zero-size files")
        print("3. Implement proper error handling for failed downloads")
        print("4. Add file integrity verification")
    
    return total_issues

def analyze_media_directory(directory, media_type):
    """Analyze a specific media directory"""
    issues = 0
    
    if not os.path.exists(directory):
        print(f"   ❌ {media_type} directory does not exist")
        return 1
    
    files = os.listdir(directory)
    if not files:
        print(f"   📁 {media_type} directory is empty")
        return 0
    
    print(f"   📁 {media_type} directory: {len(files)} files")
    
    # Analyze files
    zero_size_files = 0
    heic_files = 0
    jpg_files = 0
    meta_files = 0
    corrupted_files = 0
    
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            
            if file_size == 0:
                zero_size_files += 1
                issues += 1
                print(f"      ❌ {file}: ZERO SIZE")
            elif file.endswith('.HEIC'):
                heic_files += 1
                print(f"      ✅ {file}: {file_size:,} bytes (HEIC)")
            elif file.endswith('.JPG'):
                jpg_files += 1
                if file_size > 0:
                    print(f"      ✅ {file}: {file_size:,} bytes (JPG)")
                else:
                    print(f"      ❌ {file}: ZERO SIZE")
            elif file.endswith('.meta'):
                meta_files += 1
                print(f"      📄 {file}: {file_size:,} bytes (metadata)")
            else:
                print(f"      📄 {file}: {file_size:,} bytes")
    
    # Summary for this directory
    print(f"   📊 {media_type} Summary:")
    print(f"      • Total files: {len(files)}")
    print(f"      • Zero size files: {zero_size_files}")
    print(f"      • HEIC files: {heic_files}")
    print(f"      • JPG files: {jpg_files}")
    print(f"      • Metadata files: {meta_files}")
    
    if zero_size_files > 0:
        print(f"      ⚠️  {zero_size_files} files failed to download properly")
    
    return issues

def suggest_fixes():
    """Suggest fixes for the identified issues"""
    print()
    print("🛠️  SUGGESTED FIXES")
    print("=" * 80)
    
    print("1. 📁 DIRECTORY NAMING ISSUES:")
    print("   • Problem: Special characters in device names cause path issues")
    print("   • Solution: Normalize device names before creating directories")
    print("   • Example: 'Parikshit's iPhone' → 'Parikshit_s_iPhone'")
    print()
    
    print("2. 📷 ZERO-SIZE FILE ISSUES:")
    print("   • Problem: JPG files are 0 bytes (download failures)")
    print("   • Root cause: HEIC conversion process failing")
    print("   • Solution: Remove HEIC conversion, save files in original format")
    print()
    
    print("3. 🔧 CODE FIXES NEEDED:")
    print("   • Remove HEIC conversion from file_transfer.py")
    print("   • Add device name normalization in file_transfer.py")
    print("   • Improve error handling for failed downloads")
    print("   • Add file integrity verification")
    print()
    
    print("4. 🎯 IMMEDIATE ACTIONS:")
    print("   • Test downloads without HEIC conversion")
    print("   • Implement device name normalization")
    print("   • Add better error reporting")

def main():
    """Main function"""
    issues = analyze_download_issues()
    suggest_fixes()
    
    print()
    print("✅ Analysis complete!")
    if issues == 0:
        print("🎉 No issues found - downloads are working correctly!")
    else:
        print(f"⚠️  Found {issues} issues that need attention")

if __name__ == "__main__":
    main()
