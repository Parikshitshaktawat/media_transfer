#!/usr/bin/env python3
"""
iPhone Media Transfer App - PyQt6 Version
Modern, professional GUI for transferring media from iPhone to computer
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QComboBox, QProgressBar, 
    QListWidget, QListWidgetItem, QCheckBox, QFrame, QSplitter,
    QGroupBox, QTextEdit, QFileDialog, QMessageBox, QButtonGroup,
    QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPalette, QColor

# Import our existing modules
from modules.device_manager import DeviceManager
from modules.media_handler import MediaHandler
from modules.file_transfer import FileTransfer
from modules.config import Config

class ScanMediaThread(QThread):
    """Thread for scanning media files to prevent UI freezing"""
    progress_updated = pyqtSignal(int, str)  # progress, status
    scan_completed = pyqtSignal(list)  # media_files
    scan_error = pyqtSignal(str)  # error message
    
    def __init__(self, media_handler, mount_point, media_type="all", start_range=None, end_range=None):
        super().__init__()
        self.media_handler = media_handler
        self.mount_point = mount_point
        self.media_type = media_type
        self.start_range = start_range
        self.end_range = end_range
        self._stop_requested = False
    
    def request_stop(self):
        """Request the thread to stop gracefully"""
        self._stop_requested = True
    
    def run(self):
        try:
            self.progress_updated.emit(0, "Starting scan...")
            media_files = self.media_handler.scan_media_with_progress(
                self.mount_point, 
                progress_callback=self._progress_callback,
                media_type=self.media_type,
                start_range=self.start_range,
                end_range=self.end_range
            )
            self.scan_completed.emit(media_files)
        except Exception as e:
            self.scan_error.emit(str(e))
    
    def _progress_callback(self, processed, total_files, filename):
        # Check if stop was requested
        if self._stop_requested:
            return False  # Signal to stop processing
        
        progress = int((processed / total_files) * 100) if total_files > 0 else 0
        status = f"Processing {filename} ({processed}/{total_files})"
        self.progress_updated.emit(progress, status)
        return True  # Continue processing

class DownloadThread(QThread):
    """Thread for downloading files to prevent UI freezing"""
    progress_updated = pyqtSignal(int, str)  # progress, status
    download_completed = pyqtSignal(dict)  # results
    download_error = pyqtSignal(str)  # error message
    
    def __init__(self, file_transfer, media_files, download_dir, device_name):
        super().__init__()
        self.file_transfer = file_transfer
        self.media_files = media_files
        self.download_dir = download_dir
        self.device_name = device_name
    
    def run(self):
        try:
            self.progress_updated.emit(0, "Starting download...")
            results = self.file_transfer.download_files(
                self.media_files,
                self.download_dir,
                self.device_name,
                progress_callback=self._progress_callback
            )
            self.download_completed.emit(results)
        except Exception as e:
            self.download_error.emit(str(e))
    
    def _progress_callback(self, progress, status):
        self.progress_updated.emit(progress, status)

class MediaItemWidget(QWidget):
    """Custom widget for displaying media items with thumbnails"""
    
    def __init__(self, media_file, parent=None):
        super().__init__(parent)
        self.media_file = media_file
        self.is_selected = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Checkbox for selection
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_selection_changed)
        layout.addWidget(self.checkbox)
        
        # Thumbnail/icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(60, 60)
        self.icon_label.setStyleSheet("border: 1px solid #ddd; background: #f5f5f5;")
        
        # Set icon based on file type
        if self.media_file.get('type') == 'photo':
            self.icon_label.setText("📷")
        else:
            self.icon_label.setText("🎥")
        
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # File info
        info_layout = QVBoxLayout()
        
        # File name
        file_name = self.media_file.get('name', 'Unknown')
        if file_name == 'Unknown':
            # Try to get filename from path
            file_path = self.media_file.get('path', '')
            if file_path:
                file_name = os.path.basename(file_path)
        self.name_label = QLabel(file_name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addWidget(self.name_label)
        
        # File details
        details = f"Size: {self.media_file.get('size', 'Unknown')}"
        if self.media_file.get('date'):
            details += f" | Date: {self.media_file.get('date')}"
        
        self.details_label = QLabel(details)
        self.details_label.setFont(QFont("Arial", 8))
        self.details_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.details_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def on_selection_changed(self, state):
        self.is_selected = state == Qt.CheckState.Checked.value
        if hasattr(self.parent(), 'on_media_selection_changed'):
            self.parent().on_media_selection_changed(self.media_file, self.is_selected)

class IPhoneMediaTransferApp(QMainWindow):
    """Main application window with modern PyQt6 interface"""
    
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.media_handler = MediaHandler()
        self.file_transfer = FileTransfer()
        self.config = Config()
        
        # Application state
        self.current_media = []
        self.selected_media = []
        self.current_filter = "all"  # all, photos, videos
        self.current_media_type = "all"  # all, photos, videos (for scanning)
        self.mount_point = None
        self.device_name = "iPhone"
        self.current_batch_start = 0
        
        # Threads
        self.scan_thread = None
        self.download_thread = None
        
        # Set window icon early in initialization
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()
        self.setup_logging()
        self.refresh_devices()
    
    def create_custom_title_bar(self):
        """Create custom title bar with integrated help button like Cursor IDE"""
        # Set window flags to create a frameless window with custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Create title bar widget
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-bottom: 1px solid #333333;
            }
        """)
        
        # Create title bar layout
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(10)
        
        # App icon (logo.png)
        app_icon = QLabel()
        app_icon.setFixedSize(20, 20)
        app_icon.setPixmap(QPixmap("icons/logo.png").scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        app_icon.setStyleSheet("""
            QLabel {
                background: transparent;
            }
        """)
        
        # App title
        app_title = QLabel("iPhone Media Transfer")
        app_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # Spacer to push controls to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Help button (integrated into title bar)
        self.help_btn = QPushButton()
        self.help_btn.setFixedSize(30, 20)
        self.help_btn.setIcon(QIcon("icons/help.svg"))
        self.help_btn.setIconSize(QSize(16, 16))
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 0.3);
            }
        """)
        self.help_btn.clicked.connect(self.show_help_menu)
        
        # Window control buttons with SVG icons
        self.minimize_btn = QPushButton()
        self.minimize_btn.setFixedSize(30, 20)
        self.minimize_btn.setIcon(QIcon("icons/minimize.svg"))
        self.minimize_btn.setIconSize(QSize(16, 16))
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton()
        self.maximize_btn.setFixedSize(30, 20)
        self.maximize_btn.setIcon(QIcon("icons/maximize.svg"))
        self.maximize_btn.setIconSize(QSize(16, 16))
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(30, 20)
        self.close_btn.setIcon(QIcon("icons/close.svg"))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        # Add widgets to title bar layout
        title_layout.addWidget(app_icon)
        title_layout.addWidget(app_title)
        title_layout.addWidget(spacer)
        title_layout.addWidget(self.help_btn)
        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(self.close_btn)
        
        self.title_bar.setLayout(title_layout)
        
        # Store for dragging
        self._drag_position = None
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
    
    def show_help_menu(self):
        """Show help menu as a popup"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtCore import QPoint
        
        help_menu = QMenu(self)
        help_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
        """)
        
        # Add menu actions
        user_guide_action = help_menu.addAction("📖 User Guide")
        user_guide_action.triggered.connect(self.show_user_guide)
        
        troubleshooting_action = help_menu.addAction("🔧 Troubleshooting")
        troubleshooting_action.triggered.connect(self.show_troubleshooting)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction("ℹ️ About")
        about_action.triggered.connect(self.show_about)
        
        # Show menu at help button position
        help_btn = self.sender()
        if help_btn:
            pos = help_btn.mapToGlobal(help_btn.rect().bottomLeft())
            help_menu.exec(pos)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def create_menu_bar(self):
        """Create menu bar (hidden since we have custom header)"""
        # Hide the menu bar since we have custom header with help
        menubar = self.menuBar()
        menubar.hide()
    
    def show_user_guide(self):
        """Show user guide dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("User Guide")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Create scroll area for content
        scroll = QScrollArea()
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # User guide content
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setHtml("""
        <h1>iPhone Media Transfer - User Guide</h1>
        
        <h2>Getting Started</h2>
        <ol>
        <li><b>Connect your iPhone</b> to your computer using a USB cable</li>
        <li><b>Unlock your iPhone</b> and tap "Trust This Computer" when prompted</li>
        <li><b>Launch the application</b> and wait for your device to appear in the dropdown</li>
        <li><b>Click "Mount Device"</b> to access your iPhone's media files</li>
        </ol>
        
        <h2>Scanning Media</h2>
        <h3>Full Scan (All Media)</h3>
        <ol>
        <li>Select "All Media" from the media type filter</li>
        <li>Click "🔍 Scan Media" to scan all photos and videos</li>
        <li>Wait for the scan to complete (progress bar will show status)</li>
        </ol>
        
        <h3>Filtered Scan</h3>
        <ol>
        <li>Select "Photos Only" or "Videos Only" from the media type filter</li>
        <li>Click "🔍 Scan Media" to scan only the selected type</li>
        </ol>
        
        <h3>Range Selection</h3>
        <ol>
        <li>Check "Use Range" to limit the number of files scanned</li>
        <li>Set "From" and "To" values (e.g., 1-100 to scan first 100 files)</li>
        <li>Click "🔍 Scan Media" to scan only the specified range</li>
        </ol>
        
        <h2>Downloading Media</h2>
        <h3>Select Files</h3>
        <ul>
        <li><b>Individual Selection:</b> Click on files in the list to select them</li>
        <li><b>Select All:</b> Click "Select All" to select all visible files</li>
        <li><b>Deselect All:</b> Click "Deselect All" to clear all selections</li>
        </ul>
        
        <h3>Download Options</h3>
        <ul>
        <li><b>Download Selected:</b> Download only the selected files</li>
        <li><b>Download Batch:</b> Download files in batches (useful for large collections)</li>
        </ul>
        
        <h3>Batch Downloading</h3>
        <ol>
        <li>Use range selection to limit files (e.g., 1-500)</li>
        <li>Download the batch</li>
        <li>Change range to next batch (e.g., 501-1000)</li>
        <li>Download to the same folder to continue the collection</li>
        </ol>
        
        <h2>Features</h2>
        <h3>Progress Tracking</h3>
        <ul>
        <li>Real-time progress bars for scanning and downloading</li>
        <li>Status messages showing current operation</li>
        <li>File count and completion percentage</li>
        </ul>
        
        <h3>File Organization</h3>
        <ul>
        <li>Files are saved in organized folders: <code>DeviceName_YYYYMMDD_HHMMSS/Photos</code> and <code>Videos</code></li>
        <li>Metadata files (.meta) are created for each media file</li>
        <li>Original file formats are preserved (HEIC stays HEIC, JPG stays JPG)</li>
        </ul>
        
        <h3>Stop Functionality</h3>
        <ul>
        <li>Click "⏹️ Stop Scan" to cancel scanning at any time</li>
        <li>Graceful stop without system warnings</li>
        <li>Can restart scanning immediately after stopping</li>
        </ul>
        
        <h2>Tips for Best Results</h2>
        <ul>
        <li><b>Use range selection</b> for large collections to avoid memory issues</li>
        <li><b>Download in batches</b> for better organization and progress tracking</li>
        <li><b>Keep your iPhone unlocked</b> during the transfer process</li>
        <li><b>Use a stable USB connection</b> to avoid transfer interruptions</li>
        <li><b>Check available disk space</b> before starting large downloads</li>
        </ul>
        
        <h2>Troubleshooting</h2>
        <p>If you encounter issues:</p>
        <ul>
        <li>Check the "Troubleshooting" menu for common solutions</li>
        <li>Ensure your iPhone is trusted and unlocked</li>
        <li>Try a different USB cable or port</li>
        <li>Restart the application if needed</li>
        </ul>
        """)
        
        content_layout.addWidget(guide_text)
        content.setLayout(content_layout)
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_troubleshooting(self):
        """Show troubleshooting dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Troubleshooting")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Create scroll area for content
        scroll = QScrollArea()
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Troubleshooting content
        troubleshooting_text = QTextEdit()
        troubleshooting_text.setReadOnly(True)
        troubleshooting_text.setHtml("""
        <h1>Troubleshooting Guide</h1>
        
        <h2>Common Issues and Solutions</h2>
        
        <h3>1. "No devices found" Error</h3>
        <p><b>Problem:</b> The application shows "No devices found" in the device dropdown.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Connect your iPhone via USB cable</li>
        <li>Unlock your iPhone (enter passcode or use Face ID/Touch ID)</li>
        <li>Trust the computer - when prompted on your iPhone, tap "Trust This Computer"</li>
        <li>Try refreshing - click "Refresh Devices" button</li>
        <li>Check cable - try a different USB cable</li>
        </ul>
        
        <h3>2. "Mount failed" Error</h3>
        <p><b>Problem:</b> Device is detected but mounting fails.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Unlock your iPhone completely</li>
        <li>Trust the computer again (disconnect and reconnect)</li>
        <li>Check if iPhone is in use - close any other apps that might be accessing photos</li>
        <li>Restart the application</li>
        </ul>
        
        <h3>3. Application Won't Start</h3>
        <p><b>Problem:</b> Application crashes or won't start.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Check Python version (should be 3.7+): <code>python3 --version</code></li>
        <li>Install missing dependencies: <code>pip install -r requirements.txt</code></li>
        <li>Check for errors in the terminal output</li>
        </ul>
        
        <h3>4. Permission Issues</h3>
        <p><b>Problem:</b> Cannot access iPhone files.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Add user to plugdev group: <code>sudo usermod -a -G plugdev $USER</code></li>
        <li>Log out and log back in (or restart)</li>
        <li>Check udev rules and reload them</li>
        </ul>
        
        <h3>5. Slow Performance</h3>
        <p><b>Problem:</b> Application is slow or freezes.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Use range selection to limit files (e.g., 1-100 instead of all files)</li>
        <li>Use media type filtering (Photos only or Videos only)</li>
        <li>Close other applications</li>
        <li>Use batch downloading for large collections</li>
        </ul>
        
        <h3>6. Files Not Downloading</h3>
        <p><b>Problem:</b> Files appear to download but are corrupted or missing.</p>
        <p><b>Solutions:</b></p>
        <ul>
        <li>Check disk space: <code>df -h</code></li>
        <li>Check download directory permissions</li>
        <li>Try a different download location</li>
        </ul>
        
        <h2>Quick Fixes</h2>
        <h3>Reset Application</h3>
        <pre><code># Remove configuration
rm ~/.iphone_transfer_config.json

# Remove logs
rm -rf ~/.iphone_transfer_logs/

# Restart application
python main_pyqt6.py</code></pre>
        
        <h3>Reinstall Dependencies</h3>
        <pre><code># Install system dependencies
sudo apt install libimobiledevice-utils ifuse ffmpeg

# Install Python dependencies
pip install -r requirements.txt</code></pre>
        
        <h2>Still Having Issues?</h2>
        <ul>
        <li>Check the terminal output for error messages</li>
        <li>Run diagnostic tests in the tests/ folder</li>
        <li>Try running as different user (if permission issues)</li>
        <li>Check if iPhone is supported (iOS 7+ should work)</li>
        </ul>
        """)
        
        content_layout.addWidget(troubleshooting_text)
        content.setLayout(content_layout)
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog with developer information"""
        dialog = QDialog(self)
        dialog.setWindowTitle("About iPhone Media Transfer")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Application info
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <div style="text-align: center;">
        <h1>iPhone Media Transfer</h1>
        <h2>Professional Media Transfer Application</h2>
        
        <p><b>Version:</b> 2.0.0</p>
        <p><b>Platform:</b> Linux (Ubuntu/Debian)</p>
        <p><b>Framework:</b> PyQt6</p>
        
        <hr>
        
        <h3>Developer Information</h3>
        <p><b>Name:</b> Parikshit Shaktawat</p>
        <p><b>Email:</b> parikshitshaktawat.it@gmail.com</p>
        
        <hr>
        
        <h3>Features</h3>
        <ul style="text-align: left;">
        <li>✅ iPhone device detection and mounting</li>
        <li>✅ Full media scanning with progress tracking</li>
        <li>✅ Range selection for batch processing</li>
        <li>✅ Media type filtering (Photos/Videos/All)</li>
        <li>✅ Batch downloading to organized folders</li>
        <li>✅ Graceful stop functionality</li>
        <li>✅ File integrity verification</li>
        <li>✅ Metadata preservation</li>
        <li>✅ Memory optimization for large collections</li>
        <li>✅ Modern PyQt6 interface</li>
        </ul>
        
        <hr>
        
        <h3>Technical Details</h3>
        <p><b>Core Technologies:</b></p>
        <ul style="text-align: left;">
        <li>Python 3.7+</li>
        <li>PyQt6 for modern GUI</li>
        <li>libimobiledevice for iPhone communication</li>
        <li>ifuse for iPhone mounting</li>
        <li>PIL/Pillow for image processing</li>
        <li>SHA256 for file integrity verification</li>
        </ul>
        
        <hr>
        
        <h3>Project Structure</h3>
        <p><b>Main Application:</b> main_pyqt6.py</p>
        <p><b>Core Modules:</b> modules/ (device_manager, media_handler, file_transfer, config, utils)</p>
        <p><b>Tests:</b> tests/ (unit tests and device detection tests)</p>
        <p><b>Debug Tools:</b> debug/ (analysis and troubleshooting scripts)</p>
        
        <hr>
        
        <p><i>Developed with ❤️ for seamless iPhone media transfer</i></p>
        <p><b>© 2025 Parikshit Shaktawat. All rights reserved.</b></p>
        """)
        
        layout.addWidget(about_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("iPhone Media Transfer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create custom title bar with integrated help button
        self.create_custom_title_bar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Set modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: white;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add custom title bar
        main_layout.addWidget(self.title_bar)
        
        # Create content widget for main application content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Create sections in content widget
        self.create_device_section(content_layout)
        self.create_control_section(content_layout)
        self.create_media_section(content_layout)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        
        # Create status section
        self.create_status_section(main_layout)
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
    
    def create_device_section(self, parent_layout):
        """Create device selection section"""
        device_group = QGroupBox("Device Selection")
        device_layout = QHBoxLayout()
        
        # Device dropdown
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        device_layout.addWidget(self.device_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_btn)
        
        # Mount/Unmount button
        self.mount_btn = QPushButton("📱 Mount Device")
        self.mount_btn.clicked.connect(self.toggle_mount)
        self.mount_btn.setEnabled(False)
        device_layout.addWidget(self.mount_btn)
        
        # Mount status indicator
        self.mount_status_label = QLabel("🔴 Not Mounted")
        self.mount_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        device_layout.addWidget(self.mount_status_label)
        
        device_layout.addStretch()
        device_group.setLayout(device_layout)
        parent_layout.addWidget(device_group)
    
    def create_control_section(self, parent_layout):
        """Create control buttons section"""
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        # Action buttons row
        action_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🔍 Scan Media")
        self.scan_btn.clicked.connect(self.scan_media)
        self.scan_btn.setEnabled(False)
        action_layout.addWidget(self.scan_btn)
        
        # Stop scan button
        self.stop_scan_btn = QPushButton("⏹️ Stop Scan")
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)
        action_layout.addWidget(self.stop_scan_btn)
        
        # Load range button
        self.load_range_btn = QPushButton("📋 Load Media Range")
        self.load_range_btn.clicked.connect(self.load_media_range)
        self.load_range_btn.setEnabled(False)
        action_layout.addWidget(self.load_range_btn)
        
        # Media type filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Media Type:"))
        
        self.filter_group = QButtonGroup()
        self.filter_all_btn = QRadioButton("All Media")
        self.filter_photos_btn = QRadioButton("Photos Only")
        self.filter_videos_btn = QRadioButton("Videos Only")
        
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.toggled.connect(lambda: self.set_media_type_filter("all"))
        self.filter_photos_btn.toggled.connect(lambda: self.set_media_type_filter("photos"))
        self.filter_videos_btn.toggled.connect(lambda: self.set_media_type_filter("videos"))
        
        filter_layout.addWidget(self.filter_all_btn)
        filter_layout.addWidget(self.filter_photos_btn)
        filter_layout.addWidget(self.filter_videos_btn)
        filter_layout.addStretch()
        
        action_layout.addLayout(filter_layout)
        
        # Range selection
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Range:"))
        
        self.range_start = QSpinBox()
        self.range_start.setMinimum(1)
        self.range_start.setMaximum(9999)
        self.range_start.setValue(1)
        self.range_start.setEnabled(False)
        range_layout.addWidget(QLabel("From:"))
        range_layout.addWidget(self.range_start)
        
        self.range_end = QSpinBox()
        self.range_end.setMinimum(1)
        self.range_end.setMaximum(9999)
        self.range_end.setValue(100)
        self.range_end.setEnabled(False)
        range_layout.addWidget(QLabel("To:"))
        range_layout.addWidget(self.range_end)
        
        self.range_enabled = QCheckBox("Use Range")
        self.range_enabled.toggled.connect(self.toggle_range_selection)
        range_layout.addWidget(self.range_enabled)
        
        range_layout.addStretch()
        action_layout.addLayout(range_layout)
        
        control_layout.addLayout(action_layout)
        
        # Batch download controls
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Download:"))
        
        self.batch_size = QSpinBox()
        self.batch_size.setMinimum(50)
        self.batch_size.setMaximum(1000)
        self.batch_size.setValue(500)
        self.batch_size.setSuffix(" files")
        batch_layout.addWidget(QLabel("Batch Size:"))
        batch_layout.addWidget(self.batch_size)
        
        self.download_batch_btn = QPushButton("📥 Download Batch")
        self.download_batch_btn.clicked.connect(self.download_batch)
        self.download_batch_btn.setEnabled(False)
        batch_layout.addWidget(self.download_batch_btn)
        
        batch_layout.addStretch()
        control_layout.addLayout(batch_layout)
        
        # Download buttons row
        download_layout = QHBoxLayout()
        
        self.download_selected_btn = QPushButton("📥 Download Selected")
        self.download_selected_btn.clicked.connect(self.download_selected)
        self.download_selected_btn.setEnabled(True)  # Enable by default
        download_layout.addWidget(self.download_selected_btn)
        
        self.download_all_btn = QPushButton("📥 Download All")
        self.download_all_btn.clicked.connect(self.download_all)
        self.download_all_btn.setEnabled(False)
        download_layout.addWidget(self.download_all_btn)
        
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setEnabled(False)
        download_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("☐ Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setEnabled(False)
        download_layout.addWidget(self.deselect_all_btn)
        
        download_layout.addStretch()
        control_layout.addLayout(download_layout)
        
        control_group.setLayout(control_layout)
        parent_layout.addWidget(control_group)
    
    def create_media_section(self, parent_layout):
        """Create media display section"""
        media_group = QGroupBox("Media Files")
        media_layout = QVBoxLayout()
        
        # Media list
        self.media_list = QListWidget()
        self.media_list.setMinimumHeight(400)
        media_layout.addWidget(self.media_list)
        
        # Load more button
        self.load_more_btn = QPushButton("📄 Load More Files")
        self.load_more_btn.clicked.connect(self.load_more_files)
        self.load_more_btn.setEnabled(False)
        media_layout.addWidget(self.load_more_btn)
        
        media_group.setLayout(media_layout)
        parent_layout.addWidget(media_group)
    
    def create_status_section(self, parent_layout):
        """Create status and progress section"""
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        parent_layout.addWidget(status_group)
    
    def refresh_devices(self):
        """Refresh the list of connected devices"""
        try:
            self.status_label.setText("Detecting devices...")
            devices = self.device_manager.detect_devices()
            
            self.device_combo.clear()
            
            if not devices:
                self.device_combo.addItem("No devices found")
                self.mount_btn.setEnabled(False)
                self.status_label.setText("No devices found")
            else:
                for device in devices:
                    device_name = device.get('name', 'Unknown Device')
                    if device.get('status') == 'needs_trust':
                        device_name += " (Not Trusted)"
                    self.device_combo.addItem(device_name, device)
                
                self.mount_btn.setEnabled(True)
                self.status_label.setText(f"Found {len(devices)} device(s)")
                
        except Exception as e:
            self.logger.error(f"Error detecting devices: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def toggle_mount(self):
        """Toggle device mount/unmount"""
        if self.mount_point:
            self.unmount_device()
        else:
            self.mount_device()
    
    def mount_device(self):
        """Mount the selected device"""
        try:
            current_data = self.device_combo.currentData()
            if not current_data:
                return
            
            if current_data.get('status') == 'needs_trust':
                QMessageBox.information(
                    self, 
                    "Device Not Trusted",
                    "Please trust this computer on your iPhone:\n\n"
                    "1. Unlock your iPhone\n"
                    "2. Tap 'Trust This Computer'\n"
                    "3. Enter your passcode if prompted\n"
                    "4. Click Refresh to try again"
                )
                return
            
            self.status_label.setText("Mounting device...")
            self.mount_btn.setEnabled(False)
            
            # Mount device
            self.mount_point = self.device_manager.mount_device(current_data['udid'])
            self.device_name = self.device_manager.get_device_name()
            
            # Update mount status indicator
            self.mount_status_label.setText("🟢 Mounted")
            self.mount_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.mount_btn.setText("📱 Unmount Device")
            
            self.status_label.setText(f"Device mounted at {self.mount_point}")
            self.scan_btn.setEnabled(True)
            self.mount_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error mounting device: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.mount_btn.setEnabled(True)
    
    def unmount_device(self):
        """Unmount the current device"""
        try:
            if self.mount_point:
                self.device_manager.unmount_device()
                self.mount_point = None
                
                # Update mount status indicator
                self.mount_status_label.setText("🔴 Not Mounted")
                self.mount_status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
                self.mount_btn.setText("📱 Mount Device")
                
                # Clear media and disable scan
                self.current_media = []
                self.media_list.clear()
                self.scan_btn.setEnabled(False)
                self.download_all_btn.setEnabled(False)
                self.download_selected_btn.setEnabled(False)
                self.select_all_btn.setEnabled(False)
                self.deselect_all_btn.setEnabled(False)
                self.load_more_btn.setEnabled(False)
                
                self.status_label.setText("Device unmounted")
                
        except Exception as e:
            self.logger.error(f"Error unmounting device: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def scan_media(self):
        """Start scanning media files"""
        if not self.mount_point:
            return
        
        try:
            # Use media type filter instead of file limits
            media_type = getattr(self, 'current_media_type', 'all')
            
            # Check if range is enabled
            if self.range_enabled.isChecked():
                start_range = self.range_start.value()
                end_range = self.range_end.value()
                if start_range >= end_range:
                    QMessageBox.warning(self, "Invalid Range", "Start must be less than end")
                    return
                self.status_label.setText(f"Scanning {media_type} files {start_range}-{end_range}...")
            else:
                if media_type == "photos":
                    self.status_label.setText("Scanning all photos...")
                elif media_type == "videos":
                    self.status_label.setText("Scanning all videos...")
                else:  # all
                    self.status_label.setText("Scanning all media files...")
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.scan_btn.setEnabled(False)
            self.stop_scan_btn.setEnabled(True)
            
            # Start scan thread with media type filter and range
            start_range = self.range_start.value() if self.range_enabled.isChecked() else None
            end_range = self.range_end.value() if self.range_enabled.isChecked() else None
            
            self.scan_thread = ScanMediaThread(self.media_handler, self.mount_point, media_type, start_range, end_range)
            self.scan_thread.progress_updated.connect(self.update_scan_progress)
            self.scan_thread.scan_completed.connect(self.scan_completed)
            self.scan_thread.scan_error.connect(self.scan_error)
            self.scan_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting scan: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.scan_btn.setEnabled(True)
            self.stop_scan_btn.setEnabled(False)
    
    def update_scan_progress(self, progress, status):
        """Update scan progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def scan_completed(self, media_files):
        """Handle scan completion"""
        # Media files are already filtered by range during scanning
        self.current_media = media_files
        
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.load_range_btn.setEnabled(True)
        self.download_batch_btn.setEnabled(True)
        
        # Reset batch start position
        self.current_batch_start = 0
        
        # Count media types
        photo_count = len([f for f in self.current_media if f.get('type') == 'photo'])
        video_count = len([f for f in self.current_media if f.get('type') == 'video'])
        
        # Update status
        if self.range_enabled.isChecked():
            self.status_label.setText(f"Loaded {len(self.current_media)} files from range {self.range_start.value()}-{self.range_end.value()}")
        else:
            if self.current_media_type == "photos":
                self.status_label.setText(f"Found {photo_count} photos")
            elif self.current_media_type == "videos":
                self.status_label.setText(f"Found {video_count} videos")
            else:
                self.status_label.setText(f"Found {photo_count} photos and {video_count} videos")
        
        # Display media files
        self.display_media()
        
        # Enable controls
        self.download_all_btn.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)
        self.load_more_btn.setEnabled(True)
        self.load_range_btn.setEnabled(True)
        
        # Update range controls - set reasonable maximums
        if self.current_media:
            total_files = len(self.current_media)
            # Set maximum to a reasonable value, not limited by current media
            max_range = max(1000, total_files)  # At least 1000, or total files if more
            self.range_start.setMaximum(max_range)
            self.range_end.setMaximum(max_range)
            # Only update end value if it's currently 0 or invalid
            if self.range_end.value() == 0 or self.range_end.value() > total_files:
                self.range_end.setValue(min(100, total_files))
    
    def stop_scan(self):
        """Stop the current scan operation"""
        if hasattr(self, 'scan_thread') and self.scan_thread and self.scan_thread.isRunning():
            self.logger.info("Stopping scan operation...")
            self.scan_thread.request_stop()  # Request graceful stop
            
            # Reset UI state immediately
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.stop_scan_btn.setEnabled(False)
            self.status_label.setText("Stopping scan...")
            
            # Clear any partial results
            self.current_media = []
            self.media_list.clear()
            
            self.logger.info("Scan stop requested")
    
    def scan_error(self, error_msg):
        """Handle scan error"""
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.status_label.setText(f"Scan error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", f"Error scanning media: {error_msg}")
    
    def display_media(self):
        """Display media files in the list"""
        self.media_list.clear()
        
        # Get filtered media
        filtered_media = self.get_filtered_media()
        
        # Display first 100 files (lazy loading)
        display_count = min(100, len(filtered_media))
        
        for i in range(display_count):
            media_file = filtered_media[i]
            
            # Create custom widget for media item
            item_widget = MediaItemWidget(media_file)
            
            # Create list item
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            
            # Add to list
            self.media_list.addItem(list_item)
            self.media_list.setItemWidget(list_item, item_widget)
        
        # Update load more button
        if len(filtered_media) > 100:
            self.load_more_btn.setText(f"📄 Load More ({len(filtered_media) - 100} remaining)")
        else:
            self.load_more_btn.setEnabled(False)
    
    def get_filtered_media(self):
        """Get media files based on current filter"""
        if self.current_filter == "all":
            return self.current_media
        elif self.current_filter == "photos":
            return [m for m in self.current_media if m.get('type') == 'photo']
        elif self.current_filter == "videos":
            return [m for m in self.current_media if m.get('type') == 'video']
        return self.current_media
    
    def toggle_range_selection(self, enabled):
        """Toggle range selection controls"""
        self.range_start.setEnabled(enabled)
        self.range_end.setEnabled(enabled)
        
        if enabled:
            # Set default range values
            self.range_start.setValue(1)
            self.range_end.setValue(100)
            
            if self.current_media:
                # Set maximum to a reasonable value, not limited by current media
                total_files = len(self.current_media)
                max_range = max(1000, total_files)  # At least 1000, or total files if more
                self.range_start.setMaximum(max_range)
                self.range_end.setMaximum(max_range)
                # Only update end value if it's currently 0 or invalid
                if self.range_end.value() == 0 or self.range_end.value() > total_files:
                    self.range_end.setValue(min(100, total_files))
    
    def get_range_media(self):
        """Get media files within the selected range"""
        if not self.range_enabled.isChecked():
            return self.get_filtered_media()
        
        start_idx = self.range_start.value() - 1  # Convert to 0-based index
        end_idx = self.range_end.value()
        
        filtered_media = self.get_filtered_media()
        return filtered_media[start_idx:end_idx]
    
    def load_media_range(self):
        """Load media files in a specific range like the original iphone_transfer.py"""
        if not self.current_media:
            QMessageBox.warning(self, "No Media", "Please scan media first")
            return
        
        total_media = len(self.current_media)
        
        # Create range dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Media Range")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel(f"Found {total_media} media files")
        layout.addWidget(info_label)
        
        # Range inputs
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Start:"))
        
        start_spin = QSpinBox()
        start_spin.setMinimum(1)
        start_spin.setMaximum(total_media)
        start_spin.setValue(1)
        range_layout.addWidget(start_spin)
        
        range_layout.addWidget(QLabel("End:"))
        
        end_spin = QSpinBox()
        end_spin.setMinimum(1)
        end_spin.setMaximum(total_media)
        end_spin.setValue(min(100, total_media))
        range_layout.addWidget(end_spin)
        
        layout.addLayout(range_layout)
        
        # Media type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Media Type:"))
        
        type_all = QRadioButton("All")
        type_photos = QRadioButton("Photos Only")
        type_videos = QRadioButton("Videos Only")
        type_all.setChecked(True)
        
        type_layout.addWidget(type_all)
        type_layout.addWidget(type_photos)
        type_layout.addWidget(type_videos)
        layout.addLayout(type_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        load_btn = QPushButton("Load")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        def on_load():
            start = start_spin.value() - 1  # Convert to 0-based index
            end = end_spin.value()
            
            if start >= end:
                QMessageBox.warning(dialog, "Invalid Range", "Start must be less than end")
                return
            
            # Determine media type filter
            if type_photos.isChecked():
                media_type = "photo"
            elif type_videos.isChecked():
                media_type = "video"
            else:
                media_type = "all"
            
            # Filter media by type and range
            filtered_media = []
            for i, media_file in enumerate(self.current_media):
                if i < start or i >= end:
                    continue
                
                file_type = media_file.get('type', 'photo')
                if media_type == "all" or file_type == media_type:
                    filtered_media.append(media_file)
            
            dialog.accept()
            
            # Load the filtered media
            self.current_media = filtered_media
            self.display_media()
            
            # Update status
            self.status_label.setText(f"Loaded {len(filtered_media)} files from range {start+1}-{end}")
            
            # Enable download buttons
            self.download_all_btn.setEnabled(True)
            self.download_selected_btn.setEnabled(True)
        
        load_btn.clicked.connect(on_load)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def set_filter(self, filter_type):
        """Set the current filter"""
        self.current_filter = filter_type
        self.display_media()
    
    def set_media_type_filter(self, media_type):
        """Set the media type filter for scanning"""
        self.current_media_type = media_type
        self.logger.info(f"Media type filter set to: {media_type}")
    
    def deselect_all(self):
        """Deselect all media files"""
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.selected_media.clear()
    
    def load_more_files(self):
        """Load more files into the display"""
        # For now, just show all files
        self.display_media()
        self.load_more_btn.setEnabled(False)
    
    def select_all(self):
        """Select all visible media files"""
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
    
    def clear_selection(self):
        """Clear all selections"""
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.selected_media.clear()
    
    def download_selected(self):
        """Download selected media files"""
        # Get selected media from the UI
        selected_media = []
        for i in range(self.media_list.count()):
            item = self.media_list.item(i)
            widget = self.media_list.itemWidget(item)
            if widget and hasattr(widget, 'checkbox') and widget.checkbox.isChecked():
                selected_media.append(widget.media_file)
        
        if not selected_media:
            QMessageBox.information(self, "No Selection", "Please select files to download")
            return
        
        self.start_download(selected_media)
    
    def download_all(self):
        """Download all filtered media files or range if specified"""
        media_to_download = self.get_range_media()
        if not media_to_download:
            QMessageBox.information(self, "No Files", "No files to download")
            return
        
        self.start_download(media_to_download)
    
    def download_batch(self):
        """Download a batch of media files"""
        if not self.current_media:
            QMessageBox.information(self, "No Media", "Please scan media files first")
            return
        
        batch_size = self.batch_size.value()
        start_idx = self.current_batch_start
        end_idx = min(start_idx + batch_size, len(self.current_media))
        
        if start_idx >= len(self.current_media):
            QMessageBox.information(self, "Batch Complete", "All files have been downloaded")
            return
        
        # Get batch of media files
        batch_media = self.current_media[start_idx:end_idx]
        
        # Update batch start for next download
        self.current_batch_start = end_idx
        
        # Update status
        self.status_label.setText(f"Downloading batch {start_idx+1}-{end_idx} of {len(self.current_media)} files")
        
        # Start download
        self.start_download(batch_media)
        
        # Update batch info
        remaining = len(self.current_media) - end_idx
        if remaining > 0:
            self.status_label.setText(f"Batch downloaded. {remaining} files remaining. Click 'Download Batch' for next batch.")
        else:
            self.status_label.setText("All files downloaded!")
            self.download_batch_btn.setEnabled(False)
    
    def start_download(self, media_files):
        """Start download process"""
        try:
            # Get download directory
            download_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Download Directory",
                str(Path.home() / "Pictures" / "iPhone_Media")
            )
            
            if not download_dir:
                return
            
            self.status_label.setText("Starting download...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Disable buttons
            self.download_selected_btn.setEnabled(False)
            self.download_all_btn.setEnabled(False)
            
            # Start download thread
            self.download_thread = DownloadThread(
                self.file_transfer, 
                media_files, 
                download_dir, 
                self.device_name
            )
            self.download_thread.progress_updated.connect(self.update_download_progress)
            self.download_thread.download_completed.connect(self.download_completed)
            self.download_thread.download_error.connect(self.download_error)
            self.download_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting download: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.progress_bar.setVisible(False)
            self.download_selected_btn.setEnabled(True)
            self.download_all_btn.setEnabled(True)
    
    def update_download_progress(self, progress, status):
        """Update download progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def download_completed(self, results):
        """Handle download completion"""
        self.progress_bar.setVisible(False)
        self.download_selected_btn.setEnabled(True)
        self.download_all_btn.setEnabled(True)
        
        success = results.get('success', 0)
        failed = results.get('failed', 0)
        skipped = results.get('skipped', 0)
        download_path = results.get('download_path', '')
        
        self.status_label.setText(f"Download complete: {success} success, {failed} failed, {skipped} skipped")
        
        QMessageBox.information(
            self, 
            "Download Complete",
            f"Download completed!\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"⏭️ Skipped: {skipped}\n\n"
            f"Files saved to: {download_path}"
        )
    
    def download_error(self, error_msg):
        """Handle download error"""
        self.progress_bar.setVisible(False)
        self.download_selected_btn.setEnabled(True)
        self.download_all_btn.setEnabled(True)
        self.status_label.setText(f"Download error: {error_msg}")
        QMessageBox.critical(self, "Download Error", f"Error downloading files: {error_msg}")
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Cleanup threads
            if self.scan_thread and self.scan_thread.isRunning():
                self.scan_thread.terminate()
                self.scan_thread.wait()
            
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait()
            
            # Unmount device
            if self.mount_point:
                self.unmount_device()
            
            # Save config
            self.config.save()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("iPhone Media Transfer")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Media Transfer Tools")
    
    # Create and show main window
    window = IPhoneMediaTransferApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
