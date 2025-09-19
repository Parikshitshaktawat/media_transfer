"""
Configuration Module
Handles application settings and configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = os.path.join(os.path.expanduser("~"), ".iphone_transfer_config.json")
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'download_dir': os.path.join(os.path.expanduser("~"), "Pictures", "iPhone_Media"),
            'thumbnail_size': 'medium',
            'show_thumbnails': True,
            'preserve_metadata': True,
            'verify_integrity': True,
            'auto_mount': True,
            'batch_size': 10,
            'max_retries': 3,
            'log_level': 'INFO',
            'window_geometry': {
                'width': 1200,
                'height': 800,
                'x': 100,
                'y': 100
            },
            'media_filters': {
                'photos': True,
                'videos': True,
                'min_size': 0,
                'max_size': 0  # 0 means no limit
            },
            'transfer_settings': {
                'create_timestamped_folders': True,
                'preserve_folder_structure': False,
                'skip_duplicates': True,
                'verify_after_transfer': True
            },
            'ui_settings': {
                'theme': 'default',
                'font_size': 10,
                'show_file_sizes': True,
                'show_thumbnails': True,
                'grid_columns': 5
            },
            'advanced': {
                'temp_dir': None,  # Will be set automatically
                'max_memory_usage': 1024,  # MB
                'concurrent_transfers': 3,
                'chunk_size': 1024 * 1024,  # 1MB
                'timeout': 30
            }
        }
    
    def load(self) -> bool:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                # Merge with defaults (preserve new default keys)
                self.config = self._merge_configs(self.config, saved_config)
                self.logger.info("Configuration loaded successfully")
                return True
            else:
                self.logger.info("No configuration file found, using defaults")
                return True
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def _merge_configs(self, default: Dict[str, Any], saved: Dict[str, Any]) -> Dict[str, Any]:
        """Merge saved configuration with defaults"""
        merged = default.copy()
        
        for key, value in saved.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting config value for {key}: {str(e)}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting config value for {key}: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = self._get_default_config()
            self.logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {str(e)}")
            return False
    
    # Convenience properties
    @property
    def download_dir(self) -> str:
        """Get download directory"""
        return self.get('download_dir', os.path.join(os.path.expanduser("~"), "Pictures", "iPhone_Media"))
    
    @download_dir.setter
    def download_dir(self, value: str):
        """Set download directory"""
        self.set('download_dir', value)
    
    @property
    def thumbnail_size(self) -> str:
        """Get thumbnail size setting"""
        return self.get('thumbnail_size', 'medium')
    
    @thumbnail_size.setter
    def thumbnail_size(self, value: str):
        """Set thumbnail size"""
        if value in ['small', 'medium', 'large']:
            self.set('thumbnail_size', value)
    
    @property
    def show_thumbnails(self) -> bool:
        """Get show thumbnails setting"""
        return self.get('show_thumbnails', True)
    
    @show_thumbnails.setter
    def show_thumbnails(self, value: bool):
        """Set show thumbnails setting"""
        self.set('show_thumbnails', value)
    
    @property
    def preserve_metadata(self) -> bool:
        """Get preserve metadata setting"""
        return self.get('preserve_metadata', True)
    
    @preserve_metadata.setter
    def preserve_metadata(self, value: bool):
        """Set preserve metadata setting"""
        self.set('preserve_metadata', value)
    
    @property
    def verify_integrity(self) -> bool:
        """Get verify integrity setting"""
        return self.get('verify_integrity', True)
    
    @verify_integrity.setter
    def verify_integrity(self, value: bool):
        """Set verify integrity setting"""
        self.set('verify_integrity', value)
    
    @property
    def batch_size(self) -> int:
        """Get batch size setting"""
        return self.get('batch_size', 10)
    
    @batch_size.setter
    def batch_size(self, value: int):
        """Set batch size setting"""
        if 1 <= value <= 100:
            self.set('batch_size', value)
    
    @property
    def max_retries(self) -> int:
        """Get max retries setting"""
        return self.get('max_retries', 3)
    
    @max_retries.setter
    def max_retries(self, value: int):
        """Set max retries setting"""
        if 0 <= value <= 10:
            self.set('max_retries', value)
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry settings"""
        return self.get('window_geometry', {
            'width': 1200,
            'height': 800,
            'x': 100,
            'y': 100
        })
    
    def set_window_geometry(self, width: int, height: int, x: int = 100, y: int = 100):
        """Set window geometry settings"""
        self.set('window_geometry', {
            'width': width,
            'height': height,
            'x': x,
            'y': y
        })
    
    def get_media_filters(self) -> Dict[str, Any]:
        """Get media filter settings"""
        return self.get('media_filters', {
            'photos': True,
            'videos': True,
            'min_size': 0,
            'max_size': 0
        })
    
    def set_media_filters(self, photos: bool = True, videos: bool = True, 
                         min_size: int = 0, max_size: int = 0):
        """Set media filter settings"""
        self.set('media_filters', {
            'photos': photos,
            'videos': videos,
            'min_size': min_size,
            'max_size': max_size
        })
    
    def get_transfer_settings(self) -> Dict[str, Any]:
        """Get transfer settings"""
        return self.get('transfer_settings', {
            'create_timestamped_folders': True,
            'preserve_folder_structure': False,
            'skip_duplicates': True,
            'verify_after_transfer': True
        })
    
    def set_transfer_settings(self, create_timestamped_folders: bool = True,
                            preserve_folder_structure: bool = False,
                            skip_duplicates: bool = True,
                            verify_after_transfer: bool = True):
        """Set transfer settings"""
        self.set('transfer_settings', {
            'create_timestamped_folders': create_timestamped_folders,
            'preserve_folder_structure': preserve_folder_structure,
            'skip_duplicates': skip_duplicates,
            'verify_after_transfer': verify_after_transfer
        })
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings"""
        return self.get('ui_settings', {
            'theme': 'default',
            'font_size': 10,
            'show_file_sizes': True,
            'show_thumbnails': True,
            'grid_columns': 5
        })
    
    def set_ui_settings(self, theme: str = 'default', font_size: int = 10,
                        show_file_sizes: bool = True, show_thumbnails: bool = True,
                        grid_columns: int = 5):
        """Set UI settings"""
        self.set('ui_settings', {
            'theme': theme,
            'font_size': font_size,
            'show_file_sizes': show_file_sizes,
            'show_thumbnails': show_thumbnails,
            'grid_columns': grid_columns
        })
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """Get advanced settings"""
        return self.get('advanced', {
            'temp_dir': None,
            'max_memory_usage': 1024,
            'concurrent_transfers': 3,
            'chunk_size': 1024 * 1024,
            'timeout': 30
        })
    
    def set_advanced_settings(self, max_memory_usage: int = 1024,
                            concurrent_transfers: int = 3,
                            chunk_size: int = 1024 * 1024,
                            timeout: int = 30):
        """Set advanced settings"""
        self.set('advanced', {
            'max_memory_usage': max_memory_usage,
            'concurrent_transfers': concurrent_transfers,
            'chunk_size': chunk_size,
            'timeout': timeout
        })
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return any issues"""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check download directory
            download_dir = self.download_dir
            if not os.path.exists(download_dir):
                try:
                    os.makedirs(download_dir, exist_ok=True)
                except Exception as e:
                    issues['errors'].append(f"Cannot create download directory: {str(e)}")
            
            # Check if download directory is writable
            if not os.access(download_dir, os.W_OK):
                issues['errors'].append(f"Download directory is not writable: {download_dir}")
            
            # Check batch size
            batch_size = self.batch_size
            if not (1 <= batch_size <= 100):
                issues['warnings'].append(f"Batch size should be between 1 and 100, got {batch_size}")
            
            # Check max retries
            max_retries = self.max_retries
            if not (0 <= max_retries <= 10):
                issues['warnings'].append(f"Max retries should be between 0 and 10, got {max_retries}")
            
            # Check advanced settings
            advanced = self.get_advanced_settings()
            if advanced.get('max_memory_usage', 0) < 100:
                issues['warnings'].append("Max memory usage is very low, may cause performance issues")
            
            if advanced.get('concurrent_transfers', 0) > 10:
                issues['warnings'].append("High concurrent transfers may cause system instability")
            
        except Exception as e:
            issues['errors'].append(f"Error validating configuration: {str(e)}")
        
        return issues
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to a file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {str(e)}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            if not isinstance(imported_config, dict):
                raise ValueError("Invalid configuration format")
            
            # Merge with current config
            self.config = self._merge_configs(self.config, imported_config)
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {str(e)}")
            return False
