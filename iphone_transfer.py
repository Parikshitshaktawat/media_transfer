import os
import sys
import subprocess
import tempfile
import threading
import time
import shutil
import json
import io
import gc
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
from queue import Queue
from functools import partial

# Suppress PIL DecompressionBombWarning
import warnings
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

class IPhoneMediaDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("iPhone Media Downloader")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize state variables
        self.current_device = None
        self.mount_point = None
        self.media_paths = []
        self.displayed_media = []
        self.selected_media = set()
        self.download_dir = os.path.expanduser("~/Pictures/iPhone_Media")
        self.temp_dir = tempfile.mkdtemp()
        self.downloaded_files = set()
        self.thumbnail_cache = {}
        self.current_media_type = "all"  # Options: "photos", "videos", "all"
        self.is_loading = False
        self.last_download_range = {"start": 1, "end": 0}
        
        # For threading
        self.queue = Queue()
        self.items_per_row = 5  # Default, will be adjusted based on window size
        
        # Ensure download directory exists
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # Create default video icon
        self.video_icon = self._create_video_icon()
        
        # Setup the user interface
        self.create_ui()
        
        # Start queue processor
        self.process_queue()
        
        # Check dependencies
        self.check_dependencies()
        
        # Load download history
        self._load_download_history()
        
        # Detect devices
        self.detect_devices()
        
        # Configure resize event
        self.root.bind("<Configure>", self.on_window_resize)
    
    def on_window_resize(self, event):
        """Handle window resize to adjust grid layout"""
        # Only respond to root window resize events
        if event.widget != self.root:
            return
            
        # Only proceed if we have displayed media
        if not self.displayed_media:
            return
            
        # Recalculate items per row based on window width
        width = event.width
        thumb_size = self.current_thumb_size if hasattr(self, 'current_thumb_size') else "medium"
        
        # Calculate how many items can fit in a row
        if thumb_size == "small":
            new_items_per_row = max(3, width // 120)
        elif thumb_size == "medium":
            new_items_per_row = max(3, width // 160)
        else:  # large
            new_items_per_row = max(2, width // 200)
            
        # If changed, rebuild the grid
        if new_items_per_row != self.items_per_row and not self.is_loading:
            self.items_per_row = new_items_per_row
            self.rebuild_grid()
    
    def rebuild_grid(self):
        """Rebuild the grid layout with current items and new row count"""
        # Remember what's displayed
        current_media = self.displayed_media.copy()
        current_thumb_size = self.current_thumb_size if hasattr(self, 'current_thumb_size') else "medium"
        current_media_type = self.current_media_type  # Get the current media type setting
        
        # Clear the current display
        for widget in self.media_frame.winfo_children():
            widget.destroy()
        
        # Reset the displayed media
        self.displayed_media = []
        
        # Add items back using the new grid layout
        current_row = 0
        current_col = 0
        
        for path in current_media:
            # Determine media type
            media_type = "photo"
            if any(path.lower().endswith(ext) for ext in ['.mp4', '.mov', '.m4v', '.3gp']):
                media_type = "video"
            
            # Skip if it doesn't match the current media type filter
            if current_media_type == "photos" and media_type != "photo":
                continue
            if current_media_type == "videos" and media_type != "video":
                continue
            
            # Create frame for this item
            item_frame = ttk.Frame(self.media_frame, padding=5)
            item_frame.grid(row=current_row, column=current_col, padx=5, pady=5, sticky="nsew")
            
            # Add checkbox for selection
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(
                item_frame, variable=var,
                command=lambda p=path, v=var: self.toggle_selection(p, v.get())
            )
            cb.pack(anchor=tk.W)
            
            # Add thumbnail
            if path in self.thumbnail_cache:
                thumbnail = self.thumbnail_cache[path]
                
                label = ttk.Label(item_frame, image=thumbnail)
                label.image = thumbnail  # Keep reference
                label.pack(pady=2)
            
            # Display filename
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:10] + "..." + filename[-7:]
            
            name_label = ttk.Label(item_frame, text=filename, wraplength=100)
            name_label.pack()
            
            # Add to displayed media list
            self.displayed_media.append(path)
            
            # Update grid position
            current_col += 1
            if current_col >= self.items_per_row:
                current_col = 0
                current_row += 1
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _create_video_icon(self):
        """Create a default video thumbnail icon"""
        # Create a blank image with a play button
        width, height = 100, 100
        image = Image.new('RGB', (width, height), color=(40, 40, 40))
        
        # Try to add a play triangle in the center
        try:
            draw = ImageDraw.Draw(image)
            
            # Draw a play triangle
            center_x, center_y = width // 2, height // 2
            size = 30
            
            # Triangle points for a "play" symbol
            points = [
                (center_x - size // 2, center_y - size),
                (center_x - size // 2, center_y + size),
                (center_x + size, center_y)
            ]
            
            # Draw the triangle in white
            draw.polygon(points, fill=(255, 255, 255))
            
            # Add text "VIDEO" below the play button
            draw.text((center_x - 20, center_y + size + 5), "VIDEO", fill=(255, 255, 255))
        except Exception:
            # If drawing fails, just use the blank image
            pass
            
        return ImageTk.PhotoImage(image)
        
    def create_ui(self):
        """Create the main user interface"""
        # Top control panel
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)
        
        # Device selection
        ttk.Label(control_frame, text="Device:").pack(side=tk.LEFT, padx=(0, 5))
        self.device_combo = ttk.Combobox(control_frame, state="readonly", width=30)
        self.device_combo.pack(side=tk.LEFT, padx=5)
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        # Action buttons
        self.refresh_btn = ttk.Button(control_frame, text="Refresh Devices", 
                                     command=self.detect_devices)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_btn = ttk.Button(control_frame, text="Load Media Range", 
                                  command=self.ask_media_range, state=tk.DISABLED)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_selected_btn = ttk.Button(control_frame, text="Download Selected", 
                                              command=self.download_selected, state=tk.DISABLED)
        self.download_selected_btn.pack(side=tk.LEFT, padx=5)
        
        self.download_all_btn = ttk.Button(control_frame, text="Download All Displayed", 
                                         command=self.download_all_displayed, state=tk.DISABLED)
        self.download_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="Clear Media", 
                                   command=self.clear_media, state=tk.DISABLED)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Second control row with media type selection
        media_type_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        media_type_frame.pack(fill=tk.X)
        
        ttk.Label(media_type_frame, text="Media Type:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Media type radio buttons
        self.media_type_var = tk.StringVar(value="all")
        
        ttk.Radiobutton(media_type_frame, text="All Media", 
                       variable=self.media_type_var, value="all").pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(media_type_frame, text="Photos Only", 
                       variable=self.media_type_var, value="photos").pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(media_type_frame, text="Videos Only", 
                       variable=self.media_type_var, value="videos").pack(side=tk.LEFT, padx=5)
        
        # Thumbnail options
        ttk.Label(media_type_frame, text="Thumbnails:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.thumbnail_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(media_type_frame, text="Show Thumbnails", 
                       variable=self.thumbnail_var).pack(side=tk.LEFT, padx=5)
        
        # Progress info
        self.progress_info = ttk.Label(media_type_frame, 
                                      text="Last download: None")
        self.progress_info.pack(side=tk.RIGHT, padx=5)
        
        # Directory selection
        dir_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        dir_frame.pack(fill=tk.X)
        
        ttk.Label(dir_frame, text="Download Directory:").pack(side=tk.LEFT, padx=(0, 5))
        self.dir_label = ttk.Label(dir_frame, text=self.download_dir)
        self.dir_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(dir_frame, text="Change...", 
                  command=self.change_download_directory).pack(side=tk.LEFT, padx=5)
        
        # Status and progress
        status_frame = ttk.Frame(self.root, padding=(10, 5))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(status_frame, textvariable=self.status_var, 
                                   anchor=tk.W, relief=tk.SUNKEN, padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # Create main canvas for media grid with scrollbars
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame inside canvas for media thumbnails
        self.media_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.media_frame, anchor="nw")
        
        # Configure column weights for even distribution
        for i in range(10):  # Pre-configure some columns
            self.media_frame.columnconfigure(i, weight=1)
        
        # Make sure media_frame expands to fill canvas width
        self.canvas.bind('<Configure>', self._configure_canvas)
        self.media_frame.bind("<Configure>", self._configure_scroll_region)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        # Selection counter
        self.selection_var = tk.StringVar(value="0 items selected")
        ttk.Label(self.root, textvariable=self.selection_var).pack(side=tk.BOTTOM, anchor=tk.W, padx=10)
    
    def process_queue(self):
        """Process UI update queue"""
        try:
            while not self.queue.empty():
                task = self.queue.get(False)
                task()
                self.queue.task_done()
        except Exception as e:
            print(f"Error processing queue: {str(e)}")
        
        # Schedule next check
        self.root.after(100, self.process_queue)
    
    def _configure_canvas(self, event):
        """Adjust the canvas window when canvas size changes"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _configure_scroll_region(self, event):
        """Update the scrollable region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if hasattr(event, 'num') and event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif hasattr(event, 'num') and event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # Scroll down
            self.canvas.yview_scroll(1, "units")
        # For Windows
        elif hasattr(event, 'delta'):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Prevent event propagation
        return "break"
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        missing_deps = []
        
        try:
            subprocess.run(["idevice_id", "-l"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append("libimobiledevice6")
        
        try:
            subprocess.run(["ifuse", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append("ifuse")
        
        if missing_deps:
            messagebox.showerror(
                "Dependencies Missing", 
                f"Required dependencies missing. Please install:\n\n"
                f"sudo apt update\n"
                f"sudo apt install {' '.join(missing_deps)} libimobiledevice-utils"
            )
            sys.exit(1)
    
    def detect_devices(self):
        """Detect connected iPhone devices"""
        self.status_var.set("Detecting devices...")
        self.refresh_btn.config(state=tk.DISABLED)
        self.root.update()
        
        # Run device detection in a separate thread
        threading.Thread(target=self._detect_devices_thread, daemon=True).start()

    def _update_ui_no_devices(self):
        """Update UI when no devices are found"""
        self.device_combo['values'] = ["No devices found"]
        self.device_combo.current(0)
        self.status_var.set("No iPhone devices connected")
        self.device_combo.config(state="readonly")  # Keep it readable
        self.load_btn.config(state=tk.DISABLED)
        self.download_selected_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.NORMAL)
        
        # Show a helpful message
        messagebox.showinfo(
            "No Devices", 
            "No iPhone devices were detected.\n\n"
            "Please connect your iPhone via USB and try clicking 'Refresh Devices'."
        )
    
    def _detect_devices_thread(self):
        """Thread function for device detection with improved handling of no devices"""
        try:
            # Use idevice_id to list connected devices
            result = subprocess.run(["idevice_id", "-l"], 
                                capture_output=True, text=True, check=False)
            
            # Check if the command failed completely (command not found)
            if result.returncode != 0 and "command not found" in result.stderr:
                self.queue.put(lambda: self._handle_device_error("idevice_id command not found. Please check installation."))
                return
                
            # Get device list - even if empty
            devices = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            
            if not devices:
                self.queue.put(lambda: self._update_ui_no_devices())
                return
            
            # Get device info for each connected device
            device_info = []
            for udid in devices:
                try:
                    name_result = subprocess.run(
                        ["ideviceinfo", "-u", udid, "-k", "DeviceName"], 
                        capture_output=True, text=True, check=True
                    )
                    device_name = name_result.stdout.strip()
                    device_info.append(f"{device_name} ({udid})")
                except Exception:
                    device_info.append(f"Unknown Device ({udid})")
            
            self.queue.put(lambda: self._update_device_list(device_info))
            
        except Exception as e:
            self.queue.put(lambda: self._handle_device_error(str(e)))
    
    def _update_device_list(self, device_info):
        """Update the device dropdown list in the UI thread"""
        self.device_combo['values'] = device_info
        self.device_combo.current(0)
        self.status_var.set(f"Found {len(device_info)} device(s)")
        self.refresh_btn.config(state=tk.NORMAL)
        
        # Enable load button if devices found
        if device_info and device_info[0] != "No devices found":
            self.load_btn.config(state=tk.NORMAL)
    
    def _handle_device_error(self, error_msg):
        """Handle device detection errors in the UI thread"""
        self.status_var.set(f"Error detecting devices")
        self.refresh_btn.config(state=tk.NORMAL)
        messagebox.showerror("Error", f"Failed to detect devices: {error_msg}")

    def on_device_selected(self, event):
        """Handle device selection with automatic mounting"""
        selection = self.device_combo.get()
        if "No devices found" in selection:
            return
        
        # Extract UDID from selection
        udid = selection.split("(")[-1].rstrip(")")
        
        self.status_var.set(f"Selected device: {udid}")
        self.current_device = udid
        
        # Enable the load button
        self.load_btn.config(state=tk.NORMAL)
        
        # Auto-mount the device in a background thread
        self.status_var.set(f"Automatically mounting {udid}...")
        threading.Thread(target=self._auto_mount_device, args=(udid,), daemon=True).start()
    

    def _auto_mount_device(self, udid):
        """Automatically mount device when selected"""
        try:
            # Check if already mounted
            if self.mount_point and os.path.exists(self.mount_point):
                self.queue.put(lambda: self.status_var.set(f"Device already mounted at {self.mount_point}"))
                return
                
            # Show a subtle indication that mounting is happening
            self.queue.put(lambda: self.status_var.set("Mounting device... (this may take a moment)"))
            
            # Create mount point
            mount_path = os.path.join(self.temp_dir, f"iphone_mount_{int(time.time())}")
            os.makedirs(mount_path, exist_ok=True)
            
            # Try to mount
            self.current_process = subprocess.Popen(
                ["ifuse", "-u", udid, mount_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # This allows killing the process group
            )
            
            # Wait with timeout
            try:
                stdout, stderr = self.current_process.communicate(timeout=20)
                result = self.current_process.returncode
                self.current_process = None
                
                # Check if mount was successful
                if result == 0 or os.path.ismount(mount_path) or any(os.listdir(mount_path)):
                    # Success
                    self.mount_point = mount_path
                    self.queue.put(lambda: self.status_var.set(f"Device mounted at {mount_path}. Ready to load media."))
                    
                    # Since we're already mounted, let's scan for media too
                    threading.Thread(target=self._preload_media_count, daemon=True).start()
                else:
                    # Mount failed
                    error_msg = stderr.strip() if stderr else "Unknown error"
                    if "No device found" in error_msg:
                        self.queue.put(lambda: self.status_var.set("Device not found. Please ensure it's connected and unlocked."))
                    else:
                        self.queue.put(lambda: self.status_var.set(f"Mount failed: {error_msg}"))
            except subprocess.TimeoutExpired:
                # Timeout - kill the process
                try:
                    import signal
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                except:
                    if self.current_process:
                        self.current_process.terminate()
                
                self.current_process = None
                self.queue.put(lambda: self.status_var.set("Mounting timed out. Device may need to be unlocked."))
                
        except Exception as e:
            self.queue.put(lambda: self.status_var.set(f"Error mounting: {str(e)}"))

    def _preload_media_count(self):
        """Pre-scan media to have counts ready"""
        try:
            if not self.mount_point or not os.path.exists(self.mount_point):
                return
                
            dcim_path = os.path.join(self.mount_point, "DCIM")
            if not os.path.isdir(dcim_path):
                return
                
            # Count files by type
            photo_count = 0
            video_count = 0
            
            for root, dirs, files in os.walk(dcim_path):
                for file in files:
                    file_lower = file.lower()
                    if file_lower.endswith(('.jpg', '.jpeg', '.png', '.heic')):
                        photo_count += 1
                    elif file_lower.endswith(('.mp4', '.mov', '.m4v', '.3gp')):
                        video_count += 1
            
            # Update status with counts
            if photo_count > 0 or video_count > 0:
                self.queue.put(lambda p=photo_count, v=video_count: 
                            self.status_var.set(
                                f"Device ready. Found {p} photos and {v} videos. Click 'Load Media Range' to proceed."
                            ))
        except Exception as e:
            print(f"Error in preload count: {str(e)}")


    def _prepare_device_thread(self, udid):
        """Prepare device by mounting it in the background"""
        try:
            # Update status
            self.queue.put(lambda: self.status_var.set("Preparing device connection..."))
            
            # Try to validate pairing
            try:
                subprocess.run(
                    ["idevicepair", "validate", "-u", udid],
                    capture_output=True, check=True, timeout=5
                )
            except Exception:
                # Just check if device is connected, don't try to pair here
                check_result = subprocess.run(
                    ["idevice_id", "-l"],
                    capture_output=True, text=True, check=True
                )
                if udid not in check_result.stdout:
                    self.queue.put(lambda: self.status_var.set("Device not connected"))
                    return
            
            # Update status to ready
            self.queue.put(lambda: self.status_var.set("Device ready. Select range to load."))
            
        except Exception as e:
            self.queue.put(lambda: self.status_var.set(f"Error: {str(e)}"))

    def limit_concurrent_thumbnails(self, media_paths, start_idx, end_idx, thumb_size):
        """Limit concurrent thumbnail creation to reduce lag"""
        # Only generate thumbnails for visible items first
        visible_count = min(50, end_idx - start_idx)
        
        # First batch - process visible items
        for i in range(start_idx, start_idx + visible_count):
            if self.cancel_loading:
                return []
                
            path, media_type = media_paths[i]
            if path not in self.thumbnail_cache:
                thumbnail = self.create_thumbnail(path, media_type, thumb_size)
                if thumbnail:
                    self.thumbnail_cache[path] = thumbnail
        
        # Then process the rest in background
        if end_idx - start_idx > visible_count and not self.cancel_loading:
            threading.Thread(
                target=self._background_thumbnail_loader,
                args=(media_paths, start_idx + visible_count, end_idx, thumb_size),
                daemon=True
            ).start()
        
        return self.thumbnail_cache

    def _background_thumbnail_loader(self, media_paths, start_idx, end_idx, thumb_size):
        """Load thumbnails in background to prevent UI lag"""
        for i in range(start_idx, end_idx):
            if self.cancel_loading:
                return
                
            path, media_type = media_paths[i]
            if path not in self.thumbnail_cache:
                thumbnail = self.create_thumbnail(path, media_type, thumb_size)
                if thumbnail:
                    self.thumbnail_cache[path] = thumbnail
            
            # Slow down processing to reduce CPU load
            time.sleep(0.01)
    
    def ask_media_range(self):
        """Ask user for media range to load"""
        if not self.current_device:
            messagebox.showwarning("No Device", "Please select a device first")
            return
        
        # Update current media type
        self.current_media_type = self.media_type_var.get()
        
        # First, mount the device if not already mounted
        if not self.mount_point or not os.path.exists(self.mount_point):
            self.status_var.set("Mounting device...")
            self.root.update()
            
            # Mount in a separate thread
            mount_thread = threading.Thread(target=self._mount_device_thread, daemon=True)
            mount_thread.start()
            mount_thread.join()  # Wait for mount to complete
            
            if not self.mount_point:
                return  # Mount failed
        
        # Count total media (if not already done)
        if not self.media_paths:
            self.status_var.set("Scanning media...")
            self.root.update()
            
            # Scan in a separate thread
            scan_thread = threading.Thread(target=self._count_media_thread, daemon=True)
            scan_thread.start()
            scan_thread.join()  # Wait for scan to complete
        
        total_media = len(self.media_paths)
        if total_media == 0:
            messagebox.showinfo("No Media", f"No {self.current_media_type} files found on device")
            return
        
        # Create dialog
        range_dialog = tk.Toplevel(self.root)
        range_dialog.title("Media Range")
        range_dialog.geometry("400x300")  # Make dialog bigger
        range_dialog.transient(self.root)
        range_dialog.grab_set()
        
        # Center dialog
        range_dialog.update_idletasks()
        w, h = range_dialog.winfo_width(), range_dialog.winfo_height()
        x = (range_dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (range_dialog.winfo_screenheight() // 2) - (h // 2)
        range_dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        media_type_str = "media items"
        if self.current_media_type == "photos":
            media_type_str = "photos"
        elif self.current_media_type == "videos":
            media_type_str = "videos"
        
        # Update download history info
        last_download_info = f"Previously downloaded: {len(self.downloaded_files)} items"
        if self.last_download_range["end"] > 0:
            last_download_info += f"\nLast loaded range: {self.last_download_range['start']} - {self.last_download_range['end']}"
            
        ttk.Label(range_dialog, text=f"Found {total_media} {media_type_str}\n{last_download_info}").pack(pady=10)
        
        # Range inputs
        range_frame = ttk.Frame(range_dialog)
        range_frame.pack(pady=10)
        
        ttk.Label(range_frame, text="Start:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Suggest starting after the last downloaded batch
        suggested_start = self.last_download_range["end"] + 1 if self.last_download_range["end"] > 0 else 1
        suggested_start = min(suggested_start, total_media)
        
        start_var = tk.StringVar(value=str(suggested_start))
        start_entry = ttk.Entry(range_frame, textvariable=start_var, width=8)
        start_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(range_frame, text="End:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Suggest a reasonable batch size based on media type
        default_batch = 150 if self.current_media_type == "photos" else 75
        suggested_end = min(suggested_start + default_batch - 1, total_media)
        
        end_var = tk.StringVar(value=str(suggested_end))
        end_entry = ttk.Entry(range_frame, textvariable=end_var, width=8)
        end_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Thumbnail size option
        thumb_frame = ttk.Frame(range_dialog)
        thumb_frame.pack(pady=10)
        
        ttk.Label(thumb_frame, text="Thumbnail Size:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        thumb_size_var = tk.StringVar(value="medium")
        size_combo = ttk.Combobox(thumb_frame, textvariable=thumb_size_var, width=15, state="readonly")
        size_combo['values'] = ["small", "medium", "large"]
        size_combo.current(1)  # Medium by default
        size_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Define what happens when Load is clicked BEFORE creating buttons
        def on_load():
            try:
                start = int(start_var.get())
                end = int(end_var.get())
                
                if start < 1:
                    messagebox.showwarning("Invalid Range", "Start must be at least 1")
                    return
                
                if end > total_media:
                    messagebox.showwarning("Invalid Range", 
                                        f"End cannot exceed total media ({total_media})")
                    return
                
                if start > end:
                    messagebox.showwarning("Invalid Range", "Start must be less than end")
                    return
                
                # Check if range is too large with thumbnails
                batch_size = end - start + 1
                show_thumbnails = self.thumbnail_var.get()
                thumb_size = thumb_size_var.get()
                
                # If batch size is very large and thumbnails are enabled, warn user
                if show_thumbnails and batch_size > 300:
                    warning = messagebox.askyesno(
                        "Performance Warning",
                        f"Loading {batch_size} items with thumbnails may cause slow performance.\n\n"
                        f"Do you want to continue with thumbnails enabled?",
                        icon=messagebox.WARNING
                    )
                    if not warning:
                        return
                
                # Save the range for next time
                self.last_download_range = {"start": start, "end": end}
                
                range_dialog.destroy()
                
                # Update the progress info
                self.progress_info.config(text=f"Current range: {start}-{end}")
                
                # Load the media in a background thread
                threading.Thread(
                    target=self.load_media_thread,
                    args=(start-1, end, thumb_size),
                    daemon=True
                ).start()
                
            except ValueError:
                messagebox.showwarning("Invalid Input", "Please enter valid numbers")
        
        # Button frame
        button_frame = ttk.Frame(range_dialog)
        button_frame.pack(pady=15)
        
        # Create the buttons with bigger size
        load_btn = ttk.Button(
            button_frame, 
            text="Load", 
            command=on_load,
            width=15
        )
        load_btn.pack(side=tk.LEFT, padx=20, pady=10)
        
        cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=range_dialog.destroy,
            width=15
        )
        cancel_btn.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Set focus to first entry
        start_entry.focus_set()

    def show_loading_dialog(self, message="Loading..."):
        """Show a modal loading dialog with cancel button"""
        self.loading_dialog = tk.Toplevel(self.root)
        self.loading_dialog.title("Loading")
        self.loading_dialog.transient(self.root)
        self.loading_dialog.grab_set()
        
        # Prevent closing with X button
        self.loading_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Make it a fixed size
        self.loading_dialog.geometry("300x150")
        self.loading_dialog.resizable(False, False)
        
        # Center the dialog
        self.loading_dialog.update_idletasks()
        w, h = self.loading_dialog.winfo_width(), self.loading_dialog.winfo_height()
        x = (self.loading_dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.loading_dialog.winfo_screenheight() // 2) - (h // 2)
        self.loading_dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        # Message
        self.loading_message = tk.StringVar(value=message)
        message_label = ttk.Label(
            self.loading_dialog, 
            textvariable=self.loading_message,
            font=("Arial", 12)
        )
        message_label.pack(pady=(20, 10))
        
        # Progress bar
        progress = ttk.Progressbar(self.loading_dialog, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start()
        
        # Cancel button
        self.cancel_loading = False
        cancel_btn = ttk.Button(
            self.loading_dialog, 
            text="Cancel", 
            command=self.cancel_loading_process,
            width=15
        )
        cancel_btn.pack(pady=15)
        
        # Force update
        self.loading_dialog.update()

    def cancel_loading_process(self):
        """Cancel the current loading process with proper cleanup"""
        self.cancel_loading = True
        self.loading_message.set("Cancelling...")
        
        # Terminate any active subprocess
        if hasattr(self, 'current_process') and self.current_process:
            try:
                # On Unix/Linux
                import signal
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
            except (AttributeError, ProcessLookupError, ImportError):
                try:
                    # Generic attempt
                    self.current_process.terminate()
                except:
                    pass
        
        # Close loading dialog after a short delay
        self.root.after(1000, self.close_loading_dialog)
        
        # Reset UI state
        self.root.after(1200, lambda: self.disable_all_buttons(False))
        self.root.after(1200, lambda: self.status_var.set("Operation cancelled"))
        
    def close_loading_dialog(self):
        """Close the loading dialog safely"""
        try:
            if hasattr(self, 'loading_dialog') and self.loading_dialog:
                self.loading_dialog.destroy()
                self.loading_dialog = None
        except:
            pass  # Handle any exception if dialog was already closed
        
        # Reset state variables
        self.cancel_loading = False
        if hasattr(self, 'current_process') and self.current_process:
            try:
                self.current_process.terminate()
            except:
                pass
            self.current_process = None
    
    def _mount_device_thread(self):
        """Mount the device in a background thread"""
        try:
            # Show loading dialog
            self.queue.put(lambda: self.show_loading_dialog("Mounting device..."))
            
            # Try direct mounting first without explicit pairing
            try:
                # Create mount point
                mount_path = os.path.join(self.temp_dir, f"iphone_mount_{int(time.time())}")
                os.makedirs(mount_path, exist_ok=True)
                
                # Set timeout longer for mounting
                self.queue.put(lambda: self.loading_message.set("Mounting iPhone... (This may take a few moments)"))
                
                # Try mounting directly with a longer timeout
                result = subprocess.run(
                    ["ifuse", "-u", self.current_device, mount_path],
                    capture_output=True, text=True, timeout=30
                )
                
                # Verify mount worked
                if os.path.ismount(mount_path) or any(os.listdir(mount_path)):
                    self.mount_point = mount_path
                    self.queue.put(lambda: self.status_var.set(f"Device mounted at {mount_path}"))
                    self.queue.put(self.close_loading_dialog)
                    return
                else:
                    # If direct mount failed, show more detailed message
                    self.queue.put(lambda: self.loading_message.set("Device not trusted. Please unlock your iPhone and trust this computer."))
                    time.sleep(2)  # Give user time to read
            except Exception as e:
                print(f"Direct mount failed: {str(e)}")
            
            # If we get here, direct mounting failed - try to restart the USB connection
            self.queue.put(lambda: self.loading_message.set("Reconnecting to iPhone..."))
            
            # Suggest user action
            self.queue.put(lambda: messagebox.showinfo(
                "iPhone Connection Issue",
                "Please try these steps:\n\n"
                "1. Unlock your iPhone\n"
                "2. Tap 'Trust' if prompted\n"
                "3. If no prompt appears, try disconnecting and reconnecting the USB cable\n"
                "4. Click OK after these steps"
            ))
            
            # Try one more time after user action
            try:
                self.queue.put(lambda: self.loading_message.set("Trying to mount again..."))
                
                                # Try mounting directly with Popen for better control
                self.current_process = subprocess.Popen(
                    ["ifuse", "-u", self.current_device, mount_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid  # This allows killing the process group
                )

                # Wait for completion with timeout
                try:
                    stdout, stderr = self.current_process.communicate(timeout=30)
                    result = self.current_process.returncode
                    self.current_process = None
                    
                    # Check result
                    if result == 0 and (os.path.ismount(mount_path) or any(os.listdir(mount_path))):
                        # Success
                        self.mount_point = mount_path
                        self.queue.put(lambda: self.status_var.set(f"Device mounted at {mount_path}"))
                        self.queue.put(self.close_loading_dialog)
                        return
                    else:
                        # Failed
                        error_msg = stderr if stderr else "Unknown mounting error"
                        self.queue.put(lambda: self.loading_message.set("Device not trusted. Please unlock your iPhone and trust this computer."))
                        time.sleep(2)  # Give user time to read
                except subprocess.TimeoutExpired:
                    # Timeout - kill the process
                    try:
                        import signal
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                    except:
                        self.current_process.terminate()
                    
                    self.current_process = None
                    print("Mounting timed out - device may be busy or not responding")
            except Exception as e:
                raise Exception(f"Mount failed: {str(e)}")
                
        except Exception as e:
            self.queue.put(self.close_loading_dialog)
            self.queue.put(lambda e=e: messagebox.showerror(
                "Mount Error",
                f"Failed to mount device. Please ensure your device is unlocked and trusted.\n\n"
                f"Error: {str(e)}"
            ))
            self.queue.put(lambda: self.disable_all_buttons(False))
    
    def _count_media_thread(self):
        """Count media files in a background thread"""
        try:
            # Check for DCIM directory
            dcim_path = os.path.join(self.mount_point, "DCIM")
            if not os.path.isdir(dcim_path):
                self.queue.put(lambda: messagebox.showerror(
                    "Error", 
                    "No DCIM directory found on device"
                ))
                return
            
            media_type = self.current_media_type
            
            # Find all media files in all subdirectories
            media_paths = []
            total_found = 0
            
            for root, dirs, files in os.walk(dcim_path):
                for file in files:
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    # Update progress occasionally
                    if total_found % 100 == 0:
                        self.queue.put(lambda count=total_found: 
                                    self.status_var.set(f"Scanning media... Found {count} files"))
                    
                    # Photos
                    if media_type in ["photos", "all"] and file_lower.endswith(('.jpg', '.jpeg', '.png', '.heic')):
                        media_paths.append((file_path, "photo"))
                        total_found += 1
                    
                    # Videos
                    if media_type in ["videos", "all"] and file_lower.endswith(('.mp4', '.mov', '.m4v', '.3gp')):
                        media_paths.append((file_path, "video"))
                        total_found += 1
            
            # Sort paths (usually corresponds to date taken)
            media_paths.sort(key=lambda x: x[0])
            
            self.media_paths = media_paths
            
            media_type_str = "media files"
            if media_type == "photos":
                media_type_str = "photos"
            elif media_type == "videos":
                media_type_str = "videos"
                
            self.queue.put(lambda: self.status_var.set(f"Found {len(media_paths)} {media_type_str} on device"))
        
        except Exception as e:
            self.queue.put(lambda: self.status_var.set(f"Error scanning media"))
            self.queue.put(lambda: messagebox.showerror("Error", f"Failed to scan media: {str(e)}"))

    # def create_thumbnail(self, media_path, media_type, size="small"):
    #     """Create a thumbnail with better memory optimization"""
    #     try:
    #         # Determine thumbnail size
    #         if size == "small":
    #             thumb_size = (80, 80)
    #         elif size == "medium":
    #             thumb_size = (120, 120)
    #         else:  # large
    #             thumb_size = (160, 160)
                
    #         if media_type == "photo":
    #             # Use memory-efficient approach 
    #             with Image.open(media_path) as image:
    #                 # Create small image first
    #                 image.thumbnail((thumb_size[0]*2, thumb_size[1]*2))
                    
    #                 # Convert to RGB if needed
    #                 if image.mode != 'RGB':
    #                     image = image.convert('RGB')
                    
    #                 # Further reduce to final size
    #                 image.thumbnail(thumb_size)
                    
    #                 # Force garbage collection to prevent memory leaks
    #                 gc.collect()
                    
    #                 # Create PhotoImage
    #                 return ImageTk.PhotoImage(image)
    #         else:  # video
    #             return self.video_icon
            
    #     except Exception as e:
    #         print(f"Error creating thumbnail: {str(e)}")
    #         return None
    def create_thumbnail(self, media_path, media_type, size="small"):
        """Create a memory-efficient thumbnail with proper cleanup"""
        try:
            # Determine thumbnail size
            if size == "small":
                thumb_size = (60, 60)  # Smaller size to use less memory
            elif size == "medium":
                thumb_size = (100, 100)
            else:  # large
                thumb_size = (140, 140)
                
            if media_type == "photo":
                # More aggressive memory management
                img = None
                photo = None
                
                try:
                    # Open with a max size limit upfront
                    with open(media_path, 'rb') as f:
                        img_data = f.read(1024*1024)  # Only read up to 1MB
                    
                    img_stream = io.BytesIO(img_data)
                    img = Image.open(img_stream)
                    
                    # Create a very small image first
                    img.thumbnail((thumb_size[0], thumb_size[1]))
                    
                    # Convert to RGB and mode optimization
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Force a copy to ensure original image is released
                    img_copy = img.copy()
                    img.close()
                    img = img_copy
                    
                    # Create PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Force cleanup
                    img.close()
                    img = None
                    gc.collect()
                    
                    return photo
                except Exception as e:
                    print(f"Thumbnail error: {str(e)}")
                    # Clean up on error
                    if img:
                        try:
                            img.close()
                        except:
                            pass
                    return None
            else:  # video
                return self.video_icon
            
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
            return None
        
    def disable_all_buttons(self, disabled=True):
        """Disable or enable all buttons to prevent interference"""
        state = tk.DISABLED if disabled else tk.NORMAL
        
        # Buttons that should always be disabled when no media is loaded
        media_dependent_buttons = [self.download_selected_btn, 
                                self.download_all_btn, 
                                self.clear_btn]
        
        # Buttons that should be disabled during any loading operation
        all_buttons = [self.refresh_btn, self.load_btn, 
                    self.device_combo, self.select_dir_btn] + media_dependent_buttons
        
        for button in all_buttons:
            button.config(state=state)
        
        # If re-enabling, make sure media-dependent buttons are still disabled if no media
        if not disabled and not self.displayed_media:
            for button in media_dependent_buttons:
                button.config(state=tk.DISABLED)

    def load_media_thread(self, start_idx, end_idx, thumb_size="medium"):
        """Load media items with active memory monitoring and protection"""
        try:
            print("DEBUG: Starting load_media_thread")
            self.is_loading = True
            self.cancel_loading = False
            
            # Show loading dialog
            self.queue.put(lambda: self.show_loading_dialog("Preparing to load media..."))
            
            # Store thumbnail size for later use
            self.current_thumb_size = thumb_size
            
            # Clear previous media in the UI thread
            self.queue.put(self.clear_media)
            
            # Exit if canceled
            if self.cancel_loading:
                self.queue.put(self.close_loading_dialog)
                self.is_loading = False
                return
            
            # Validate range
            if start_idx < 0:
                start_idx = 0
            if end_idx > len(self.media_paths):
                end_idx = len(self.media_paths)
            
            # Get UI preferences
            show_thumbnails = self.thumbnail_var.get()
            
            # Create a temporary list to track items
            temp_media_list = []
            
            # Calculate grid layout
            width = self.root.winfo_width()
            if thumb_size == "small":
                items_per_row = max(3, width // 120)
            elif thumb_size == "medium":
                items_per_row = max(3, width // 160)
            else:  # large
                items_per_row = max(2, width // 200)
            
            self.items_per_row = items_per_row
            
            # Track grid position
            current_row = 0
            current_col = 0
            
            # Use a more efficient batching approach
            # Process items in chunks of 20, but wait for UI updates
            max_batch_size = 20
            memory_check_interval = 5
            
            # Track memory usage
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_limit = min(start_memory * 3, start_memory + 500)  # Limit to 3x start or +500MB
            
            self.queue.put(lambda: self.loading_message.set(f"Loading items {start_idx+1} to {end_idx}..."))
            
            # Close the initial loading dialog
            self.queue.put(self.close_loading_dialog)
            
            # Process items in small batches
            for batch_start in range(start_idx, end_idx, max_batch_size):
                if self.cancel_loading:
                    break
                    
                batch_end = min(batch_start + max_batch_size, end_idx)
                batch_items = []
                
                # Progress update
                progress = ((batch_start - start_idx) / (end_idx - start_idx)) * 100
                self.queue.put(lambda p=progress: self.progress_var.set(p))
                self.queue.put(lambda s=batch_start+1, e=batch_end: 
                            self.status_var.set(f"Loading items {s} to {e} (of {end_idx})..."))
                
                # Check memory every few items
                if batch_start % (max_batch_size * 3) == 0:
                    current_memory = process.memory_info().rss / (1024 * 1024)  # MB
                    print(f"Memory usage: {current_memory:.1f}MB / {memory_limit:.1f}MB limit")
                    
                    # If we're approaching the memory limit, GC and wait
                    if current_memory > memory_limit * 0.8:
                        print("Memory usage high, performing cleanup")
                        self.thumbnail_cache.clear()
                        gc.collect()
                        time.sleep(0.5)  # Allow system to reclaim memory
                    
                    # If still too high, offer to continue with no thumbnails
                    current_memory = process.memory_info().rss / (1024 * 1024)
                    if current_memory > memory_limit:
                        print("Memory usage exceeded limit, reducing thumbnails")
                        self.queue.put(lambda: messagebox.showwarning(
                            "Memory Warning", 
                            "Memory usage is high. Continuing with reduced thumbnails."
                        ))
                        show_thumbnails = False
                        self.thumbnail_cache.clear()
                        gc.collect()
                
                # Process this batch
                for i in range(batch_start, batch_end):
                    path, media_type = self.media_paths[i]
                    
                    # Create thumbnail if enabled and not too memory intensive
                    thumbnail = None
                    if show_thumbnails:
                        if path in self.thumbnail_cache:
                            thumbnail = self.thumbnail_cache[path]
                        else:
                            thumbnail = self.create_thumbnail(path, media_type, thumb_size)
                            # Only cache if we haven't cached too many
                            if thumbnail and len(self.thumbnail_cache) < 300:
                                self.thumbnail_cache[path] = thumbnail
                    
                    # Add to batch
                    batch_items.append((path, media_type, thumbnail, current_row, current_col))
                    temp_media_list.append(path)
                    
                    # Update grid position
                    current_col += 1
                    if current_col >= items_per_row:
                        current_col = 0
                        current_row += 1
                
                # Update UI with batch
                self.queue.put(lambda items=batch_items: self._add_media_batch(items))
                
                # Short pause to let UI update and process events
                time.sleep(0.05)
            
            # Set the displayed media list - critical fix!
            self.queue.put(lambda items=temp_media_list: setattr(self, 'displayed_media', items.copy()))
            
            # Verify that we succeeded
            print(f"DEBUG: Loaded {len(temp_media_list)} items into displayed_media")
            
            # Enable buttons
            self.queue.put(lambda: self.download_selected_btn.config(state=tk.NORMAL))
            self.queue.put(lambda: self.download_all_btn.config(state=tk.NORMAL))
            self.queue.put(lambda: self.clear_btn.config(state=tk.NORMAL))
            
            # Final UI update
            self.queue.put(lambda: self.progress_var.set(100))
            self.queue.put(lambda count=len(temp_media_list): 
                        self.status_var.set(f"Loaded {count} items from {start_idx+1} to {end_idx}"))
            
        except Exception as e:
            print(f"Error in load_media_thread: {str(e)}")
            self.queue.put(lambda: self.status_var.set(f"Error loading media: {str(e)}"))
        finally:
            # Always ensure we finish properly
            self.is_loading = False
            if hasattr(self, 'loading_dialog') and self.loading_dialog:
                self.queue.put(self.close_loading_dialog)

    def check_memory_usage(self):
        """Monitor memory usage and perform emergency cleanup if needed"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # If memory usage exceeds 1GB, take action
            if memory_mb > 1000:
                print(f"EMERGENCY: Memory usage at {memory_mb:.1f}MB - performing cleanup")
                self.thumbnail_cache.clear()
                gc.collect()
                
                # If still critical after cleanup
                memory_mb = process.memory_info().rss / (1024 * 1024)
                if memory_mb > 1200:
                    print("CRITICAL: Memory usage still high after cleanup")
                    # Force more aggressive cleanup
                    self.clear_media()
                    gc.collect()
                    
                    self.queue.put(lambda: messagebox.showwarning(
                        "Memory Warning",
                        "Memory usage critically high. Media display has been cleared.\n\n"
                        "Please try working with smaller batches of media."
                    ))
        except ImportError:
            # psutil not available
            pass

    def _add_media_batch(self, batch_items):
        """Add a batch of media items to the grid"""
        print(f"DEBUG: Adding batch of {len(batch_items)} items")
        for path, media_type, thumbnail, row, col in batch_items:
            # Create frame for this item
            item_frame = ttk.Frame(self.media_frame, padding=5)
            item_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Add checkbox for selection
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(
                item_frame, variable=var,
                command=lambda p=path, v=var: self.toggle_selection(p, v.get())
            )
            cb.pack(anchor=tk.W)
            
            # Add thumbnail if available
            if thumbnail:
                label = ttk.Label(item_frame, image=thumbnail)
                label.image = thumbnail  # Keep reference
                label.pack(pady=2)
            
            # Display filename
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:10] + "..." + filename[-7:]
            
            name_label = ttk.Label(item_frame, text=filename, wraplength=100)
            name_label.pack()
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def toggle_selection(self, path, is_selected):
        """Toggle selection state of a media item"""
        if is_selected:
            self.selected_media.add(path)
        else:
            if path in self.selected_media:
                self.selected_media.remove(path)
        
        # Update selection counter
        self.selection_var.set(f"{len(self.selected_media)} items selected")

    def download_selected(self):
        """Download selected media"""
        if not self.selected_media:
            messagebox.showinfo("No Selection", "No items selected for download")
            return
        
        # Confirm download
        confirmation = messagebox.askyesno(
            "Confirm Download", 
            f"Download {len(self.selected_media)} selected items to\n{self.download_dir}?"
        )
        
        if confirmation:
            threading.Thread(target=self._download_media, 
                            args=(list(self.selected_media),), daemon=True).start()

    def download_all_displayed(self):
        """Download all displayed media"""
        print(f"DEBUG: displayed_media count: {len(self.displayed_media)}")
        if not self.displayed_media:
            messagebox.showinfo("No Media", "No items displayed to download")
            return
        
        # Confirm download
        confirmation = messagebox.askyesno(
            "Confirm Download", 
            f"Download all {len(self.displayed_media)} displayed items to\n{self.download_dir}?"
        )
        
        if confirmation:
            threading.Thread(target=self._download_media, 
                            args=(self.displayed_media,), daemon=True).start()

    # def _download_media(self, media_list):
    #     """Worker thread for downloading media"""
    #     print(f"Download thread started for {len(media_list)} items")
    #     total = len(media_list)
    #     error_count = 0
        
    #     # Disable buttons during download
    #     self.queue.put(lambda: self.download_selected_btn.config(state=tk.DISABLED))
    #     self.queue.put(lambda: self.download_all_btn.config(state=tk.DISABLED))
        
    #     # Create directory with timestamp
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     download_dir = os.path.join(self.download_dir, f"iPhone_Media_{timestamp}")
        
    #     try:
    #         os.makedirs(download_dir, exist_ok=True)
    #         print(f"Created download directory: {download_dir}")
    #     except Exception as e:
    #         print(f"Failed to create directory: {str(e)}")
    #         self.queue.put(lambda e=e: messagebox.showerror(
    #             "Directory Error", f"Could not create directory: {str(e)}"
    #         ))
    #         self.queue.put(lambda: self.download_selected_btn.config(state=tk.NORMAL))
    #         self.queue.put(lambda: self.download_all_btn.config(state=tk.NORMAL))
    #         return
        
    #     # Download each media item
    #     success_count = 0
    #     skipped_count = 0
        
    #     for i, media_path in enumerate(media_list):
    #         # Skip already downloaded files if restarting
    #         if media_path in self.downloaded_files:
    #             skipped_count += 1
    #             self.queue.put(lambda i=i, total=total, f=os.path.basename(media_path): 
    #                     self.status_var.set(f"Skipping already downloaded {i+1}/{total}: {f}"))
    #             continue
            
    #         # Update status
    #         self.queue.put(lambda i=i, total=total, f=os.path.basename(media_path): 
    #                     self.status_var.set(f"Downloading {i+1}/{total}: {f}"))
    #         self.queue.put(lambda i=i, total=total: 
    #                     self.progress_var.set((i / total) * 100))
            
    #         try:
    #             filename = os.path.basename(media_path)
    #             dest_path = os.path.join(download_dir, filename)

    #             if not os.path.exists(media_path):
    #                 print(f"Source file not found: {media_path}")
                    
    #                 # Try to find the file with an updated mount point
    #                 if hasattr(self, 'mount_point') and self.mount_point:
    #                     # Try to extract the relative path
    #                     for old_mount in [self.temp_dir, '/tmp', '/mnt']:
    #                         if old_mount in media_path:
    #                             rel_path = media_path[media_path.find('DCIM'):]
    #                             new_path = os.path.join(self.mount_point, rel_path)
    #                             if os.path.exists(new_path):
    #                                 print(f"Found file at updated path: {new_path}")
    #                                 media_path = new_path
    #                                 break
                    
    #                 # If still doesn't exist, report error
    #                 if not os.path.exists(media_path):
    #                     print(f"File not found, even after attempting path correction: {media_path}")
    #                     error_count += 1
    #                     continue
                
    #             # Copy the file
    #             print(f"Copying {media_path} to {dest_path}")
                
    #             # Copy the file
    #             shutil.copy2(media_path, dest_path)
                
    #             if os.path.exists(dest_path):
    #                 # Add to downloaded files set
    #                 self.downloaded_files.add(media_path)
    #                 success_count += 1
    #                 print(f"Successfully copied file {i+1}/{total}")
    #             else:
    #                 print(f"Copy failed - destination file not found: {dest_path}")
    #                 error_count += 1
                
    #         except Exception as e:
    #             print(f"Error downloading {os.path.basename(media_path)}: {str(e)}")
        
    #     # Save download history
    #     self._save_download_history()
        
    #     # Update status
    #     self.queue.put(lambda: self.progress_var.set(100))
    #     self.queue.put(lambda success=success_count, skipped=skipped_count, total=total, dir=download_dir: 
    #                 self.status_var.set(
    #                     f"Downloaded {success} items, skipped {skipped} (already downloaded) of {total} total. "
    #                     f"Saved to {dir}"
    #                 ))
        
    #     # Re-enable buttons
    #     self.queue.put(lambda: self.download_selected_btn.config(state=tk.NORMAL))
    #     self.queue.put(lambda: self.download_all_btn.config(state=tk.NORMAL))
        
    #     # Update the progress info
    #     range_info = f"Range {self.last_download_range['start']}-{self.last_download_range['end']}"
    #     download_info = f"Downloaded: {len(self.downloaded_files)} items"
    #     self.queue.put(lambda: self.progress_info.config(text=f"{range_info}, {download_info}"))
        
    #     # Show message
    #     message_text = f"Download complete:\n• Successfully downloaded: {success_count}\n• Skipped (already downloaded): {skipped_count}\n• Failed: {error_count}\n• Total processed: {total}\n\nSaved to:\n{download_dir}"
    
    #     self.queue.put(lambda msg=message_text: 
    #                 messagebox.showinfo("Download Complete", msg))
        
    #     # Ask to clear memory if needed
    #     if success_count > 100:
    #         self.queue.put(lambda: messagebox.showinfo(
    #             "Memory Management",
    #             "To maintain good performance, consider clearing the media list\n"
    #             "before loading a new range of items."
    #         ))
    def _download_media(self, media_list):
        """Download media with efficient memory usage"""
        print(f"Download thread started with {len(media_list)} items")
        total = len(media_list)
        error_count = 0
        
        # Disable buttons during download
        self.queue.put(lambda: self.download_selected_btn.config(state=tk.DISABLED))
        self.queue.put(lambda: self.download_all_btn.config(state=tk.DISABLED))
        
        # Create directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_dir = os.path.join(self.download_dir, f"iPhone_Media_{timestamp}")
        
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception as e:
            self.queue.put(lambda: messagebox.showerror(
                "Directory Error", f"Could not create directory: {str(e)}"
            ))
            self.queue.put(lambda: self.download_selected_btn.config(state=tk.NORMAL))
            self.queue.put(lambda: self.download_all_btn.config(state=tk.NORMAL))
            return
        
        # Download in smaller batches for better memory management
        success_count = 0
        skipped_count = 0
        
        # Process in smaller batches
        batch_size = 50
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            
            # Check memory
            self.check_memory_usage()
            
            for i in range(batch_start, batch_end):
                media_path = media_list[i]
                
                # Skip already downloaded
                if media_path in self.downloaded_files:
                    skipped_count += 1
                    continue
                    
                # Update status
                self.queue.put(lambda i=i, total=total, f=os.path.basename(media_path): 
                            self.status_var.set(f"Downloading {i+1}/{total}: {f}"))
                self.queue.put(lambda i=i, total=total: self.progress_var.set((i/total)*100))
                
                # Download the file with error handling
                try:
                    filename = os.path.basename(media_path)
                    dest_path = os.path.join(download_dir, filename)
                    
                    # Handle source path updates if needed
                    if not os.path.exists(media_path):
                        # Try to adjust path
                        dcim_index = media_path.find('DCIM')
                        if dcim_index >= 0 and hasattr(self, 'mount_point'):
                            rel_path = media_path[dcim_index:]
                            new_path = os.path.join(self.mount_point, rel_path)
                            if os.path.exists(new_path):
                                media_path = new_path
                            else:
                                error_count += 1
                                continue
                        else:
                            error_count += 1
                            continue
                    
                    # Copy with limited buffer size
                    with open(media_path, 'rb') as src_file:
                        with open(dest_path, 'wb') as dst_file:
                            buffer_size = 1024 * 1024  # 1MB chunks
                            while True:
                                buffer = src_file.read(buffer_size)
                                if not buffer:
                                    break
                                dst_file.write(buffer)
                    
                    # Success
                    self.downloaded_files.add(media_path)
                    success_count += 1
                    
                except Exception as e:
                    print(f"Error downloading {os.path.basename(media_path)}: {str(e)}")
                    error_count += 1
            
            # Save progress after each batch
            self._save_download_history()
        
        # Final status updates
        self.queue.put(lambda: self.progress_var.set(100))
        self.queue.put(lambda s=success_count, skip=skipped_count, err=error_count, t=total: 
                    self.status_var.set(
                        f"Downloaded {s} items, skipped {skip}, failed {err} of {t} total"
                    ))
        
        # Re-enable buttons
        self.queue.put(lambda: self.download_selected_btn.config(state=tk.NORMAL))
        self.queue.put(lambda: self.download_all_btn.config(state=tk.NORMAL))
        
        # Update progress info
        self.queue.put(lambda: self.progress_info.config(
            text=f"Range {self.last_download_range['start']}-{self.last_download_range['end']}, "
                f"Downloaded: {len(self.downloaded_files)} items"
        ))
        
        # Show completion message
        self.queue.put(lambda s=success_count, skip=skipped_count, err=error_count, t=total, d=download_dir: 
                    messagebox.showinfo(
                        "Download Complete", 
                        f"Download results:\n"
                        f"• Successfully downloaded: {s}\n"
                        f"• Already downloaded (skipped): {skip}\n"
                        f"• Failed: {err}\n"
                        f"• Total processed: {t}\n\n"
                        f"Saved to:\n{d}"
                    ))

    def detect_devices(self):
        """Detect connected iPhone devices with better error handling"""
        self.status_var.set("Detecting devices...")
        self.refresh_btn.config(state=tk.DISABLED)
        self.root.update()
        
        # Run device detection in a separate thread
        threading.Thread(target=self._detect_devices_thread, daemon=True).start()
        

    def emergency_cleanup(self):
        """Emergency cleanup when memory gets too high"""
        # Clear all thumbnails and displayed content
        self.thumbnail_cache.clear()
        self.displayed_media.clear()
        self.clear_media()
        
        # Force garbage collection multiple times
        for _ in range(5):
            gc.collect()
            time.sleep(0.1)
        
        # Save any pending data
        self._save_download_history()
        
        # Emergency unmount
        if self.mount_point and os.path.exists(self.mount_point):
            try:
                subprocess.run(["fusermount", "-uz", self.mount_point], 
                            capture_output=True, check=False)
            except:
                pass

    def _save_download_history(self):
        """Save downloaded file history"""
        try:
            config = {
                'download_dir': self.download_dir,
                'downloaded_files': list(self.downloaded_files),
                'last_range': self.last_download_range
            }
            
            config_file = os.path.join(os.path.expanduser("~"), ".iphone_downloader_history.json")
            with open(config_file, 'w') as f:
                json.dump(config, f)
                
        except Exception as e:
            print(f"Error saving download history: {str(e)}")

    def _load_download_history(self):
        """Load download history if available"""
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".iphone_downloader_history.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                if 'download_dir' in config and os.path.exists(config['download_dir']):
                    self.download_dir = config['download_dir']
                    self.dir_label.config(text=self.download_dir)
                
                if 'downloaded_files' in config:
                    self.downloaded_files = set(config['downloaded_files'])
                
                if 'last_range' in config:
                    self.last_download_range = config['last_range']
                    
                # Update progress info if we have history
                if len(self.downloaded_files) > 0:
                    range_info = ""
                    if self.last_download_range['end'] > 0:
                        range_info = f"Last range: {self.last_download_range['start']}-{self.last_download_range['end']}"
                    
                    self.progress_info.config(text=f"Previously downloaded: {len(self.downloaded_files)} items. {range_info}")
                    
                return True
        except Exception as e:
            print(f"Error loading download history: {str(e)}")
        
        return False

    def clear_media(self):
        """Clear the media grid and free memory"""
        # Clear all widgets from the media frame
        for widget in self.media_frame.winfo_children():
            widget.destroy()
        
        # Clear displayed media and selections
        self.displayed_media.clear()
        self.selected_media.clear()
        
        # Update selection counter
        self.selection_var.set("0 items selected")
        
        # Disable download buttons
        self.download_selected_btn.config(state=tk.DISABLED)
        self.download_all_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        
        # Clear thumbnail cache to free memory
        self.thumbnail_cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        self.status_var.set("Media cleared")

    def change_download_directory(self):
        """Change the download directory"""
        directory = filedialog.askdirectory(
            initialdir=self.download_dir,
            title="Select Download Directory"
        )
        
        if directory:
            self.download_dir = directory
            self.dir_label.config(text=self.download_dir)

    def cleanup(self):
        """Clean up resources before exiting"""
        # Save download history
        self._save_download_history()
        
        # Unmount device
        if self.mount_point and os.path.exists(self.mount_point):
            try:
                subprocess.run(
                    ["fusermount", "-u", self.mount_point],
                    capture_output=True, check=False
                )
            except Exception:
                pass
        
        # Clean up thumbnail cache
        self.thumbnail_cache.clear()
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            try:
                for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                    for dir in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir))
                        except:
                            pass
                try:
                    os.rmdir(self.temp_dir)
                except:
                    pass
            except:
                pass

def main():
    root = tk.Tk()
    app = IPhoneMediaDownloader(root)
    
    # Clean up on exit
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    
    root.mainloop()

if __name__ == "__main__":
    main()