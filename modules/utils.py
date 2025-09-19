"""
Utilities Module
Common utility functions and helpers
"""

import os
import sys
import logging
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.expanduser("~"), ".iphone_transfer_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Default log file
        if not log_file:
            log_file = os.path.join(log_dir, "iphone_transfer.log")
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific loggers
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
        
    except Exception:
        return f"{size_bytes} bytes"

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    try:
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
            
    except Exception:
        return f"{seconds}s"

def get_safe_filename(filename: str) -> str:
    """Get a safe filename by removing/replacing invalid characters"""
    try:
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename
        
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip(' .')
        
        # Ensure filename is not empty
        if not safe_name:
            safe_name = "unnamed_file"
        
        # Limit length
        if len(safe_name) > 200:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:200-len(ext)] + ext
        
        return safe_name
        
    except Exception:
        return "unnamed_file"

def create_unique_filename(base_path: str, filename: str) -> str:
    """Create a unique filename to avoid conflicts"""
    try:
        full_path = os.path.join(base_path, filename)
        
        if not os.path.exists(full_path):
            return full_path
        
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_filename = f"{name}_{counter}{ext}"
            new_path = os.path.join(base_path, new_filename)
            
            if not os.path.exists(new_path):
                return new_path
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 10000:
                import time
                timestamp = int(time.time())
                new_filename = f"{name}_{timestamp}{ext}"
                return os.path.join(base_path, new_filename)
                
    except Exception:
        import time
        timestamp = int(time.time())
        return os.path.join(base_path, f"file_{timestamp}")

def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if necessary"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory {path}: {str(e)}")
        return False

def get_temp_directory() -> str:
    """Get a temporary directory for the application"""
    try:
        temp_dir = os.path.join(tempfile.gettempdir(), "iphone_transfer")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    except Exception:
        return tempfile.gettempdir()

def cleanup_temp_files(temp_dir: str) -> None:
    """Clean up temporary files"""
    try:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        logging.error(f"Error cleaning up temp files: {str(e)}")

def validate_path(path: str) -> bool:
    """Validate if path exists and is accessible"""
    try:
        return os.path.exists(path) and os.access(path, os.R_OK)
    except Exception:
        return False

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        
        return {
            'path': file_path,
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime,
            'is_file': os.path.isfile(file_path),
            'is_dir': os.path.isdir(file_path),
            'extension': os.path.splitext(file_path)[1].lower()
        }
        
    except Exception as e:
        logging.error(f"Error getting file info for {file_path}: {str(e)}")
        return {}

def is_media_file(file_path: str) -> bool:
    """Check if file is a media file"""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        media_extensions = {
            '.jpg', '.jpeg', '.png', '.heic', '.tiff', '.tif',  # Photos
            '.mp4', '.mov', '.m4v', '.3gp', '.avi', '.mkv'      # Videos
        }
        return ext in media_extensions
    except Exception:
        return False

def get_media_type(file_path: str) -> str:
    """Get media type (photo/video) from file extension"""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        photo_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.tiff', '.tif'}
        video_extensions = {'.mp4', '.mov', '.m4v', '.3gp', '.avi', '.mkv'}
        
        if ext in photo_extensions:
            return 'photo'
        elif ext in video_extensions:
            return 'video'
        else:
            return 'unknown'
            
    except Exception:
        return 'unknown'

def calculate_directory_size(directory: str) -> int:
    """Calculate total size of directory"""
    try:
        total_size = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    continue
        return total_size
    except Exception:
        return 0

def get_available_space(path: str) -> int:
    """Get available disk space for a path"""
    try:
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    except Exception:
        return 0

def check_disk_space(path: str, required_space: int) -> bool:
    """Check if there's enough disk space"""
    try:
        available = get_available_space(path)
        return available >= required_space
    except Exception:
        return False

def create_progress_callback(total: int, callback_func: callable) -> callable:
    """Create a progress callback function"""
    def progress_callback(current: int, item: Any = None):
        try:
            progress = (current / total) * 100 if total > 0 else 0
            callback_func(progress, current, total, item)
        except Exception as e:
            logging.error(f"Error in progress callback: {str(e)}")
    
    return progress_callback

def sanitize_string(text: str, max_length: int = 100) -> str:
    """Sanitize string for safe display"""
    try:
        # Remove control characters
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length-3] + "..."
        
        return sanitized
    except Exception:
        return ""

def get_system_info() -> Dict[str, str]:
    """Get system information"""
    try:
        import platform
        import psutil
        
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'cpu_count': str(psutil.cpu_count()),
            'memory_total': format_file_size(psutil.virtual_memory().total),
            'memory_available': format_file_size(psutil.virtual_memory().available)
        }
    except Exception:
        return {
            'platform': 'Unknown',
            'platform_version': 'Unknown',
            'architecture': 'Unknown',
            'python_version': 'Unknown'
        }

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available"""
    dependencies = {
        'PIL': False,
        'psutil': False,
        'idevice_id': False,
        'ifuse': False,
        'ffmpeg': False,
        'ffprobe': False
    }
    
    try:
        # Check Python packages
        import PIL
        dependencies['PIL'] = True
    except ImportError:
        pass
    
    try:
        import psutil
        dependencies['psutil'] = True
    except ImportError:
        pass
    
    # Check system commands
    import subprocess
    
    for cmd in ['idevice_id', 'ifuse', 'ffmpeg', 'ffprobe']:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True, timeout=5)
            dependencies[cmd] = True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return dependencies

def get_missing_dependencies() -> list:
    """Get list of missing dependencies"""
    dependencies = check_dependencies()
    missing = []
    
    required = ['PIL', 'idevice_id', 'ifuse']
    optional = ['psutil', 'ffmpeg', 'ffprobe']
    
    for dep in required:
        if not dependencies.get(dep, False):
            missing.append(dep)
    
    return missing

def install_instructions() -> str:
    """Get installation instructions for missing dependencies"""
    try:
        import platform
        
        if platform.system() == "Linux":
            return """
Installation Instructions for Linux:

Required packages:
sudo apt update
sudo apt install libimobiledevice6 libimobiledevice-utils ifuse
sudo apt install python3-pil python3-psutil

Optional packages (for video thumbnails):
sudo apt install ffmpeg

For HEIC support:
sudo apt install libheif-dev
pip install pillow-heif
"""
        elif platform.system() == "Darwin":  # macOS
            return """
Installation Instructions for macOS:

Required packages:
brew install libimobiledevice
brew install ifuse
pip install pillow psutil

Optional packages (for video thumbnails):
brew install ffmpeg

For HEIC support:
pip install pillow-heif
"""
        else:
            return """
Installation Instructions:

Please install the required dependencies manually:
- libimobiledevice and ifuse for device access
- Python packages: pillow, psutil
- Optional: ffmpeg for video thumbnails
"""
    except Exception:
        return "Please install the required dependencies manually."
