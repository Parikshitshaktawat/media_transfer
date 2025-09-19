# iPhone Media Transfer - Troubleshooting Guide

## Common Issues and Solutions

### 1. HEIC Files Not Processing
**Problem**: Getting "cannot identify image file" errors for HEIC files
**Solution**: 
```bash
# Install HEIC support libraries
sudo apt install -y libheif-dev libheif1

# Install Python HEIC support
pip install pillow-heif
```

### 2. "Dependencies Missing" Error

**Problem**: You get a popup saying dependencies are missing.

**Solution**:
```bash
# Run the dependency checker
python check_dependencies.py

# If dependencies are missing, install them:
sudo apt update
sudo apt install libimobiledevice6 libimobiledevice-utils ifuse ffmpeg
sudo apt install python3-pil python3-psutil
```

### 2. "No devices found" Error

**Problem**: The application shows "No devices found" in the device dropdown.

**Solutions**:
1. **Connect your iPhone** via USB cable
2. **Unlock your iPhone** (enter passcode or use Face ID/Touch ID)
3. **Trust the computer** - when prompted on your iPhone, tap "Trust This Computer"
4. **Try refreshing** - click "Refresh Devices" button
5. **Check cable** - try a different USB cable
6. **Check USB port** - try a different USB port

### 3. "Mount failed" Error

**Problem**: Device is detected but mounting fails.

**Solutions**:
1. **Unlock your iPhone** completely
2. **Trust the computer** again (disconnect and reconnect)
3. **Check if iPhone is in use** - close any other apps that might be accessing photos
4. **Restart the application**
5. **Try a different USB cable**

### 4. "Permission denied" Error

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

### 5. Application Won't Start

**Problem**: Application crashes or won't start.

**Solutions**:
1. **Check Python version**:
   ```bash
   python3 --version
   ```
   Should be Python 3.7 or higher.

2. **Check dependencies**:
   ```bash
   python check_dependencies.py
   ```

3. **Check for errors**:
   ```bash
   python main.py
   ```
   Look for error messages in the terminal.

### 6. Slow Performance

**Problem**: Application is slow or freezes.

**Solutions**:
1. **Reduce batch size** in settings
2. **Disable thumbnails** temporarily
3. **Close other applications**
4. **Check available memory**:
   ```bash
   free -h
   ```

### 7. Files Not Downloading

**Problem**: Files appear to download but are corrupted or missing.

**Solutions**:
1. **Check disk space**:
   ```bash
   df -h
   ```
2. **Check download directory permissions**
3. **Try a different download location**
4. **Check for antivirus interference**

### 8. HEIC Files Not Supported

**Problem**: HEIC files show as unsupported.

**Solutions**:
1. **Install HEIC support**:
   ```bash
   sudo apt install libheif-dev
   pip install pillow-heif
   ```
2. **Convert HEIC to JPG** on your iPhone first

### 9. Video Thumbnails Not Working

**Problem**: Video files show placeholder instead of thumbnails.

**Solutions**:
1. **Install ffmpeg**:
   ```bash
   sudo apt install ffmpeg
   ```
2. **Check ffmpeg installation**:
   ```bash
   ffmpeg -version
   ```

### 10. Memory Issues

**Problem**: Application uses too much memory.

**Solutions**:
1. **Reduce batch size** in settings
2. **Disable thumbnails**
3. **Process fewer files at once**
4. **Close other applications**

## Getting Help

### Check Application Logs
```bash
# View application logs
tail -f ~/.iphone_transfer_logs/iphone_transfer.log
```

### Run Diagnostic Tests
```bash
# Test all modules
python test_modules.py

# Test folder structure
python test_folder_structure.py

# Check dependencies
python check_dependencies.py
```

### System Information
```bash
# Check system info
python -c "from modules.utils import get_system_info; import json; print(json.dumps(get_system_info(), indent=2))"
```

## Still Having Issues?

1. **Check the logs** in `~/.iphone_transfer_logs/`
2. **Run diagnostic tests** above
3. **Check system requirements** in README.md
4. **Try running as different user** (if permission issues)
5. **Check if iPhone is supported** (iOS 7+ should work)

## Quick Fixes

### Reset Application
```bash
# Remove configuration
rm ~/.iphone_transfer_config.json

# Remove logs
rm -rf ~/.iphone_transfer_logs/

# Restart application
python main.py
```

### Reinstall Dependencies
```bash
# Remove and reinstall system dependencies
sudo apt remove libimobiledevice6 libimobiledevice-utils ifuse
sudo apt install libimobiledevice6 libimobiledevice-utils ifuse

# Reinstall Python dependencies
sudo apt remove python3-pil python3-psutil
sudo apt install python3-pil python3-psutil
```
