#!/usr/bin/env python3
"""
Script to scan downloaded iPhone media files and identify issues
"""

import os
import sys
from pathlib import Path
from PIL import Image
import hashlib
import json
from datetime import datetime

def scan_directory(directory_path):
    """Scan directory for media files and identify issues"""
    print(f"🔍 Scanning directory: {directory_path}")
    print("=" * 80)
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory does not exist: {directory_path}")
        return None, None, None
    
    # Count files by type
    file_stats = {
        'total_files': 0,
        'photos': 0,
        'videos': 0,
        'heic_files': 0,
        'jpg_files': 0,
        'png_files': 0,
        'mp4_files': 0,
        'mov_files': 0,
        'corrupted_files': 0,
        'zero_size_files': 0,
        'large_files': 0,
        'small_files': 0
    }
    
    issues = []
    file_details = []
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.bmp'}
    video_extensions = {'.mp4', '.mov', '.m4v', '.3gp', '.avi', '.mkv'}
    
    print("📁 File Analysis:")
    print("-" * 40)
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_stats['total_files'] += 1
            
            # Get file info
            try:
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file)[1].lower()
                
                file_info = {
                    'name': file,
                    'path': file_path,
                    'size': file_size,
                    'extension': file_ext,
                    'issues': []
                }
                
                # Check for zero size files
                if file_size == 0:
                    file_stats['zero_size_files'] += 1
                    file_info['issues'].append("Zero size file")
                    issues.append(f"Zero size: {file}")
                
                # Check for very large files (>100MB)
                elif file_size > 100 * 1024 * 1024:
                    file_stats['large_files'] += 1
                    file_info['issues'].append(f"Very large file ({file_size / (1024*1024):.1f}MB)")
                
                # Check for very small files (<1KB)
                elif file_size < 1024:
                    file_stats['small_files'] += 1
                    file_info['issues'].append(f"Very small file ({file_size} bytes)")
                
                # Count by extension
                if file_ext in image_extensions:
                    file_stats['photos'] += 1
                    if file_ext == '.heic':
                        file_stats['heic_files'] += 1
                    elif file_ext in ['.jpg', '.jpeg']:
                        file_stats['jpg_files'] += 1
                    elif file_ext == '.png':
                        file_stats['png_files'] += 1
                    
                    # Try to open image files to check for corruption
                    try:
                        with Image.open(file_path) as img:
                            img.verify()  # This will raise an exception if corrupted
                            # Try to get basic info
                            width, height = img.size
                            mode = img.mode
                            file_info['image_info'] = {
                                'width': width,
                                'height': height,
                                'mode': mode
                            }
                    except Exception as e:
                        file_stats['corrupted_files'] += 1
                        file_info['issues'].append(f"Corrupted image: {str(e)}")
                        issues.append(f"Corrupted image: {file} - {str(e)}")
                
                elif file_ext in video_extensions:
                    file_stats['videos'] += 1
                    if file_ext == '.mp4':
                        file_stats['mp4_files'] += 1
                    elif file_ext == '.mov':
                        file_stats['mov_files'] += 1
                
                file_details.append(file_info)
                
            except Exception as e:
                issues.append(f"Error analyzing {file}: {str(e)}")
                print(f"❌ Error with {file}: {str(e)}")
    
    # Print statistics
    print(f"📊 File Statistics:")
    print(f"   Total files: {file_stats['total_files']}")
    print(f"   Photos: {file_stats['photos']}")
    print(f"   Videos: {file_stats['videos']}")
    print(f"   HEIC files: {file_stats['heic_files']}")
    print(f"   JPG files: {file_stats['jpg_files']}")
    print(f"   PNG files: {file_stats['png_files']}")
    print(f"   MP4 files: {file_stats['mp4_files']}")
    print(f"   MOV files: {file_stats['mov_files']}")
    print()
    
    # Print issues
    if issues:
        print(f"⚠️  Issues Found ({len(issues)}):")
        print("-" * 40)
        for issue in issues[:20]:  # Show first 20 issues
            print(f"   • {issue}")
        if len(issues) > 20:
            print(f"   ... and {len(issues) - 20} more issues")
        print()
    else:
        print("✅ No issues found!")
        print()
    
    # Show file size distribution
    if file_details:
        sizes = [f['size'] for f in file_details if f['size'] > 0]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            
            print(f"📏 File Size Analysis:")
            print(f"   Average size: {avg_size / (1024*1024):.2f} MB")
            print(f"   Smallest file: {min_size / 1024:.2f} KB")
            print(f"   Largest file: {max_size / (1024*1024):.2f} MB")
            print()
    
    # Check for specific issues
    print("🔍 Specific Issue Analysis:")
    print("-" * 40)
    
    # Check for HEIC files that might need conversion
    heic_files = [f for f in file_details if f['extension'] == '.heic']
    if heic_files:
        print(f"📱 HEIC Files ({len(heic_files)}):")
        for heic_file in heic_files[:5]:  # Show first 5
            print(f"   • {heic_file['name']} ({heic_file['size'] / 1024:.1f} KB)")
        if len(heic_files) > 5:
            print(f"   ... and {len(heic_files) - 5} more HEIC files")
        print("   💡 Note: HEIC files may not be viewable in all applications")
        print()
    
    # Check for very small files
    small_files = [f for f in file_details if f['size'] < 1024 and f['size'] > 0]
    if small_files:
        print(f"📏 Very Small Files ({len(small_files)}):")
        for small_file in small_files[:5]:
            print(f"   • {small_file['name']} ({small_file['size']} bytes)")
        if len(small_files) > 5:
            print(f"   ... and {len(small_files) - 5} more small files")
        print()
    
    # Check for zero size files
    zero_files = [f for f in file_details if f['size'] == 0]
    if zero_files:
        print(f"❌ Zero Size Files ({len(zero_files)}):")
        for zero_file in zero_files:
            print(f"   • {zero_file['name']}")
        print()
    
    # Check for corrupted files
    corrupted_files = [f for f in file_details if f['issues']]
    if corrupted_files:
        print(f"💥 Corrupted Files ({len(corrupted_files)}):")
        for corrupted_file in corrupted_files[:5]:
            print(f"   • {corrupted_file['name']}: {', '.join(corrupted_file['issues'])}")
        if len(corrupted_files) > 5:
            print(f"   ... and {len(corrupted_files) - 5} more corrupted files")
        print()
    
    # Summary
    print("📋 Summary:")
    print("-" * 40)
    if file_stats['zero_size_files'] > 0:
        print(f"❌ {file_stats['zero_size_files']} zero-size files (download failures)")
    if file_stats['corrupted_files'] > 0:
        print(f"💥 {file_stats['corrupted_files']} corrupted files")
    if file_stats['heic_files'] > 0:
        print(f"📱 {file_stats['heic_files']} HEIC files (may need conversion for compatibility)")
    if file_stats['large_files'] > 0:
        print(f"📏 {file_stats['large_files']} very large files (>100MB)")
    
    if file_stats['zero_size_files'] == 0 and file_stats['corrupted_files'] == 0:
        print("✅ All files appear to be in good condition!")
    
    return file_stats, issues, file_details

def main():
    """Main function"""
    # Target directory - use the path we found
    target_dir = "/home/parikshit/Pictures/iPhone_Media/Parikshit's_iPhone_20250920_015124/Photos"
    
    print("🔍 iPhone Media File Scanner")
    print("=" * 80)
    print(f"Target directory: {target_dir}")
    print()
    
    # Scan the directory
    stats, issues, details = scan_directory(target_dir)
    
    # Save detailed report
    report_file = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        'scan_time': datetime.now().isoformat(),
        'target_directory': target_dir,
        'statistics': stats,
        'issues': issues,
        'file_details': details
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
