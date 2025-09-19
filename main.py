#!/usr/bin/env python3
"""
iPhone Media Transfer Application
Main application module with GUI interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
from pathlib import Path
import threading

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.device_manager import DeviceManager
from modules.media_handler import MediaHandler
from modules.file_transfer import FileTransfer
from modules.config import Config
from modules.utils import setup_logging

class IPhoneMediaTransferApp:
    """Main application class for iPhone media transfer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("iPhone Media Transfer")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules
        self.config = Config()
        self.device_manager = DeviceManager()
        self.media_handler = MediaHandler()
        self.file_transfer = FileTransfer()
        
        # Application state
        self.current_device = None
        self.current_media = []
        self.selected_media = []  # Changed from set to list
        self.is_loading = False
        self.current_filter = "all"  # all, photos, videos
        
        # Create UI
        self.create_ui()
        
        # Initialize
        self.initialize_app()
    
    def create_ui(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # Media display area
        self.create_media_display(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_control_panel(self, parent):
        """Create the control panel with device selection and actions"""
        control_frame = ttk.LabelFrame(parent, text="Device & Actions", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Device selection row
        device_frame = ttk.Frame(control_frame)
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(device_frame, text="Device:").pack(side=tk.LEFT, padx=(0, 5))
        self.device_combo = ttk.Combobox(device_frame, state="readonly", width=40)
        self.device_combo.pack(side=tk.LEFT, padx=5)
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        self.refresh_btn = ttk.Button(device_frame, text="Refresh Devices", 
                                    command=self.refresh_devices)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Filter buttons row
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_all_btn = ttk.Button(filter_frame, text="All", 
                                        command=lambda: self.set_filter("all"))
        self.filter_all_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_photos_btn = ttk.Button(filter_frame, text="Photos", 
                                           command=lambda: self.set_filter("photos"))
        self.filter_photos_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_videos_btn = ttk.Button(filter_frame, text="Videos", 
                                          command=lambda: self.set_filter("videos"))
        self.filter_videos_btn.pack(side=tk.LEFT, padx=2)
        
        # Action buttons row
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X)
        
        self.scan_btn = ttk.Button(action_frame, text="Scan Media", 
                                 command=self.scan_media, state=tk.DISABLED)
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_btn = ttk.Button(action_frame, text="Download Selected", 
                                     command=self.download_selected, state=tk.DISABLED)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_all_btn = ttk.Button(action_frame, text="Download All", 
                                         command=self.download_all, state=tk.DISABLED)
        self.download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(action_frame, text="Clear", 
                                  command=self.clear_media, state=tk.DISABLED)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings
        settings_btn = ttk.Button(action_frame, text="Settings", 
                               command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_media_display(self, parent):
        """Create the media display area with thumbnails"""
        media_frame = ttk.LabelFrame(parent, text="Media Files", padding="10")
        media_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbar
        canvas_frame = ttk.Frame(media_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", 
                                     command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame inside canvas for media items
        self.media_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.media_frame, anchor="nw")
        
        # Bind canvas events
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.media_frame.bind("<Configure>", self._on_media_frame_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def create_status_bar(self, parent):
        """Create the status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                    anchor=tk.W, relief=tk.SUNKEN, padding=(5, 2))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Progress bar and text
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.progress_text = tk.StringVar(value="")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text, 
                                      font=("Arial", 8))
        self.progress_label.pack(side=tk.TOP)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                         maximum=100, length=200)
        self.progress_bar.pack(side=tk.BOTTOM)
    
    def initialize_app(self):
        """Initialize the application"""
        try:
            self.logger.info("Initializing iPhone Media Transfer App")
            self.status_var.set("Initializing...")
            self.root.update()
            
            # Check dependencies
            if not self.device_manager.check_dependencies():
                messagebox.showerror("Dependencies Missing", 
                                   "Required dependencies are missing. Please install them first.")
                return
            
            # Load configuration
            self.config.load()
            
            # Detect devices
            self.refresh_devices()
            
            self.status_var.set("Ready")
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {str(e)}")
            messagebox.showerror("Initialization Error", f"Failed to initialize: {str(e)}")
    
    def refresh_devices(self):
        """Refresh the list of connected devices"""
        try:
            self.status_var.set("Detecting devices...")
            self.refresh_btn.config(state=tk.DISABLED)
            self.root.update()
            
            devices = self.device_manager.detect_devices()
            
            if devices:
                device_list = []
                for device in devices:
                    if device.get('status') == 'needs_trust':
                        device_list.append(f"{device['name']} - Click to Trust")
                    else:
                        device_list.append(f"{device['name']} ({device['udid']})")
                
                self.device_combo['values'] = device_list
                self.device_combo.current(0)
                self.status_var.set(f"Found {len(devices)} device(s)")
            else:
                self.device_combo['values'] = ["No devices found"]
                self.device_combo.current(0)
                self.status_var.set("No devices found")
            
            self.refresh_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.logger.error(f"Error detecting devices: {str(e)}")
            self.status_var.set("Error detecting devices")
            self.refresh_btn.config(state=tk.NORMAL)
            messagebox.showerror("Device Detection Error", f"Failed to detect devices: {str(e)}")
    
    def on_device_selected(self, event):
        """Handle device selection"""
        selection = self.device_combo.get()
        if "No devices found" in selection:
            return
        
        try:
            if "Click to Trust" in selection:
                # Show trust instructions
                self.status_var.set("iPhone needs to be trusted")
                messagebox.showinfo(
                    "Trust iPhone", 
                    "To use your iPhone with this application:\n\n"
                    "1. Make sure your iPhone is UNLOCKED\n"
                    "2. Disconnect and reconnect the USB cable\n"
                    "3. When prompted on your iPhone, tap 'Trust This Computer'\n"
                    "4. Enter your iPhone passcode\n"
                    "5. Click 'Refresh Devices' after trusting\n\n"
                    "If you don't see the trust dialog:\n"
                    "Go to iPhone Settings > General > Reset > Reset Location & Privacy"
                )
                return
            
            # Extract UDID from selection
            udid = selection.split("(")[-1].rstrip(")")
            self.current_device = udid
            
            self.status_var.set(f"Selected device: {udid}")
            self.scan_btn.config(state=tk.NORMAL)
            
            # Auto-mount device
            self.mount_device()
            
        except Exception as e:
            self.logger.error(f"Error selecting device: {str(e)}")
            messagebox.showerror("Device Selection Error", f"Failed to select device: {str(e)}")
    
    def mount_device(self):
        """Mount the selected device"""
        try:
            self.status_var.set("Mounting device...")
            self.root.update()
            
            mount_point = self.device_manager.mount_device(self.current_device)
            if mount_point:
                self.status_var.set(f"Device mounted at {mount_point}")
                self.logger.info(f"Device mounted successfully at {mount_point}")
            else:
                self.status_var.set("Failed to mount device")
                messagebox.showerror("Mount Error", "Failed to mount device. Please check connection.")
                
        except Exception as e:
            self.logger.error(f"Error mounting device: {str(e)}")
            self.status_var.set("Mount failed")
            messagebox.showerror("Mount Error", f"Failed to mount device: {str(e)}")
    
    def scan_media(self):
        """Scan for media files on the device"""
        if self.is_loading:
            return
            
        self.is_loading = True
        self.status_var.set("Scanning for media...")
        self.progress_var.set(0)
        self.progress_text.set("Starting scan...")
        self.scan_btn.config(state=tk.DISABLED)
        self.root.update()
        
        # Start scanning in a separate thread
        scan_thread = threading.Thread(target=self._scan_media_thread)
        scan_thread.daemon = True
        scan_thread.start()
    
    def _scan_media_thread(self):
        """Threaded media scanning with progress updates"""
        try:
            # Get media files with progress callback
            media_files = self.media_handler.scan_media_with_progress(
                self.device_manager.mount_point, 
                self._update_scan_progress
            )
            
            # Update UI in main thread
            self.root.after(0, self._scan_media_complete, media_files)
            
        except Exception as e:
            self.logger.error(f"Error scanning media: {str(e)}")
            self.root.after(0, self._scan_media_error, str(e))
    
    def _update_scan_progress(self, current, total, filename):
        """Update progress during scanning"""
        if total > 0:
            progress = (current / total) * 100
            self.root.after(0, self._update_progress_ui, progress, f"Scanning: {filename}")
    
    def _update_progress_ui(self, progress, text):
        """Update progress UI (called from main thread)"""
        self.progress_var.set(progress)
        self.progress_text.set(text)
        self.root.update()
    
    def _scan_media_complete(self, media_files):
        """Handle scan completion"""
        self.is_loading = False
        self.current_media = media_files
        
        if media_files:
            self.display_media(media_files)
            self.download_btn.config(state=tk.NORMAL)
            self.download_all_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
            
            # Check if we hit file limits
            if len(media_files) >= 600:  # max_total limit
                self.status_var.set(f"Found {len(media_files)} media files (limited to prevent system overload)")
                self.progress_text.set("Limited to 600 files")
                messagebox.showwarning("File Limit Reached", 
                    f"Found {len(media_files)} media files, but limited to 600 to prevent system overload.\n\n"
                    f"This includes up to 500 photos and 100 videos.\n"
                    f"To transfer more files, you may need to transfer in batches.")
            else:
                self.status_var.set(f"Found {len(media_files)} media files")
                self.progress_text.set("Scan complete!")
        else:
            self.status_var.set("No media files found")
            self.progress_text.set("No files found")
            messagebox.showinfo("No Media", "No media files found on the device")
        
        self.scan_btn.config(state=tk.NORMAL)
        self.progress_var.set(100)
    
    def _scan_media_error(self, error_msg):
        """Handle scan error"""
        self.is_loading = False
        self.status_var.set("Scan failed")
        self.progress_text.set("Scan failed")
        messagebox.showerror("Scan Error", f"Failed to scan media: {error_msg}")
        self.scan_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
    
    def display_media(self, media_files):
        """Display media files in the grid with lazy loading"""
        # Clear existing items
        for widget in self.media_frame.winfo_children():
            widget.destroy()
        
        # Apply filter
        filtered_files = self.get_filtered_media()
        
        # Limit initial display to prevent memory issues
        max_initial_display = 100  # Show only first 100 files initially
        display_files = filtered_files[:max_initial_display]
        
        # Create grid layout
        cols = 5  # Number of columns
        for i, media_file in enumerate(display_files):
            row = i // cols
            col = i % cols
            
            self.create_media_item(media_file, row, col)
        
        # Add "Load More" button if there are more files
        if len(media_files) > max_initial_display:
            remaining = len(media_files) - max_initial_display
            load_more_frame = ttk.Frame(self.media_frame)
            load_more_frame.grid(row=(len(display_files) // cols) + 1, column=0, 
                               columnspan=cols, pady=20, sticky="ew")
            
            load_more_btn = ttk.Button(load_more_frame, 
                                     text=f"Load More ({remaining} files remaining)",
                                     command=lambda: self.load_more_media(media_files, max_initial_display))
            load_more_btn.pack()
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def create_media_item(self, media_file, row, col):
        """Create a media item widget with lazy thumbnail loading"""
        item_frame = ttk.Frame(self.media_frame, padding=5)
        item_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Checkbox for selection
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(item_frame, variable=var,
                           command=lambda mf=media_file, v=var: self.toggle_selection(mf, v.get()))
        cb.pack(anchor=tk.W)
        
        # Thumbnail (placeholder - no actual thumbnail loading to prevent memory issues)
        file_ext = os.path.splitext(media_file['path'])[1].lower()
        if file_ext in ['.mp4', '.mov', '.m4v']:
            thumb_text = "🎥"
        else:
            thumb_text = "📷"
        
        thumb_label = ttk.Label(item_frame, text=thumb_text, font=("Arial", 24))
        thumb_label.pack(pady=2)
        
        # Filename
        filename = os.path.basename(media_file['path'])
        if len(filename) > 20:
            filename = filename[:17] + "..."
        
        name_label = ttk.Label(item_frame, text=filename, wraplength=100)
        name_label.pack()
        
        # File size
        size_mb = media_file.get('size', 0) / (1024 * 1024)
        size_text = f"{size_mb:.1f} MB"
        size_label = ttk.Label(item_frame, text=size_text, font=("Arial", 8))
        size_label.pack()
    
    def load_more_media(self, media_files, start_index):
        """Load more media files into the display"""
        # This would be implemented to load more files when "Load More" is clicked
        # For now, just show a message
        messagebox.showinfo("Load More", f"Loading more files from index {start_index}...")
    
    def toggle_selection(self, media_file, is_selected):
        """Toggle selection of a media file"""
        if is_selected:
            if media_file not in self.selected_media:
                self.selected_media.append(media_file)
        else:
            if media_file in self.selected_media:
                self.selected_media.remove(media_file)
    
    def download_selected(self):
        """Download selected media files"""
        if not self.selected_media:
            messagebox.showinfo("No Selection", "No files selected for download")
            return
        
        try:
            self.status_var.set(f"Downloading {len(self.selected_media)} files...")
            self.download_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Download files
            device_name = self.device_manager.get_device_name()
            results = self.file_transfer.download_files(list(self.selected_media), 
                                                      self.config.download_dir, device_name)
            
            # Show results
            self.show_download_results(results)
            
            self.download_btn.config(state=tk.NORMAL)
            self.status_var.set("Download complete")
            
        except Exception as e:
            self.logger.error(f"Error downloading files: {str(e)}")
            self.download_btn.config(state=tk.NORMAL)
            messagebox.showerror("Download Error", f"Failed to download files: {str(e)}")
    
    def download_all(self):
        """Download all media files"""
        filtered_media = self.get_filtered_media()
        if not filtered_media:
            messagebox.showinfo("No Media", "No media files to download")
            return
        
        try:
            self.status_var.set(f"Downloading {len(filtered_media)} files...")
            self.download_all_btn.config(state=tk.DISABLED)
            self.root.update()
            
            # Download files
            device_name = self.device_manager.get_device_name()
            results = self.file_transfer.download_files(filtered_media, 
                                                      self.config.download_dir, device_name)
            
            # Show results
            self.show_download_results(results)
            
            self.download_all_btn.config(state=tk.NORMAL)
            self.status_var.set("Download complete")
            
        except Exception as e:
            self.logger.error(f"Error downloading files: {str(e)}")
            self.download_all_btn.config(state=tk.NORMAL)
            messagebox.showerror("Download Error", f"Failed to download files: {str(e)}")
    
    def show_download_results(self, results):
        """Show download results to user"""
        success = results.get('success', 0)
        failed = results.get('failed', 0)
        skipped = results.get('skipped', 0)
        
        message = f"Download Results:\n"
        message += f"Successfully downloaded: {success}\n"
        message += f"Failed: {failed}\n"
        message += f"Skipped (already exists): {skipped}\n"
        message += f"Total processed: {success + failed + skipped}"
        
        messagebox.showinfo("Download Complete", message)
    
    def clear_media(self):
        """Clear the media display"""
        for widget in self.media_frame.winfo_children():
            widget.destroy()
        
        self.current_media = []
        self.selected_media.clear()
        
        self.download_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        
        self.status_var.set("Media cleared")
    
    def set_filter(self, filter_type):
        """Set the current filter"""
        self.current_filter = filter_type
        self.update_filter_buttons()
        self.display_media(self.current_media)
    
    def update_filter_buttons(self):
        """Update filter button states"""
        # Reset all buttons
        self.filter_all_btn.state(['!selected'])
        self.filter_photos_btn.state(['!selected'])
        self.filter_videos_btn.state(['!selected'])
        
        # Select current filter
        if self.current_filter == "all":
            self.filter_all_btn.state(['selected'])
        elif self.current_filter == "photos":
            self.filter_photos_btn.state(['selected'])
        elif self.current_filter == "videos":
            self.filter_videos_btn.state(['selected'])
    
    def get_filtered_media(self):
        """Get media files based on current filter"""
        if self.current_filter == "all":
            return self.current_media
        elif self.current_filter == "photos":
            return [m for m in self.current_media if m.get('type') == 'photo']
        elif self.current_filter == "videos":
            return [m for m in self.current_media if m.get('type') == 'video']
        return self.current_media
    
    def open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_media_frame_configure(self, event):
        """Handle media frame resize"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def cleanup(self):
        """Clean up resources before exit"""
        try:
            self.logger.info("Cleaning up application resources")
            
            # Unmount device
            if self.current_device:
                self.device_manager.unmount_device()
            
            # Save configuration
            self.config.save()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = IPhoneMediaTransferApp(root)
    
    # Clean up on exit
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    
    root.mainloop()


if __name__ == "__main__":
    main()
