"""
Secure file handling service for uploads.
Validates file types, sizes, and handles storage.
"""
import os
import re
import uuid
import logging
from enum import Enum
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile

from ..core import config

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for uploads."""
    IMAGE = "image"
    AUDIO = "audio"


class FileHandler:
    """
    Secure file upload handler with validation.
    
    Features:
    - File type validation (whitelist approach)
    - File size limits
    - Filename sanitization
    - Secure storage in organized directories
    - Prevention of directory traversal attacks
    """
    
    # File type configurations
    IMAGE_TYPES = {
        "image/png": [".png"],
        "image/jpeg": [".jpg", ".jpeg"],
        "image/gif": [".gif"],
        "image/webp": [".webp"]
    }
    
    AUDIO_TYPES = {
        "audio/wav": [".wav"],
        "audio/wave": [".wav"],
        "audio/x-wav": [".wav"],
        "audio/mpeg": [".mp3"],
        "audio/mp3": [".mp3"],
        "audio/ogg": [".ogg"],
        "audio/x-m4a": [".m4a"],
        "audio/mp4": [".m4a"]
    }
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        ".exe", ".dll", ".bat", ".cmd", ".sh", ".ps1", ".vbs", 
        ".js", ".jar", ".app", ".deb", ".rpm", ".msi", ".scr"
    }
    
    # Size limits (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def __init__(self):
        """Initialize file handler and ensure upload directories exist."""
        self.upload_base = Path(getattr(config, 'UPLOAD_DIR', "uploads"))
        self.upload_base.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.upload_base / "images").mkdir(exist_ok=True)
        (self.upload_base / "audio").mkdir(exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for storage
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        # Keep only alphanumeric, dots, hyphens, underscores
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        
        # Limit length
        name_part, ext_part = os.path.splitext(filename)
        if len(name_part) > 100:
            name_part = name_part[:100]
        
        sanitized = f"{name_part}{ext_part}".lower()
        
        # If filename is empty or only extension, generate a random name
        if not name_part or len(name_part) < 1:
            sanitized = f"file_{uuid.uuid4().hex[:8]}{ext_part}"
        
        return sanitized
    
    def validate_file_type(self, file: UploadFile, file_type: FileType) -> None:
        """
        Validate file type against allowed types.
        
        Args:
            file: Uploaded file
            file_type: Expected file type (IMAGE or AUDIO)
            
        Raises:
            ValueError: If file type is not allowed
        """
        content_type = file.content_type or ""
        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Check for dangerous extensions
        if file_ext in self.DANGEROUS_EXTENSIONS:
            raise ValueError(f"File type not allowed: {file_ext}")
        
        # Validate based on file type
        if file_type == FileType.IMAGE:
            allowed_types = self.IMAGE_TYPES
        elif file_type == FileType.AUDIO:
            allowed_types = self.AUDIO_TYPES
        else:
            raise ValueError(f"Unknown file type: {file_type}")
        
        # Check content type
        if content_type not in allowed_types:
            raise ValueError(
                f"Invalid {file_type.value} type: {content_type}. "
                f"Allowed types: {', '.join(allowed_types.keys())}"
            )
        
        # Check file extension matches content type
        expected_extensions = allowed_types[content_type]
        if file_ext not in expected_extensions:
            raise ValueError(
                f"File extension {file_ext} doesn't match content type {content_type}"
            )
    
    def validate_file_size(self, file_size: int, file_type: FileType) -> None:
        """
        Validate file size against limits.
        
        Args:
            file_size: Size of file in bytes
            file_type: Type of file (IMAGE or AUDIO)
            
        Raises:
            ValueError: If file size exceeds limit
        """
        if file_type == FileType.IMAGE:
            max_size = self.MAX_IMAGE_SIZE
            max_size_mb = self.MAX_IMAGE_SIZE / (1024 * 1024)
        elif file_type == FileType.AUDIO:
            max_size = self.MAX_AUDIO_SIZE
            max_size_mb = self.MAX_AUDIO_SIZE / (1024 * 1024)
        else:
            raise ValueError(f"Unknown file type: {file_type}")
        
        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size / (1024 * 1024):.2f} MB. "
                f"Maximum allowed: {max_size_mb:.0f} MB"
            )
        
        if file_size == 0:
            raise ValueError("File is empty")
    
    async def save_upload(
        self,
        file: UploadFile,
        user_id: str,
        file_type: FileType
    ) -> Tuple[Path, str]:
        """
        Save uploaded file with validation.
        
        Args:
            file: Uploaded file
            user_id: ID of user uploading file
            file_type: Type of file (IMAGE or AUDIO)
            
        Returns:
            Tuple of (file_path, file_url)
            
        Raises:
            ValueError: If validation fails
        """
        # Validate file type
        self.validate_file_type(file, file_type)
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        self.validate_file_size(file_size, file_type)
        
        # Sanitize filename
        original_filename = file.filename or "unnamed"
        safe_filename = self.sanitize_filename(original_filename)
        
        # Generate unique filename
        unique_id = uuid.uuid4().hex[:12]
        name_part, ext_part = os.path.splitext(safe_filename)
        unique_filename = f"{user_id}_{unique_id}_{name_part}{ext_part}"
        
        # Determine subdirectory
        if file_type == FileType.IMAGE:
            subdir = "images"
        elif file_type == FileType.AUDIO:
            subdir = "audio"
        else:
            raise ValueError(f"Unknown file type: {file_type}")
        
        # Create full path
        file_path = self.upload_base / subdir / unique_filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate URL (relative path for API)
        file_url = f"/uploads/{subdir}/{unique_filename}"
        
        logger.info(
            f"File saved: {file_path} (size: {file_size} bytes, "
            f"type: {file_type.value}, user: {user_id})"
        )
        
        return file_path, file_url
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """
        Delete an uploaded file.
        
        Args:
            file_id: File identifier (filename or path)
            user_id: ID of user requesting deletion
            
        Returns:
            True if deleted, False if not found
        """
        # Search in both subdirectories
        for subdir in ["images", "audio"]:
            file_path = self.upload_base / subdir / file_id
            
            # Security check: ensure file belongs to user
            if file_path.exists() and user_id in file_path.name:
                try:
                    file_path.unlink()
                    logger.info(f"File deleted: {file_path} by user {user_id}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")
                    return False
        
        return False
    
    def get_file_path(self, file_url: str) -> Optional[Path]:
        """
        Get filesystem path from file URL.
        
        Args:
            file_url: URL path (e.g., /uploads/images/file.png)
            
        Returns:
            Path object or None if invalid
        """
        # Remove /uploads/ prefix if present
        url_path = file_url.replace("/uploads/", "")
        
        # Prevent directory traversal
        if ".." in url_path or url_path.startswith("/"):
            return None
        
        file_path = self.upload_base / url_path
        
        if file_path.exists() and file_path.is_file():
            return file_path
        
        return None
