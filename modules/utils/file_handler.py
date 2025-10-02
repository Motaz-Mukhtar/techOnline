#!/usr/bin/env python3
"""
File handling utilities for TechOnline e-commerce platform.

This module provides comprehensive file upload, validation, and storage
functionalities for handling product images and customer profile avatars.
"""

import os
import uuid
import hashlib
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes
from typing import Optional, Tuple, Dict, Any


class FileHandler:
    """
    Handles file upload, validation, and storage operations.
    
    This class provides methods for:
    - File validation (type, size, dimensions)
    - Secure file storage with unique naming
    - Image processing and optimization
    - File deletion and cleanup
    """
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_PROFILE_SIZE = 2 * 1024 * 1024  # 2MB for profile images
    
    # Image dimensions
    MAX_IMAGE_WIDTH = 2048
    MAX_IMAGE_HEIGHT = 2048
    PROFILE_IMAGE_SIZE = (300, 300)  # Profile images will be resized to this
    PRODUCT_IMAGE_MAX_SIZE = (800, 800)  # Product images max size
    
    def __init__(self, upload_folder: str = None):
        """
        Initialize FileHandler with upload folder.
        
        Args:
            upload_folder (str): Base upload directory path
        """
        self.upload_folder = upload_folder or os.path.join(
            current_app.static_folder, 'uploads'
        )
        self._ensure_upload_directories()
    
    def _ensure_upload_directories(self):
        """
        Ensure all required upload directories exist.
        """
        directories = [
            os.path.join(self.upload_folder, 'products'),
            os.path.join(self.upload_folder, 'profiles'),
            os.path.join(self.upload_folder, 'temp')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """
        Check if file extension is allowed.
        
        Args:
            filename (str): Name of the file to check
            
        Returns:
            bool: True if file extension is allowed, False otherwise
        """
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS)
    
    def validate_file(self, file, file_type: str = 'product') -> Dict[str, Any]:
        """
        Validate uploaded file for security and constraints.
        
        Args:
            file: Werkzeug FileStorage object
            file_type (str): Type of file ('product' or 'profile')
            
        Returns:
            dict: Validation result with 'valid' boolean and 'error' message
        """
        if not file or not file.filename:
            return {'valid': False, 'error': 'No file selected'}
        
        # Check file extension
        if not self.is_allowed_file(file.filename):
            return {
                'valid': False, 
                'error': f'File type not allowed. Allowed types: {", ".join(self.ALLOWED_EXTENSIONS)}'
            }
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        max_size = self.MAX_PROFILE_SIZE if file_type == 'profile' else self.MAX_FILE_SIZE
        if file_size > max_size:
            return {
                'valid': False, 
                'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }
        
        # Validate image using PIL
        try:
            image = Image.open(file)
            image.verify()  # Verify it's a valid image
            file.seek(0)  # Reset file pointer after verification
            
            # Check image dimensions
            width, height = image.size
            if width > self.MAX_IMAGE_WIDTH or height > self.MAX_IMAGE_HEIGHT:
                return {
                    'valid': False,
                    'error': f'Image dimensions too large. Maximum: {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT}'
                }
                
        except Exception as e:
            return {'valid': False, 'error': f'Invalid image file: {str(e)}'}
        
        return {'valid': True, 'error': None}
    
    def generate_unique_filename(self, original_filename: str, prefix: str = '') -> str:
        """
        Generate a unique filename to prevent conflicts.
        
        Args:
            original_filename (str): Original filename
            prefix (str): Optional prefix for the filename
            
        Returns:
            str: Unique filename with original extension
        """
        # Get file extension
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        
        # Create filename with prefix if provided
        if prefix:
            filename = f"{prefix}_{unique_id}.{extension}"
        else:
            filename = f"{unique_id}.{extension}"
        
        return secure_filename(filename)
    
    def process_image(self, file, target_size: Tuple[int, int] = None, 
                     quality: int = 85) -> Image.Image:
        """
        Process and optimize image.
        
        Args:
            file: File object or PIL Image
            target_size (tuple): Target size (width, height) for resizing
            quality (int): JPEG quality (1-100)
            
        Returns:
            PIL.Image: Processed image
        """
        if hasattr(file, 'read'):
            image = Image.open(file)
        else:
            image = file
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if target size specified
        if target_size:
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        return image
    
    def save_file(self, file, file_type: str = 'product', 
                  entity_id: str = None) -> Dict[str, Any]:
        """
        Save uploaded file to appropriate directory.
        
        Args:
            file: Werkzeug FileStorage object
            file_type (str): Type of file ('product' or 'profile')
            entity_id (str): ID of the entity (product/customer) for naming
            
        Returns:
            dict: Result with 'success' boolean, 'filename', 'url', and 'error'
        """
        # Validate file first
        validation = self.validate_file(file, file_type)
        if not validation['valid']:
            return {
                'success': False,
                'filename': None,
                'url': None,
                'error': validation['error']
            }
        
        try:
            # Generate unique filename
            prefix = f"{file_type}_{entity_id}" if entity_id else file_type
            filename = self.generate_unique_filename(file.filename, prefix)
            
            # Determine subdirectory
            subdirectory = 'products' if file_type == 'product' else 'profiles'
            file_path = os.path.join(self.upload_folder, subdirectory, filename)
            
            # Process and save image
            if file_type == 'profile':
                # Resize profile images to standard size
                processed_image = self.process_image(file, self.PROFILE_IMAGE_SIZE)
                processed_image.save(file_path, 'JPEG', quality=85, optimize=True)
            elif file_type == 'product':
                # Optimize product images
                processed_image = self.process_image(file, self.PRODUCT_IMAGE_MAX_SIZE)
                processed_image.save(file_path, 'JPEG', quality=90, optimize=True)
            else:
                # Save as-is for other types
                file.save(file_path)
            
            # Generate URL for accessing the file
            file_url = f"/static/uploads/{subdirectory}/{filename}"
            
            return {
                'success': True,
                'filename': filename,
                'url': file_url,
                'path': file_path,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'filename': None,
                'url': None,
                'error': f'Failed to save file: {str(e)}'
            }
    
    def delete_file(self, filename: str, file_type: str = 'product') -> bool:
        """
        Delete a file from storage.
        
        Args:
            filename (str): Name of the file to delete
            file_type (str): Type of file ('product' or 'profile')
            
        Returns:
            bool: True if file was deleted successfully, False otherwise
        """
        try:
            subdirectory = 'products' if file_type == 'product' else 'profiles'
            file_path = os.path.join(self.upload_folder, subdirectory, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception:
            return False
    
    def get_file_info(self, filename: str, file_type: str = 'product') -> Optional[Dict[str, Any]]:
        """
        Get information about a stored file.
        
        Args:
            filename (str): Name of the file
            file_type (str): Type of file ('product' or 'profile')
            
        Returns:
            dict: File information or None if file doesn't exist
        """
        try:
            subdirectory = 'products' if file_type == 'product' else 'profiles'
            file_path = os.path.join(self.upload_folder, subdirectory, filename)
            
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'filename': filename,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'mime_type': mime_type,
                'url': f"/static/uploads/{subdirectory}/{filename}"
            }
            
        except Exception:
            return None


# Global file handler instance - initialized lazily
file_handler = None


def get_file_handler():
    """Get or create the global file handler instance."""
    global file_handler
    if file_handler is None:
        file_handler = FileHandler()
    return file_handler


def allowed_file(filename: str) -> bool:
    """
    Convenience function to check if file is allowed.
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return get_file_handler().is_allowed_file(filename)


def save_uploaded_file(file, file_type: str = 'product', 
                      entity_id: str = None) -> Dict[str, Any]:
    """
    Convenience function to save uploaded file.
    
    Args:
        file: Werkzeug FileStorage object
        file_type (str): Type of file ('product' or 'profile')
        entity_id (str): ID of the entity for naming
        
    Returns:
        dict: Result with success status and file information
    """
    return get_file_handler().save_file(file, file_type, entity_id)


def delete_uploaded_file(filename: str, file_type: str = 'product') -> bool:
    """
    Convenience function to delete uploaded file.
    
    Args:
        filename (str): Name of the file to delete
        file_type (str): Type of file ('product' or 'profile')
        
    Returns:
        bool: True if file was deleted successfully, False otherwise
    """
    return get_file_handler().delete_file(filename, file_type)