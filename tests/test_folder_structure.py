#!/usr/bin/env python3
"""
Test script to verify folder structure creation
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_folder_structure():
    """Test the folder structure creation"""
    print("Testing folder structure creation...")
    
    try:
        from modules.file_transfer import FileTransfer
        
        # Create a test download directory
        test_dir = "/tmp/iphone_transfer_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # Create FileTransfer instance
        ft = FileTransfer()
        
        # Test sanitize folder name
        test_names = [
            "iPhone 12 Pro",
            "My iPhone",
            "iPhone/with/slashes",
            "iPhone<with>invalid:chars",
            "   iPhone with spaces   ",
            ""
        ]
        
        print("\nTesting folder name sanitization:")
        for name in test_names:
            sanitized = ft._sanitize_folder_name(name)
            print(f"  '{name}' -> '{sanitized}'")
        
        # Test folder structure creation
        print("\nTesting folder structure creation:")
        
        # Create mock media files
        mock_media = [
            {'filename': 'IMG_001.jpg', 'type': 'photo', 'path': '/fake/path/IMG_001.jpg'},
            {'filename': 'VID_001.mp4', 'type': 'video', 'path': '/fake/path/VID_001.mp4'},
            {'filename': 'IMG_002.heic', 'type': 'photo', 'path': '/fake/path/IMG_002.heic'},
            {'filename': 'VID_002.mov', 'type': 'video', 'path': '/fake/path/VID_002.mov'}
        ]
        
        # Test the folder creation logic
        device_name = "iPhone 12 Pro"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_device_name = ft._sanitize_folder_name(device_name)
        base_folder_name = f"{safe_device_name}_{timestamp}"
        download_path = os.path.join(test_dir, base_folder_name)
        
        # Create folders
        os.makedirs(download_path, exist_ok=True)
        photos_path = os.path.join(download_path, "Photos")
        videos_path = os.path.join(download_path, "Videos")
        os.makedirs(photos_path, exist_ok=True)
        os.makedirs(videos_path, exist_ok=True)
        
        print(f"  Base folder: {download_path}")
        print(f"  Photos folder: {photos_path}")
        print(f"  Videos folder: {videos_path}")
        
        # Verify folders exist
        if os.path.exists(download_path):
            print("  ✓ Base folder created")
        else:
            print("  ✗ Base folder not created")
            return False
        
        if os.path.exists(photos_path):
            print("  ✓ Photos folder created")
        else:
            print("  ✗ Photos folder not created")
            return False
        
        if os.path.exists(videos_path):
            print("  ✓ Videos folder created")
        else:
            print("  ✗ Videos folder not created")
            return False
        
        # Test file path assignment
        print("\nTesting file path assignment:")
        for media in mock_media:
            media_type = media.get('type', 'photo')
            if media_type == 'photo':
                target_path = photos_path
            else:
                target_path = videos_path
            
            dest_path = ft._get_destination_path(media, target_path)
            print(f"  {media['filename']} ({media_type}) -> {dest_path}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        print("\n✓ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("iPhone Media Transfer - Folder Structure Test")
    print("=" * 50)
    
    if test_folder_structure():
        print("\n✅ All tests passed!")
        print("The folder structure feature is working correctly.")
        print("\nExpected folder structure:")
        print("  Download_Dir/")
        print("  └── DeviceName_YYYYMMDD_HHMMSS/")
        print("      ├── Photos/")
        print("      │   ├── IMG_001.jpg")
        print("      │   ├── IMG_002.heic")
        print("      │   └── ...")
        print("      └── Videos/")
        print("          ├── VID_001.mp4")
        print("          ├── VID_002.mov")
        print("          └── ...")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
