# iPhone Media Transfer - User Guide

## Getting Started

### Prerequisites
- Linux system (Ubuntu/Debian recommended)
- Python 3.7 or higher
- iPhone with iOS 7 or higher
- USB cable for iPhone connection

### Installation
1. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install libimobiledevice-utils ifuse ffmpeg
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main_pyqt6.py
   ```

## First Time Setup

1. **Connect your iPhone** to your computer using a USB cable
2. **Unlock your iPhone** and tap "Trust This Computer" when prompted
3. **Launch the application** and wait for your device to appear in the dropdown
4. **Click "Mount Device"** to access your iPhone's media files

## Scanning Media

### Full Scan (All Media)
1. Select "All Media" from the media type filter
2. Click "🔍 Scan Media" to scan all photos and videos
3. Wait for the scan to complete (progress bar will show status)

### Filtered Scan
1. Select "Photos Only" or "Videos Only" from the media type filter
2. Click "🔍 Scan Media" to scan only the selected type

### Range Selection
1. Check "Use Range" to limit the number of files scanned
2. Set "From" and "To" values (e.g., 1-100 to scan first 100 files)
3. Click "🔍 Scan Media" to scan only the specified range

## Downloading Media

### Select Files
- **Individual Selection:** Click on files in the list to select them
- **Select All:** Click "Select All" to select all visible files
- **Deselect All:** Click "Deselect All" to clear all selections

### Download Options
- **Download Selected:** Download only the selected files
- **Download Batch:** Download files in batches (useful for large collections)

### Batch Downloading
1. Use range selection to limit files (e.g., 1-500)
2. Download the batch
3. Change range to next batch (e.g., 501-1000)
4. Download to the same folder to continue the collection

## Features

### Progress Tracking
- Real-time progress bars for scanning and downloading
- Status messages showing current operation
- File count and completion percentage

### File Organization
- Files are saved in organized folders: `DeviceName_YYYYMMDD_HHMMSS/Photos` and `Videos`
- Metadata files (.meta) are created for each media file
- Original file formats are preserved (HEIC stays HEIC, JPG stays JPG)

### Stop Functionality
- Click "⏹️ Stop Scan" to cancel scanning at any time
- Graceful stop without system warnings
- Can restart scanning immediately after stopping

## Tips for Best Results

- **Use range selection** for large collections to avoid memory issues
- **Download in batches** for better organization and progress tracking
- **Keep your iPhone unlocked** during the transfer process
- **Use a stable USB connection** to avoid transfer interruptions
- **Check available disk space** before starting large downloads

## Troubleshooting

If you encounter issues:

1. **Check the "Troubleshooting" menu** in the application for common solutions
2. **Ensure your iPhone is trusted and unlocked**
3. **Try a different USB cable or port**
4. **Restart the application if needed**

### Common Issues

#### "No devices found" Error
- Connect your iPhone via USB cable
- Unlock your iPhone (enter passcode or use Face ID/Touch ID)
- Trust the computer - when prompted on your iPhone, tap "Trust This Computer"
- Try refreshing - click "Refresh Devices" button
- Check cable - try a different USB cable

#### "Mount failed" Error
- Unlock your iPhone completely
- Trust the computer again (disconnect and reconnect)
- Check if iPhone is in use - close any other apps that might be accessing photos
- Restart the application

#### Application Won't Start
- Check Python version (should be 3.7+): `python3 --version`
- Install missing dependencies: `pip install -r requirements.txt`
- Check for errors in the terminal output

#### Permission Issues
- Add user to plugdev group: `sudo usermod -a -G plugdev $USER`
- Log out and log back in (or restart)
- Check udev rules and reload them

#### Slow Performance
- Use range selection to limit files (e.g., 1-100 instead of all files)
- Use media type filtering (Photos only or Videos only)
- Close other applications
- Use batch downloading for large collections

#### Files Not Downloading
- Check disk space: `df -h`
- Check download directory permissions
- Try a different download location

## Quick Fixes

### Reset Application
```bash
# Remove configuration
rm ~/.iphone_transfer_config.json

# Remove logs
rm -rf ~/.iphone_transfer_logs/

# Restart application
python main_pyqt6.py
```

### Reinstall Dependencies
```bash
# Install system dependencies
sudo apt install libimobiledevice-utils ifuse ffmpeg

# Install Python dependencies
pip install -r requirements.txt
```

## Still Having Issues?

1. Check the terminal output for error messages
2. Run diagnostic tests in the tests/ folder
3. Try running as different user (if permission issues)
4. Check if iPhone is supported (iOS 7+ should work)

## Support

For additional support or to report issues, contact:
- **Developer:** Parikshit Shaktawat
- **Email:** parikshitshaktawat.it@gmail.com

---

**© 2025 Parikshit Shaktawat. All rights reserved.**
