# iPhone Media Transfer - Troubleshooting Guide

## Quick Start

### First Time Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install libimobiledevice-utils ifuse ffmpeg

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python main_pyqt6.py
```

## Common Issues and Solutions

### 1. "No devices found" Error

**Problem**: The application shows "No devices found" in the device dropdown.

**Solutions**:
1. **Connect your iPhone** via USB cable
2. **Unlock your iPhone** (enter passcode or use Face ID/Touch ID)
3. **Trust the computer** - when prompted on your iPhone, tap "Trust This Computer"
4. **Try refreshing** - click "Refresh Devices" button
5. **Check cable** - try a different USB cable

### 2. "Mount failed" Error

**Problem**: Device is detected but mounting fails.

**Solutions**:
1. **Unlock your iPhone** completely
2. **Trust the computer** again (disconnect and reconnect)
3. **Check if iPhone is in use** - close any other apps that might be accessing photos
4. **Restart the application**

### 3. Application Won't Start

**Problem**: Application crashes or won't start.

**Solutions**:
1. **Check Python version** (should be 3.7+):
   ```bash
   python3 --version
   ```

2. **Install missing dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check for errors**:
   ```bash
   python main_pyqt6.py
   ```

### 4. Permission Issues

**Problem**: Cannot access iPhone files.

**Solutions**:
1. **Add user to plugdev group**:
   ```bash
   sudo usermod -a -G plugdev $USER
   ```
2. **Log out and log back in** (or restart)
3. **Check udev rules**:
   ```bash
   sudo nano /etc/udev/rules.d/39-libimobiledevice.rules
   ```
   Add this line:
   ```
   SUBSYSTEM=="usb", ATTR{idVendor}=="05ac", MODE="0666", GROUP="plugdev"
   ```
4. **Reload udev rules**:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

### 5. Slow Performance

**Problem**: Application is slow or freezes.

**Solutions**:
1. **Use range selection** to limit files (e.g., 1-100 instead of all files)
2. **Use media type filtering** (Photos only or Videos only)
3. **Close other applications**
4. **Use batch downloading** for large collections

### 6. Files Not Downloading

**Problem**: Files appear to download but are corrupted or missing.

**Solutions**:
1. **Check disk space**:
   ```bash
   df -h
   ```
2. **Check download directory permissions**
3. **Try a different download location**

## Getting Help

### Check Application Logs
The application logs are displayed in the terminal when you run it. Look for any error messages.

### Run Diagnostic Tests
```bash
# Test device detection
python tests/test_device_detection.py

# Test modules
python tests/test_modules.py

# Check dependencies
python debug/check_dependencies.py
```

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
# Remove and reinstall system dependencies
sudo apt remove libimobiledevice-utils ifuse
sudo apt install libimobiledevice-utils ifuse

# Reinstall Python dependencies
pip install -r requirements.txt
```

## Still Having Issues?

1. **Check the terminal output** for error messages
2. **Run diagnostic tests** above
3. **Try running as different user** (if permission issues)
4. **Check if iPhone is supported** (iOS 7+ should work)

## Application Features

### Range Selection
- Use "Use Range" checkbox to limit files
- Set start and end numbers (e.g., 1-100)
- Only processes files within the specified range

### Media Type Filtering
- "All Media": Photos and videos
- "Photos Only": Only photos
- "Videos Only": Only videos

### Batch Downloading
- Download files in batches to the same folder
- Use "Download Batch" for large collections
- Files are organized in `DeviceName_YYYYMMDD_HHMMSS/Photos` and `Videos` folders

### Stop Functionality
- Click "Stop Scan" to cancel scanning
- Graceful stop without system warnings
- Can restart scanning immediately after stopping