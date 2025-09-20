"""
Media Handler Module
Handles media file scanning, metadata extraction, and thumbnail generation
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from PIL import Image, ExifTags
import hashlib

# HEIC support removed - files will be saved in original format

# Increase PIL image size limit to handle large iPhone photos
from PIL import Image
Image.MAX_IMAGE_PIXELS = 200000000  # 200M pixels (was 89M)

class MediaHandler:
    """Handles media file operations with metadata preservation"""
    
    # Supported media file extensions
    PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.tiff', '.tif'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.m4v', '.3gp', '.avi', '.mkv'}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def scan_media(self, mount_point: str) -> List[Dict[str, any]]:
        """Scan for media files on the mounted device"""
        return self.scan_media_with_progress(mount_point, None)
    
    def scan_media_with_progress(self, mount_point: str, progress_callback=None, media_type: str = "all", start_range: int = None, end_range: int = None) -> List[Dict[str, any]]:
        """Scan for media files on the mounted device with progress updates and media type filtering"""
        try:
            self.logger.info(f"Scanning media files in {mount_point} (type: {media_type})")
            
            if not os.path.exists(mount_point):
                raise FileNotFoundError(f"Mount point not found: {mount_point}")
            
            dcim_path = os.path.join(mount_point, "DCIM")
            if not os.path.exists(dcim_path):
                raise FileNotFoundError("DCIM directory not found on device")
            
            # First, collect and categorize files based on media type filter
            photo_files = []
            video_files = []
            
            for root, dirs, files in os.walk(dcim_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    # Apply media type filtering
                    if media_type == "photos" and file_ext in self.PHOTO_EXTENSIONS:
                        photo_files.append(file_path)
                    elif media_type == "videos" and file_ext in self.VIDEO_EXTENSIONS:
                        video_files.append(file_path)
                    elif media_type == "all":
                        if file_ext in self.PHOTO_EXTENSIONS:
                            photo_files.append(file_path)
                        elif file_ext in self.VIDEO_EXTENSIONS:
                            video_files.append(file_path)
            
            # Combine files (photos first, then videos)
            all_files = photo_files + video_files
            total_files = len(all_files)
            
            # Apply range filtering if specified
            if start_range is not None and end_range is not None:
                # Convert to 0-based indexing
                start_idx = max(0, start_range - 1)
                end_idx = min(len(all_files), end_range)
                all_files = all_files[start_idx:end_idx]
                self.logger.info(f"Applied range filter: {start_range}-{end_range} ({len(all_files)} files)")
            
            self.logger.info(f"Found {len(photo_files)} photos and {len(video_files)} videos")
            
            media_files = []
            processed = 0
            
            # Process files in smaller batches to avoid memory issues
            batch_size = 20
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                
                for file_path in batch:
                    try:
                        # Update progress
                        if progress_callback:
                            filename = os.path.basename(file_path)
                            result = progress_callback(processed, len(all_files), filename)
                            # Check if callback returned False (stop requested)
                            if result is False:
                                self.logger.info("Scan stopped by user request")
                                return media_files  # Return partial results
                        
                        media_info = self._get_media_info(file_path)
                        if media_info:
                            media_files.append(media_info)
                        
                        processed += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                        processed += 1
                        continue
                    
                    # Small delay to keep UI responsive and allow memory cleanup
                    if progress_callback:
                        import time
                        import gc
                        time.sleep(0.05)  # Slightly longer delay
                        gc.collect()  # Force garbage collection
            
            # Sort by modification time (newest first)
            media_files.sort(key=lambda x: x.get('mtime', 0), reverse=True)
            
            self.logger.info(f"Successfully processed {len(media_files)} media files")
            return media_files
            
        except Exception as e:
            self.logger.error(f"Error scanning media: {str(e)}")
            raise
    
    def _get_media_info(self, file_path: str) -> Optional[Dict[str, any]]:
        """Get detailed information about a media file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            
            # Log file being processed for debugging
            self.logger.debug(f"Processing file: {filename} ({file_ext}, {stat.st_size:,} bytes)")
            
            # Basic file info
            media_info = {
                'path': file_path,
                'filename': filename,
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'ctime': stat.st_ctime,
                'extension': file_ext,
                'type': 'photo' if file_ext in self.PHOTO_EXTENSIONS else 'video'
            }
            
            # Get metadata based on file type
            if media_info['type'] == 'photo':
                metadata = self._extract_photo_metadata(file_path)
            else:
                metadata = self._extract_video_metadata(file_path)
            
            media_info.update(metadata)
            
            # Generate file hash for integrity checking
            media_info['hash'] = self._calculate_file_hash(file_path)
            
            return media_info
            
        except Exception as e:
            self.logger.warning(f"Error getting media info for {file_path}: {str(e)}")
            return None
    
    def _extract_photo_metadata(self, file_path: str) -> Dict[str, any]:
        """Extract metadata from photo files"""
        metadata = {
            'exif_data': {},
            'creation_date': None,
            'camera_make': None,
            'camera_model': None,
            'dimensions': None,
            'orientation': None
        }
        
        try:
            # Try to open the image with PIL
            with Image.open(file_path) as img:
                # Get dimensions
                metadata['dimensions'] = img.size
                
                # Get EXIF data
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    
                    # Convert EXIF tags to readable format
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        metadata['exif_data'][tag] = value
                    
                    # Extract specific useful metadata
                    if 271 in exif:  # Make
                        metadata['camera_make'] = exif[271]
                    if 272 in exif:  # Model
                        metadata['camera_model'] = exif[272]
                    if 274 in exif:  # Orientation
                        metadata['orientation'] = exif[274]
                    if 306 in exif:  # DateTime
                        metadata['creation_date'] = exif[306]
                    elif 36867 in exif:  # DateTimeOriginal
                        metadata['creation_date'] = exif[36867]
                    elif 36868 in exif:  # DateTimeDigitized
                        metadata['creation_date'] = exif[36868]
                
        except Exception as e:
            # If PIL fails, try alternative methods for HEIC files
            if file_path.lower().endswith('.heic'):
                self.logger.debug(f"PIL failed for HEIC file {file_path}, trying alternative methods: {str(e)}")
                metadata.update(self._extract_heic_metadata(file_path))
            else:
                # For other files, just log as debug to reduce noise
                self.logger.debug(f"Error extracting photo metadata from {file_path}: {str(e)}")
        
        return metadata
    
    def _extract_heic_metadata(self, file_path: str) -> Dict[str, any]:
        """Extract additional metadata from HEIC files"""
        metadata = {}
        
        try:
            # Try to use exifread for HEIC files
            try:
                import exifread
                with open(file_path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    
                    for tag, value in tags.items():
                        if 'Image DateTime' in tag:
                            metadata['creation_date'] = str(value)
                        elif 'Image Make' in tag:
                            metadata['camera_make'] = str(value)
                        elif 'Image Model' in tag:
                            metadata['camera_model'] = str(value)
                        elif 'EXIF DateTimeOriginal' in tag:
                            metadata['creation_date'] = str(value)
                        elif 'EXIF DateTimeDigitized' in tag:
                            metadata['creation_date'] = str(value)
                            
            except ImportError:
                self.logger.debug("exifread not available for HEIC metadata extraction")
            except Exception as e:
                self.logger.debug(f"Error extracting HEIC metadata with exifread: {str(e)}")
                
            # If exifread fails, try to get basic file info
            if not metadata.get('creation_date'):
                try:
                    stat = os.stat(file_path)
                    metadata['creation_date'] = stat.st_mtime
                except Exception as e:
                    self.logger.debug(f"Error getting file stats: {str(e)}")
                    
        except Exception as e:
            self.logger.debug(f"Error extracting HEIC metadata: {str(e)}")
        
        return metadata
    
    def _extract_video_metadata(self, file_path: str) -> Dict[str, any]:
        """Extract metadata from video files"""
        metadata = {
            'duration': None,
            'resolution': None,
            'fps': None,
            'codec': None
        }
        
        try:
            # Try to use ffprobe for video metadata
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Extract video stream info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        metadata['codec'] = stream.get('codec_name')
                        metadata['resolution'] = f"{stream.get('width')}x{stream.get('height')}"
                        metadata['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                        break
                
                # Extract duration
                format_info = data.get('format', {})
                if 'duration' in format_info:
                    metadata['duration'] = float(format_info['duration'])
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.debug("ffprobe not available for video metadata")
        except Exception as e:
            self.logger.debug(f"Error extracting video metadata: {str(e)}")
        
        return metadata
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file for integrity checking"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (OSError, IOError) as e:
            # Handle I/O errors gracefully (file might be corrupted or inaccessible)
            self.logger.debug(f"I/O error calculating hash for {file_path}: {str(e)}")
            return ""
        except Exception as e:
            self.logger.warning(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def create_thumbnail(self, file_path: str, size: Tuple[int, int] = (150, 150)) -> Optional[Image.Image]:
        """Create a thumbnail for a media file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in self.PHOTO_EXTENSIONS:
                return self._create_photo_thumbnail(file_path, size)
            elif file_ext in self.VIDEO_EXTENSIONS:
                return self._create_video_thumbnail(file_path, size)
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Error creating thumbnail for {file_path}: {str(e)}")
            return None
    
    def _create_photo_thumbnail(self, file_path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Create thumbnail for photo files with memory optimization"""
        try:
            with Image.open(file_path) as img:
                # Check if image is too large and skip thumbnail creation
                if img.size[0] * img.size[1] > 50000000:  # 50M pixels
                    self.logger.debug(f"Skipping thumbnail for very large image: {file_path}")
                    return None
                
                # Handle orientation
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    orientation = exif.get(274)  # Orientation tag
                    if orientation:
                        img = self._apply_orientation(img, orientation)
                
                # Create thumbnail with aggressive resizing for memory efficiency
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Limit thumbnail size to prevent memory issues
                if img.size[0] > 200 or img.size[1] > 200:
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                return img
                
        except Exception as e:
            self.logger.debug(f"Error creating photo thumbnail: {str(e)}")
            return None
    
    def _create_video_thumbnail(self, file_path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Create thumbnail for video files"""
        try:
            # Try to use ffmpeg to extract frame
            import subprocess
            temp_image = f"/tmp/thumb_{os.path.basename(file_path)}.jpg"
            
            result = subprocess.run([
                'ffmpeg', '-i', file_path, '-ss', '00:00:01', '-vframes', '1',
                '-y', temp_image
            ], capture_output=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(temp_image):
                with Image.open(temp_image) as img:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    os.remove(temp_image)
                    return img
            else:
                os.remove(temp_image) if os.path.exists(temp_image) else None
                return self._create_video_placeholder(size)
                
        except Exception as e:
            self.logger.debug(f"Error creating video thumbnail: {str(e)}")
            return self._create_video_placeholder(size)
    
    def _create_video_placeholder(self, size: Tuple[int, int]) -> Image.Image:
        """Create a placeholder image for videos"""
        img = Image.new('RGB', size, (50, 50, 50))
        return img
    
    def _apply_orientation(self, img: Image.Image, orientation: int) -> Image.Image:
        """Apply EXIF orientation to image"""
        try:
            if orientation == 1:
                return img
            elif orientation == 2:
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                return img.rotate(180)
            elif orientation == 4:
                return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(90)
            elif orientation == 6:
                return img.rotate(-90)
            elif orientation == 7:
                return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(-90)
            elif orientation == 8:
                return img.rotate(90)
            else:
                return img
        except Exception:
            return img
    
    def preserve_metadata(self, source_path: str, dest_path: str) -> bool:
        """Preserve metadata when copying files"""
        try:
            # Use shutil.copy2 to preserve timestamps and permissions
            import shutil
            shutil.copy2(source_path, dest_path)
            
            # For photos, try to preserve EXIF data
            if os.path.splitext(source_path)[1].lower() in self.PHOTO_EXTENSIONS:
                self._preserve_photo_metadata(source_path, dest_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error preserving metadata: {str(e)}")
            return False
    
    def _preserve_photo_metadata(self, source_path: str, dest_path: str):
        """Preserve photo metadata using PIL"""
        try:
            with Image.open(source_path) as source_img:
                # Get EXIF data
                if hasattr(source_img, '_getexif') and source_img._getexif() is not None:
                    exif = source_img._getexif()
                    
                    # Open destination and preserve EXIF
                    with Image.open(dest_path) as dest_img:
                        dest_img.save(dest_path, exif=exif)
                        
        except Exception as e:
            self.logger.debug(f"Error preserving photo metadata: {str(e)}")
    
    def get_media_summary(self, media_files: List[Dict[str, any]]) -> Dict[str, int]:
        """Get summary statistics of media files"""
        summary = {
            'total': len(media_files),
            'photos': 0,
            'videos': 0,
            'total_size': 0
        }
        
        for media in media_files:
            if media.get('type') == 'photo':
                summary['photos'] += 1
            elif media.get('type') == 'video':
                summary['videos'] += 1
            
            summary['total_size'] += media.get('size', 0)
        
        return summary
