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
    QRadioButton, QScrollArea, QSizePolicy, QSpinBox
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
    
    def __init__(self, media_handler, mount_point):
        super().__init__()
        self.media_handler = media_handler
        self.mount_point = mount_point
    
    def run(self):
        try:
            self.progress_updated.emit(0, "Starting scan...")
            media_files = self.media_handler.scan_media_with_progress(
                self.mount_point, 
                progress_callback=self._progress_callback
            )
            self.scan_completed.emit(media_files)
        except Exception as e:
            self.scan_error.emit(str(e))
    
    def _progress_callback(self, processed, total_files, filename):
        progress = int((processed / total_files) * 100) if total_files > 0 else 0
        status = f"Processing {filename} ({processed}/{total_files})"
        self.progress_updated.emit(progress, status)

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
        self.mount_point = None
        self.device_name = "iPhone"
        
        # Threads
        self.scan_thread = None
        self.download_thread = None
        
        self.setup_ui()
        self.setup_logging()
        self.refresh_devices()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("iPhone Media Transfer - PyQt6")
        self.setGeometry(100, 100, 1400, 900)
        
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
        
        # Create sections
        self.create_device_section(main_layout)
        self.create_control_section(main_layout)
        self.create_media_section(main_layout)
        self.create_status_section(main_layout)
    
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
        
        # Load range button
        self.load_range_btn = QPushButton("📋 Load Media Range")
        self.load_range_btn.clicked.connect(self.load_media_range)
        self.load_range_btn.setEnabled(False)
        action_layout.addWidget(self.load_range_btn)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_group = QButtonGroup()
        self.filter_all_btn = QRadioButton("All")
        self.filter_photos_btn = QRadioButton("Photos (500 max)")
        self.filter_videos_btn = QRadioButton("Videos (50 max)")
        
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.toggled.connect(lambda: self.set_filter("all"))
        self.filter_photos_btn.toggled.connect(lambda: self.set_filter("photos"))
        self.filter_videos_btn.toggled.connect(lambda: self.set_filter("videos"))
        
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
        
        self.clear_selection_btn = QPushButton("☐ Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        self.clear_selection_btn.setEnabled(False)
        download_layout.addWidget(self.clear_selection_btn)
        
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
                self.clear_selection_btn.setEnabled(False)
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
            # Set file limits based on current filter
            if self.current_filter == "photos":
                self.media_handler.set_file_limits(max_photos=500, max_videos=0, max_total=500)
                self.status_label.setText("Scanning photos only (max 500)...")
            elif self.current_filter == "videos":
                self.media_handler.set_file_limits(max_photos=0, max_videos=50, max_total=50)
                self.status_label.setText("Scanning videos only (max 50)...")
            else:  # all
                self.media_handler.set_file_limits(max_photos=500, max_videos=100, max_total=600)
                self.status_label.setText("Scanning all media files...")
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.scan_btn.setEnabled(False)
            
            # Start scan thread
            self.scan_thread = ScanMediaThread(self.media_handler, self.mount_point)
            self.scan_thread.progress_updated.connect(self.update_scan_progress)
            self.scan_thread.scan_completed.connect(self.scan_completed)
            self.scan_thread.scan_error.connect(self.scan_error)
            self.scan_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting scan: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.scan_btn.setEnabled(True)
    
    def update_scan_progress(self, progress, status):
        """Update scan progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def scan_completed(self, media_files):
        """Handle scan completion"""
        self.current_media = media_files
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.load_range_btn.setEnabled(True)
        
        # Update status based on filter
        if self.current_filter == "photos":
            if len(media_files) >= 500:
                self.status_label.setText(f"Found {len(media_files)} photos (limited to 500)")
                QMessageBox.information(
                    self, 
                    "Photo Limit Reached",
                    f"Found {len(media_files)} photos, but limited to 500 to prevent system overload.\n\n"
                    f"To scan more photos, try scanning in smaller batches."
                )
            else:
                self.status_label.setText(f"Found {len(media_files)} photos")
        elif self.current_filter == "videos":
            if len(media_files) >= 50:
                self.status_label.setText(f"Found {len(media_files)} videos (limited to 50)")
                QMessageBox.information(
                    self, 
                    "Video Limit Reached",
                    f"Found {len(media_files)} videos, but limited to 50 to prevent system overload.\n\n"
                    f"To scan more videos, try scanning in smaller batches."
                )
            else:
                self.status_label.setText(f"Found {len(media_files)} videos")
        else:  # all
            if len(media_files) >= 600:
                self.status_label.setText(f"Found {len(media_files)} media files (limited to prevent system overload)")
                QMessageBox.warning(
                    self, 
                    "File Limit Reached",
                    f"Found {len(media_files)} media files, but limited to 600 to prevent system overload.\n\n"
                    f"This includes up to 500 photos and 100 videos.\n"
                    f"To transfer more files, you may need to transfer in batches."
                )
            else:
                self.status_label.setText(f"Found {len(media_files)} media files")
        
        # Display media files
        self.display_media()
        
        # Enable controls
        self.download_all_btn.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.clear_selection_btn.setEnabled(True)
        self.load_more_btn.setEnabled(True)
        self.load_range_btn.setEnabled(True)
        
        # Update range controls
        if self.current_media:
            total_files = len(self.current_media)
            self.range_start.setMaximum(total_files)
            self.range_end.setMaximum(total_files)
            self.range_end.setValue(min(100, total_files))
    
    def scan_error(self, error_msg):
        """Handle scan error"""
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
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
        
        if enabled and self.current_media:
            # Set default range based on current media count
            total_files = len(self.current_media)
            self.range_start.setMaximum(total_files)
            self.range_end.setMaximum(total_files)
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
