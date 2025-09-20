# iPhone Media Transfer

A modern, modular Python application for transferring media files from iPhone devices to Windows/Linux with full metadata preservation and integrity verification.

## Features

- **Full Metadata Preservation**: Preserves EXIF data, timestamps, and all image/video metadata
- **Integrity Verification**: SHA256 hash verification to ensure files are not corrupted
- **Organized Folder Structure**: Creates organized folders with device name, date, and separate folders for photos/videos
- **Modern PyQt6 Interface**: Professional GUI with dark theme and responsive design
- **Range Selection**: Batch processing with configurable file ranges (e.g., 1-500, 501-1000)
- **Media Type Filtering**: Separate handling of photos and videos
- **Progress Tracking**: Real-time progress bars and status updates
- **Graceful Stop**: Clean cancellation of long-running operations
- **Memory Optimization**: Efficient handling of large media collections
- **Integrated Help System**: Built-in user guide and troubleshooting
- **Developer Information**: Comprehensive about dialog with contact details
- **Error Handling**: Comprehensive error handling with retry mechanisms
- **Batch Processing**: Efficient batch processing with memory management

## Requirements

### System Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install libimobiledevice6 libimobiledevice-utils ifuse
sudo apt install ffmpeg  # Optional: for video thumbnails
```

#### macOS
```bash
brew install libimobiledevice
brew install ifuse
brew install ffmpeg  # Optional: for video thumbnails
```

#### Windows
- Install iTunes (provides libimobiledevice support)
- Install ifuse for Windows
- Install ffmpeg (optional)

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. Clone or download the project
2. Install system dependencies (see above)
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Connect iPhone**: Connect your iPhone via USB and unlock it
2. **Trust Computer**: When prompted, tap "Trust This Computer" on your iPhone
3. **Launch Application**: Run `python main_pyqt6.py`
4. **Select Device**: Choose your iPhone from the device dropdown
5. **Mount Device**: Click "Mount Device" to access iPhone files
6. **Scan Media**: Click "🔍 Scan Media" to find all photos and videos
7. **Select Files**: Choose which files to download (or download all)
8. **Download**: Click "Download Selected" or "Download Batch"

### Help System

The application includes a comprehensive help system accessible through the menu bar:

- **Help > User Guide**: Complete step-by-step instructions
- **Help > Troubleshooting**: Common issues and solutions
- **Help > About**: Developer information and application details

### Quick Start Guide

1. **Full Scan**: Select "All Media" and click "🔍 Scan Media"
2. **Range Selection**: Check "Use Range" and set limits (e.g., 1-100)
3. **Batch Download**: Use "Download Batch" for large collections
4. **Stop Function**: Click "⏹️ Stop Scan" to cancel operations

## Folder Structure

The application creates an organized folder structure for each transfer:

```
Download_Directory/
└── DeviceName_YYYYMMDD_HHMMSS/
    ├── Photos/
    │   ├── IMG_001.jpg
    │   ├── IMG_002.heic
    │   ├── IMG_001.jpg.meta  (metadata file)
    │   └── ...
    └── Videos/
        ├── VID_001.mp4
        ├── VID_002.mov
        ├── VID_001.mp4.meta  (metadata file)
        └── ...
```

- **DeviceName**: Sanitized device name (e.g., "iPhone_12_Pro")
- **YYYYMMDD_HHMMSS**: Date and time of transfer
- **Photos/**: All photo files (JPG, HEIC, PNG, etc.)
- **Videos/**: All video files (MP4, MOV, M4V, etc.)
- **Metadata files**: `.meta` files contain EXIF data and transfer information

## Architecture

The application is built with a modular architecture:

- **main.py**: Main GUI application
- **modules/device_manager.py**: iPhone device detection and mounting
- **modules/media_handler.py**: Media file scanning and metadata extraction
- **modules/file_transfer.py**: Secure file transfer with integrity verification
- **modules/config.py**: Configuration management
- **modules/utils.py**: Utility functions and helpers

## Key Improvements Over Original

### 1. **Metadata Preservation**
- Preserves all EXIF data from photos
- Maintains original timestamps and file attributes
- Preserves camera settings and GPS data
- Creates metadata files alongside media files

### 2. **Integrity Verification**
- SHA256 hash verification for all transfers
- Detects and handles corrupted files
- Retry mechanism for failed transfers
- Comprehensive error reporting

### 3. **Better Error Handling**
- No more bare `except:` clauses
- Specific exception handling for different error types
- Proper logging throughout the application
- Graceful degradation when dependencies are missing

### 4. **Memory Management**
- Efficient thumbnail generation
- Memory usage monitoring and cleanup
- Batch processing to prevent memory overload
- Garbage collection optimization

### 5. **Code Quality**
- Modular, maintainable code structure
- Type hints throughout
- Comprehensive documentation
- No duplicate code or commented-out sections

## Configuration

The application stores configuration in `~/.iphone_transfer_config.json`. Key settings include:

- **Download Directory**: Where to save transferred files
- **Thumbnail Settings**: Size and display options
- **Transfer Options**: Batch size, retry count, integrity verification
- **UI Settings**: Theme, font size, grid layout

## Troubleshooting

### Common Issues

1. **"No devices found"**
   - Ensure iPhone is connected and unlocked
   - Check that libimobiledevice is installed
   - Try disconnecting and reconnecting the USB cable

2. **"Mount failed"**
   - Make sure to tap "Trust This Computer" on your iPhone
   - Try unlocking your iPhone
   - Check if ifuse is properly installed

3. **"Dependencies missing"**
   - Install required system packages (see Requirements)
   - Install Python dependencies: `pip install -r requirements.txt`

4. **Corrupted files**
   - The application now includes integrity verification
   - Failed transfers are automatically retried
   - Check the transfer log for detailed error information

### Logs

Application logs are stored in `~/.iphone_transfer_logs/iphone_transfer.log`

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Adding New Features

The modular architecture makes it easy to add new features:

1. **New Media Types**: Add to `MediaHandler.PHOTO_EXTENSIONS` or `VIDEO_EXTENSIONS`
2. **New Metadata Fields**: Extend `_extract_photo_metadata()` or `_extract_video_metadata()`
3. **New Transfer Options**: Add to `Config` class and `FileTransfer` class
4. **New UI Features**: Extend the main application class

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the application logs
3. Create an issue with detailed information about your problem
