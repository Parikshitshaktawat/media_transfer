"""
Device Manager Module
Handles iPhone device detection, mounting, and unmounting
"""

import os
import subprocess
import tempfile
import time
import logging
from typing import List, Dict, Optional

class DeviceManager:
    """Manages iPhone device connections and mounting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mount_point = None
        self.current_device = None
        self.current_device_name = "iPhone"
        self.temp_dir = tempfile.mkdtemp(prefix="iphone_mount_")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        try:
            # Check for idevice_id (it may return error if no device connected, which is OK)
            result = subprocess.run(
                ["idevice_id", "-l"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            # idevice_id returns 255 when no devices are connected, which is normal
            if result.returncode not in [0, 255]:
                self.logger.error(f"idevice_id command failed: {result.stderr}")
                return False
            
            # Check for ifuse
            result = subprocess.run(
                ["ifuse", "--version"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.logger.error(f"ifuse command failed: {result.stderr}")
                return False
            
            self.logger.info("All dependencies are available")
            return True
            
        except FileNotFoundError as e:
            self.logger.error(f"Missing dependencies: {str(e)}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Dependency check timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False
    
    def detect_devices(self) -> List[Dict[str, str]]:
        """Detect connected iPhone devices"""
        try:
            self.logger.info("Detecting connected devices")
            
            # First, check if any Apple devices are connected via USB
            usb_result = subprocess.run(
                ["lsusb"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if usb_result.returncode == 0 and "Apple" in usb_result.stdout:
                self.logger.info("Apple device detected via USB")
                # Try to get device list
                result = subprocess.run(
                    ["idevice_id", "-l"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Device is properly detected
                    devices = []
                    for udid in result.stdout.strip().split('\n'):
                        if udid.strip():
                            device_info = self._get_device_info(udid.strip())
                            devices.append(device_info)
                    
                    self.logger.info(f"Found {len(devices)} device(s)")
                    return devices
                else:
                    # Device is connected but not trusted/paired
                    self.logger.warning("Apple device connected but not trusted")
                    return [{
                        'udid': 'unknown',
                        'name': 'iPhone (Not Trusted)',
                        'model': 'Unknown Model',
                        'status': 'needs_trust'
                    }]
            else:
                self.logger.info("No Apple devices found")
                return []
            
        except subprocess.TimeoutExpired:
            self.logger.error("Device detection timed out")
            return []
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error detecting devices: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error detecting devices: {str(e)}")
            return []
    
    def _get_device_info(self, udid: str) -> Dict[str, str]:
        """Get device information for a given UDID"""
        try:
            # Get device name
            name_result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "DeviceName"], 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=5
            )
            device_name = name_result.stdout.strip()
            
            # Get device model
            model_result = subprocess.run(
                ["ideviceinfo", "-u", udid, "-k", "ProductType"], 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=5
            )
            device_model = model_result.stdout.strip()
            
            return {
                'udid': udid,
                'name': device_name or f"Unknown Device",
                'model': device_model or "Unknown Model"
            }
            
        except Exception as e:
            self.logger.warning(f"Could not get device info for {udid}: {str(e)}")
            return {
                'udid': udid,
                'name': f"Unknown Device ({udid[:8]}...)",
                'model': "Unknown Model"
            }
    
    def mount_device(self, udid: str) -> Optional[str]:
        """Mount the specified device"""
        try:
            self.logger.info(f"Mounting device {udid}")
            
            # Get device info first
            device_info = self._get_device_info(udid)
            self.current_device_name = device_info.get('name', 'iPhone')
            
            # Check if already mounted
            if self.mount_point and os.path.exists(self.mount_point):
                if self._is_mount_valid():
                    self.logger.info("Device already mounted")
                    return self.mount_point
            
            # Create mount point
            mount_path = os.path.join(self.temp_dir, f"device_{int(time.time())}")
            os.makedirs(mount_path, exist_ok=True)
            
            # Mount device
            result = subprocess.run(
                ["ifuse", "-u", udid, mount_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Verify mount
                if os.path.ismount(mount_path) or os.listdir(mount_path):
                    self.mount_point = mount_path
                    self.current_device = udid
                    self.logger.info(f"Device mounted successfully at {mount_path}")
                    return mount_path
                else:
                    self.logger.error("Mount verification failed")
                    return None
            else:
                self.logger.error(f"Mount failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("Mount operation timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error mounting device: {str(e)}")
            return None
    
    def _is_mount_valid(self) -> bool:
        """Check if current mount is valid"""
        try:
            if not self.mount_point or not os.path.exists(self.mount_point):
                return False
            
            # Check if DCIM directory exists
            dcim_path = os.path.join(self.mount_point, "DCIM")
            return os.path.isdir(dcim_path)
            
        except Exception:
            return False
    
    def unmount_device(self) -> bool:
        """Unmount the current device"""
        try:
            if not self.mount_point:
                return True
            
            self.logger.info(f"Unmounting device from {self.mount_point}")
            
            # Try fusermount first (Linux)
            try:
                result = subprocess.run(
                    ["fusermount", "-u", self.mount_point],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.info("Device unmounted successfully")
                    return True
            except FileNotFoundError:
                # fusermount not available, try umount
                pass
            
            # Try umount as fallback
            result = subprocess.run(
                ["umount", self.mount_point],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info("Device unmounted successfully")
                return True
            else:
                self.logger.warning(f"Unmount failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Unmount operation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error unmounting device: {str(e)}")
            return False
        finally:
            # Clean up mount point
            if self.mount_point and os.path.exists(self.mount_point):
                try:
                    os.rmdir(self.mount_point)
                except:
                    pass
            self.mount_point = None
            self.current_device = None
    
    def get_mount_point(self) -> Optional[str]:
        """Get the current mount point"""
        return self.mount_point
    
    def get_device_name(self) -> str:
        """Get the current device name"""
        return self.current_device_name
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.unmount_device()
            
            # Clean up temp directory
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
