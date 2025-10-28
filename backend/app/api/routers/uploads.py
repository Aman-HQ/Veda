"""
API endpoints for file uploads (images and audio).
Secure file handling with validation and size limits.
"""
import logging
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ...core import config
from ...db.session import get_db
from ...api.deps import get_current_user
from ...models.user import User
from ...services.file_handler import FileHandler, FileType

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize file handler
file_handler = FileHandler()


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an image file (PNG, JPEG, GIF, WebP).
    
    Args:
        file: Image file to upload
        conversation_id: Optional conversation ID to associate with
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict with file URL and metadata
        
    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    try:
        # Validate and save image
        file_path, file_url = await file_handler.save_upload(
            file=file,
            user_id=str(current_user.id),
            file_type=FileType.IMAGE
        )
        
        logger.info(f"Image uploaded successfully: {file_path} by user {current_user.id}")
        
        return {
            "success": True,
            "url": file_url,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "message": "Image uploaded successfully"
        }
        
    except ValueError as e:
        # Validation error (invalid type, too large, etc.)
        logger.warning(f"Image upload validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


@router.post("/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file (WAV, MP3, OGG, M4A).
    
    Args:
        file: Audio file to upload
        conversation_id: Optional conversation ID to associate with
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict with file URL, transcription if available, and metadata
        
    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    try:
        # Validate and save audio
        file_path, file_url = await file_handler.save_upload(
            file=file,
            user_id=str(current_user.id),
            file_type=FileType.AUDIO
        )
        
        logger.info(f"Audio uploaded successfully: {file_path} by user {current_user.id}")
        
        # Optional: Transcribe audio (can be done asynchronously)
        transcription = None
        # Uncomment if transcription service is available:
        # try:
        #     from ...services.audio_utils import transcribe_audio
        #     audio_bytes = file_path.read_bytes()
        #     transcription = await transcribe_audio(audio_bytes)
        # except Exception as e:
        #     logger.warning(f"Audio transcription failed: {e}")
        
        response = {
            "success": True,
            "url": file_url,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "message": "Audio uploaded successfully"
        }
        
        if transcription:
            response["transcription"] = transcription
        
        return response
        
    except ValueError as e:
        # Validation error (invalid type, too large, etc.)
        logger.warning(f"Audio upload validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload audio"
        )


@router.delete("/upload/{file_id}")
async def delete_upload(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an uploaded file.
    
    Args:
        file_id: File identifier (filename or path component)
        current_user: Current authenticated user
        
    Returns:
        dict with success status
        
    Raises:
        HTTPException: If file not found or deletion fails
    """
    try:
        success = await file_handler.delete_file(file_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or already deleted"
            )
        
        logger.info(f"File deleted: {file_id} by user {current_user.id}")
        
        return {
            "success": True,
            "message": "File deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
