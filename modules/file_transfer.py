"""
File Transfer Module
Handles secure file transfer with integrity verification and metadata preservation
"""

import os
import shutil
import hashlib
import logging
import re
from typing import List, Dict, Optional, Callable
from pathlib import Path
from datetime import datetime
import json

class FileTransfer:
    """Handles secure file transfer with integrity checking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.transfer_history = []
    
    
    def download_files(self, media_files: List[Dict[str, any]], download_dir: str, 
                      device_name: str = "iPhone", progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """Download media files with integrity verification"""
        try:
            self.logger.info(f"Starting download of {len(media_files)} files to {download_dir}")
            
            # Create organized download directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_device_name = self._sanitize_folder_name(device_name)
            base_folder_name = f"{safe_device_name}_{timestamp}"
            download_path = os.path.join(download_dir, base_folder_name)
            
            # Create main folder and subfolders
            os.makedirs(download_path, exist_ok=True)
            photos_path = os.path.join(download_path, "Photos")
            videos_path = os.path.join(download_path, "Videos")
            os.makedirs(photos_path, exist_ok=True)
            os.makedirs(videos_path, exist_ok=True)
            
            results = {
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'total': len(media_files),
                'download_path': download_path
            }
            
            # Process files in batches
            batch_size = 10
            for i in range(0, len(media_files), batch_size):
                batch = media_files[i:i + batch_size]
                batch_results = self._process_batch(batch, download_path, photos_path, videos_path, progress_callback, i, len(media_files))
                
                results['success'] += batch_results['success']
                results['failed'] += batch_results['failed']
                results['skipped'] += batch_results['skipped']
            
            # Save transfer history
            self._save_transfer_history(results, download_path)
            
            self.logger.info(f"Download completed: {results['success']} success, {results['failed']} failed, {results['skipped']} skipped")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in download_files: {str(e)}")
            raise
    
    
    def _process_batch(self, batch: List[Dict[str, any]], download_path: str, 
                      photos_path: str, videos_path: str, progress_callback: Optional[Callable], batch_start: int, total_files: int) -> Dict[str, int]:
        """Process a batch of files"""
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, media_file in enumerate(batch):
            try:
                file_index = batch_start + i
                
                # Update progress
                if progress_callback:
                    filename = media_file.get('name', 'Unknown')
                    if filename == 'Unknown':
                        file_path = media_file.get('path', '')
                        if file_path:
                            filename = os.path.basename(file_path)
                    progress = int((file_index / total_files) * 100) if total_files > 0 else 0
                    status = f"Processing {filename} ({file_index}/{total_files})"
                    progress_callback(progress, status)
                
                # Determine destination path based on media type
                media_type = media_file.get('type', 'photo')
                if media_type == 'photo':
                    target_path = photos_path
                else:
                    target_path = videos_path
                
                dest_path = self._get_destination_path(media_file, target_path)
                if os.path.exists(dest_path):
                    if self._verify_existing_file(media_file, dest_path):
                        results['skipped'] += 1
                        self.logger.debug(f"Skipping existing file: {media_file['filename']}")
                        continue
                    else:
                        # File exists but is corrupted, remove it
                        os.remove(dest_path)
                
                # Transfer file with integrity verification
                if self._transfer_file_with_verification(media_file, dest_path):
                    results['success'] += 1
                    self.logger.debug(f"Successfully transferred: {media_file['filename']}")
                else:
                    results['failed'] += 1
                    self.logger.error(f"Failed to transfer: {media_file['filename']}")
                
            except Exception as e:
                results['failed'] += 1
                self.logger.error(f"Error processing {media_file.get('filename', 'unknown')}: {str(e)}")
        
        return results
    
    def _get_destination_path(self, media_file: Dict[str, any], download_path: str) -> str:
        """Get the destination path for a media file"""
        filename = media_file['filename']
        base_name, ext = os.path.splitext(filename)
        
        # Handle duplicate filenames
        dest_path = os.path.join(download_path, filename)
        counter = 1
        
        while os.path.exists(dest_path):
            new_filename = f"{base_name}_{counter}{ext}"
            dest_path = os.path.join(download_path, new_filename)
            counter += 1
        
        return dest_path
    
    def _transfer_file_with_verification(self, media_file: Dict[str, any], dest_path: str) -> bool:
        """Transfer file with integrity verification"""
        try:
            source_path = media_file['path']
            
            if not os.path.exists(source_path):
                self.logger.error(f"Source file not found: {source_path}")
                return False
            
            # Get source file hash
            source_hash = media_file.get('hash')
            if not source_hash:
                source_hash = self._calculate_file_hash(source_path)
            
            # Copy file with metadata preservation
            if not self._copy_file_with_metadata(source_path, dest_path):
                return False
            
            # Verify integrity
            if not self._verify_file_integrity(dest_path, source_hash):
                self.logger.error(f"Integrity verification failed for {dest_path}")
                os.remove(dest_path)
                return False
            
            # Preserve additional metadata
            self._preserve_additional_metadata(media_file, dest_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error transferring file: {str(e)}")
            return False
    
    def _copy_file_with_metadata(self, source_path: str, dest_path: str) -> bool:
        """Copy file while preserving metadata"""
        try:
            # Log file details for debugging
            source_size = os.path.getsize(source_path)
            source_ext = os.path.splitext(source_path)[1].lower()
            dest_ext = os.path.splitext(dest_path)[1].lower()
            
            self.logger.info(f"Copying {source_ext} file: {os.path.basename(source_path)} ({source_size:,} bytes)")
            self.logger.info(f"Destination: {os.path.basename(dest_path)} ({dest_ext})")
            
            # Check if source and destination extensions match
            if source_ext != dest_ext:
                self.logger.warning(f"Extension mismatch: {source_ext} -> {dest_ext}")
                # This should NOT happen - files should keep original format
                self.logger.error(f"CONVERSION DETECTED: {source_path} -> {dest_path}")
                return False
            
            # Use shutil.copy2 to preserve timestamps and permissions
            shutil.copy2(source_path, dest_path)
            
            # Verify basic copy
            if not os.path.exists(dest_path):
                self.logger.error(f"Destination file not created: {dest_path}")
                return False
            
            # Check file sizes match
            dest_size = os.path.getsize(dest_path)
            if source_size != dest_size:
                self.logger.error(f"File size mismatch: source={source_size:,}, dest={dest_size:,}")
                return False
            
            self.logger.info(f"Successfully copied: {os.path.basename(dest_path)} ({dest_size:,} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying file: {str(e)}")
            return False
    
    def _verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Verify file integrity using hash comparison"""
        try:
            if not expected_hash:
                return True  # Skip verification if no hash available
            
            actual_hash = self._calculate_file_hash(file_path)
            return actual_hash == expected_hash
            
        except Exception as e:
            self.logger.error(f"Error verifying file integrity: {str(e)}")
            return False
    
    def _verify_existing_file(self, media_file: Dict[str, any], dest_path: str) -> bool:
        """Verify if existing file is valid"""
        try:
            if not os.path.exists(dest_path):
                return False
            
            # Check file size
            if os.path.getsize(media_file['path']) != os.path.getsize(dest_path):
                return False
            
            # Check hash if available
            expected_hash = media_file.get('hash')
            if expected_hash:
                actual_hash = self._calculate_file_hash(dest_path)
                return actual_hash == expected_hash
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying existing file: {str(e)}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {str(e)}")
            return ""
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize device name for use in folder name"""
        try:
            # Replace invalid characters with underscores
            invalid_chars = '<>:"/\\|?*'
            sanitized = name
            
            for char in invalid_chars:
                sanitized = sanitized.replace(char, '_')
            
            # Handle apostrophes and quotes
            sanitized = re.sub(r"['\"`]", "_", sanitized)
            
            # Remove leading/trailing spaces and dots
            sanitized = sanitized.strip(' .')
            
            # Replace multiple spaces/underscores with single underscore
            sanitized = re.sub(r'[_\s]+', '_', sanitized)
            
            # Remove any remaining special characters except alphanumeric and underscores
            sanitized = re.sub(r'[^\w_]', '', sanitized)
            
            # Ensure name is not empty
            if not sanitized:
                sanitized = "iPhone"
            
            # Limit length
            if len(sanitized) > 50:
                sanitized = sanitized[:50]
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Error sanitizing folder name: {str(e)}")
            return "iPhone"
    
    def _preserve_additional_metadata(self, media_file: Dict[str, any], dest_path: str):
        """Preserve additional metadata like EXIF data"""
        try:
            file_ext = os.path.splitext(dest_path)[1].lower()
            
            # For photos, preserve EXIF data
            if file_ext in {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}:
                self._preserve_photo_metadata(media_file, dest_path)
            
            # Create metadata file
            self._create_metadata_file(media_file, dest_path)
            
        except Exception as e:
            self.logger.debug(f"Error preserving additional metadata: {str(e)}")
    
    def _preserve_photo_metadata(self, media_file: Dict[str, any], dest_path: str):
        """Preserve photo metadata using PIL"""
        try:
            from PIL import Image
            
            source_path = media_file['path']
            self.logger.debug(f"Preserving metadata for: {os.path.basename(dest_path)}")
            
            # Check if source file exists and has content
            if not os.path.exists(source_path):
                self.logger.warning(f"Source file not found: {source_path}")
                return
            
            source_size = os.path.getsize(source_path)
            if source_size == 0:
                self.logger.warning(f"Source file is empty: {source_path}")
                return
            
            with Image.open(source_path) as source_img:
                # Get EXIF data
                if hasattr(source_img, '_getexif') and source_img._getexif() is not None:
                    exif = source_img._getexif()
                    self.logger.debug(f"Found EXIF data for {os.path.basename(dest_path)}")
                    
                    # Check if destination file exists and has content
                    if not os.path.exists(dest_path):
                        self.logger.warning(f"Destination file not found: {dest_path}")
                        return
                    
                    dest_size = os.path.getsize(dest_path)
                    if dest_size == 0:
                        self.logger.warning(f"Destination file is empty: {dest_path}")
                        return
                    
                    # Save with EXIF data
                    with Image.open(dest_path) as dest_img:
                        # Create a backup before modifying
                        backup_path = dest_path + ".backup"
                        shutil.copy2(dest_path, backup_path)
                        
                        try:
                            dest_img.save(dest_path, exif=exif)
                            
                            # Verify the save was successful
                            new_size = os.path.getsize(dest_path)
                            if new_size == 0:
                                self.logger.error(f"EXIF preservation failed - file became 0 bytes: {dest_path}")
                                # Restore from backup
                                shutil.copy2(backup_path, dest_path)
                                self.logger.info(f"Restored from backup: {dest_path}")
                            else:
                                self.logger.debug(f"EXIF preservation successful: {os.path.basename(dest_path)} ({new_size:,} bytes)")
                                # Remove backup
                                os.remove(backup_path)
                                
                        except Exception as save_error:
                            self.logger.error(f"Error saving with EXIF: {save_error}")
                            # Restore from backup
                            shutil.copy2(backup_path, dest_path)
                            self.logger.info(f"Restored from backup: {dest_path}")
                            # Remove backup
                            os.remove(backup_path)
                else:
                    self.logger.debug(f"No EXIF data found for {os.path.basename(dest_path)}")
                        
        except Exception as e:
            self.logger.error(f"Error preserving photo metadata: {str(e)}")
            # Don't let metadata preservation break the file transfer
    
    def _create_metadata_file(self, media_file: Dict[str, any], dest_path: str):
        """Create a metadata file alongside the media file"""
        try:
            metadata_path = dest_path + ".meta"
            
            metadata = {
                'original_path': media_file['path'],
                'filename': media_file['filename'],
                'size': media_file['size'],
                'mtime': media_file['mtime'],
                'ctime': media_file['ctime'],
                'type': media_file['type'],
                'hash': media_file.get('hash', ''),
                'transfer_date': datetime.now().isoformat(),
                'exif_data': media_file.get('exif_data', {}),
                'creation_date': media_file.get('creation_date'),
                'camera_make': media_file.get('camera_make'),
                'camera_model': media_file.get('camera_model'),
                'dimensions': media_file.get('dimensions'),
                'orientation': media_file.get('orientation')
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.debug(f"Error creating metadata file: {str(e)}")
    
    def _save_transfer_history(self, results: Dict[str, int], download_path: str):
        """Save transfer history"""
        try:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'download_path': download_path,
                'results': results
            }
            
            self.transfer_history.append(history_entry)
            
            # Save to file
            history_file = os.path.join(os.path.expanduser("~"), ".iphone_transfer_history.json")
            
            # Load existing history
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    all_history = json.load(f)
            else:
                all_history = []
            
            all_history.append(history_entry)
            
            # Keep only last 50 entries
            if len(all_history) > 50:
                all_history = all_history[-50:]
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(all_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving transfer history: {str(e)}")
    
    def get_transfer_history(self) -> List[Dict[str, any]]:
        """Get transfer history"""
        try:
            history_file = os.path.join(os.path.expanduser("~"), ".iphone_transfer_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Error loading transfer history: {str(e)}")
            return []
    
    def verify_downloaded_files(self, download_path: str) -> Dict[str, int]:
        """Verify integrity of downloaded files"""
        try:
            results = {'verified': 0, 'corrupted': 0, 'missing_metadata': 0}
            
            for root, dirs, files in os.walk(download_path):
                for file in files:
                    if file.endswith('.meta'):
                        continue  # Skip metadata files
                    
                    file_path = os.path.join(root, file)
                    metadata_path = file_path + ".meta"
                    
                    if os.path.exists(metadata_path):
                        # Verify using metadata
                        if self._verify_file_with_metadata(file_path, metadata_path):
                            results['verified'] += 1
                        else:
                            results['corrupted'] += 1
                    else:
                        results['missing_metadata'] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error verifying downloaded files: {str(e)}")
            return {'verified': 0, 'corrupted': 0, 'missing_metadata': 0}
    
    def _verify_file_with_metadata(self, file_path: str, metadata_path: str) -> bool:
        """Verify file using its metadata"""
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check file size
            if os.path.getsize(file_path) != metadata.get('size', 0):
                return False
            
            # Check hash if available
            expected_hash = metadata.get('hash')
            if expected_hash:
                actual_hash = self._calculate_file_hash(file_path)
                return actual_hash == expected_hash
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying file with metadata: {str(e)}")
            return False
