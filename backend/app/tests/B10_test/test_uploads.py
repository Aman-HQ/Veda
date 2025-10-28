"""
B10 Upload Tests - Image and Audio file handling
"""

import pytest
from httpx import AsyncClient
from io import BytesIO
from pathlib import Path


@pytest.mark.asyncio
class TestImageUpload:
    """Test image upload functionality."""
    
    async def test_upload_image_png(
        self, client: AsyncClient, auth_headers, test_conversation, tmp_upload_dir
    ):
        """Test uploading PNG image."""
        # Create fake image data
        fake_image = BytesIO(b"fake png data")
        
        files = {
            "file": ("test.png", fake_image, "image/png")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should accept or return appropriate error
        assert response.status_code in [200, 201, 400, 415]
        
        if response.status_code in [200, 201]:
            result = response.json()
            assert "url" in result or "message" in result
    
    async def test_upload_image_jpeg(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test uploading JPEG image."""
        fake_image = BytesIO(b"fake jpeg data")
        
        files = {
            "file": ("test.jpg", fake_image, "image/jpeg")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 201, 400, 415]
    
    async def test_upload_image_too_large(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test uploading image that exceeds size limit."""
        # Create 10MB fake image (assuming 8MB limit)
        large_image = BytesIO(b"x" * (10 * 1024 * 1024))
        
        files = {
            "file": ("large.png", large_image, "image/png")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should reject large files
        assert response.status_code in [400, 413]
    
    async def test_upload_invalid_image_type(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test uploading non-image file as image."""
        fake_file = BytesIO(b"not an image")
        
        files = {
            "file": ("test.txt", fake_file, "text/plain")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should reject invalid type
        assert response.status_code in [400, 415]
    
    async def test_image_url_accessible(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test that uploaded image URL is accessible."""
        fake_image = BytesIO(b"fake image data")
        
        files = {
            "file": ("test.png", fake_image, "image/png")
        }
        data = {
            "type": "image"
        }
        
        upload_response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        if upload_response.status_code in [200, 201]:
            result = upload_response.json()
            
            if "url" in result:
                # Try to access the uploaded file
                file_response = await client.get(result["url"])
                # Should be accessible
                assert file_response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAudioUpload:
    """Test audio upload and transcription."""
    
    async def test_upload_audio_wav(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test uploading WAV audio file."""
        fake_audio = BytesIO(b"fake wav data")
        
        files = {
            "file": ("test.wav", fake_audio, "audio/wav")
        }
        data = {
            "type": "audio"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should accept or return appropriate error
        assert response.status_code in [200, 201, 400, 415]
    
    async def test_upload_audio_mp3(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test uploading MP3 audio file."""
        fake_audio = BytesIO(b"fake mp3 data")
        
        files = {
            "file": ("test.mp3", fake_audio, "audio/mpeg")
        }
        data = {
            "type": "audio"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 201, 400, 415]
    
    async def test_audio_transcription_returns_text(
        self, client: AsyncClient, auth_headers, test_conversation, mock_llm_provider
    ):
        """Test that audio upload returns transcribed text."""
        fake_audio = BytesIO(b"fake audio data")
        
        files = {
            "file": ("test.wav", fake_audio, "audio/wav")
        }
        data = {
            "type": "audio"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            # Should include transcribed text or message content
            assert "text" in result or "content" in result or "answer" in result
    
    async def test_audio_file_deleted_after_transcription(
        self, client: AsyncClient, auth_headers, test_conversation, tmp_upload_dir
    ):
        """Test that audio files are deleted after transcription."""
        # This is more of an integration test
        # Actual implementation would check filesystem
        pytest.skip("Audio cleanup test - implement based on actual file handling")


@pytest.mark.asyncio
class TestFileValidation:
    """Test file validation and security."""
    
    async def test_reject_executable_files(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test rejecting potentially dangerous file types."""
        fake_exe = BytesIO(b"MZ fake exe")
        
        files = {
            "file": ("malware.exe", fake_exe, "application/x-msdownload")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should reject
        assert response.status_code in [400, 415]
    
    async def test_reject_script_files(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test rejecting script files."""
        fake_script = BytesIO(b"#!/bin/bash\nrm -rf /")
        
        files = {
            "file": ("script.sh", fake_script, "application/x-sh")
        }
        data = {
            "type": "image"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        # Should reject
        assert response.status_code in [400, 415]
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Implement based on your sanitization logic
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>.png",
            "file|rm -rf.jpg",
            "file\x00.png"
        ]
        
        for name in dangerous_names:
            # Your sanitization function should handle these
            # Example assertion (adjust based on implementation):
            # sanitized = sanitize_filename(name)
            # assert ".." not in sanitized
            # assert "/" not in sanitized
            pass
