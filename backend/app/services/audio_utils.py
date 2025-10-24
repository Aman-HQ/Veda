"""
Audio utilities for STT, TTS, and Translation.
Provides abstraction between Ollama and Bhashini API providers.
"""

import httpx
import os
import tempfile
import base64
from typing import Optional, Union
from pathlib import Path
import logging

from app.core.config import (
    AUDIO_PROVIDER,
    BHASHINI_API_KEY,
    BHASHINI_BASE_URL,
    OLLAMA_URL,
    STT_MODEL,
    TRANSLATION_MODEL,
    USE_DEV_LLM
)

logger = logging.getLogger(__name__)


class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass


async def transcribe_audio(audio_data: Union[bytes, str], language: str = "en") -> str:
    """
    Transcribe audio to text using either Ollama or Bhashini.
    
    Args:
        audio_data: Audio data as bytes or file path
        language: Language code (e.g., 'en', 'hi', 'ta')
        
    Returns:
        Transcribed text
        
    Raises:
        AudioProcessingError: If transcription fails
    """
    
    if USE_DEV_LLM:
        return await _dev_mode_transcribe(audio_data, language)
    
    try:
        if AUDIO_PROVIDER == "bhashini":
            return await _bhashini_transcribe(audio_data, language)
        else:
            return await _ollama_transcribe(audio_data, language)
    except Exception as e:
        logger.error(f"Audio transcription failed with {AUDIO_PROVIDER}: {e}")
        
        # Fallback to the other provider
        try:
            if AUDIO_PROVIDER == "bhashini":
                logger.info("Falling back to Ollama for transcription")
                return await _ollama_transcribe(audio_data, language)
            else:
                logger.info("Falling back to Bhashini for transcription")
                return await _bhashini_transcribe(audio_data, language)
        except Exception as fallback_error:
            logger.error(f"Fallback transcription also failed: {fallback_error}")
            raise AudioProcessingError(f"Both transcription providers failed: {e}, {fallback_error}")


async def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Convert text to speech using either Ollama or Bhashini.
    
    Args:
        text: Text to convert to speech
        language: Language code
        
    Returns:
        Audio data as bytes
        
    Raises:
        AudioProcessingError: If synthesis fails
    """
    
    if USE_DEV_LLM:
        return await _dev_mode_synthesize(text, language)
    
    try:
        if AUDIO_PROVIDER == "bhashini":
            return await _bhashini_synthesize(text, language)
        else:
            return await _ollama_synthesize(text, language)
    except Exception as e:
        logger.error(f"Speech synthesis failed with {AUDIO_PROVIDER}: {e}")
        
        # Fallback to the other provider
        try:
            if AUDIO_PROVIDER == "bhashini":
                logger.info("Falling back to Ollama for synthesis")
                return await _ollama_synthesize(text, language)
            else:
                logger.info("Falling back to Bhashini for synthesis")
                return await _bhashini_synthesize(text, language)
        except Exception as fallback_error:
            logger.error(f"Fallback synthesis also failed: {fallback_error}")
            raise AudioProcessingError(f"Both synthesis providers failed: {e}, {fallback_error}")


async def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text from source language to target language.
    
    Args:
        text: Text to translate
        src_lang: Source language code
        tgt_lang: Target language code
        
    Returns:
        Translated text
        
    Raises:
        AudioProcessingError: If translation fails
    """
    
    if USE_DEV_LLM:
        return await _dev_mode_translate(text, src_lang, tgt_lang)
    
    try:
        if AUDIO_PROVIDER == "bhashini":
            return await _bhashini_translate(text, src_lang, tgt_lang)
        else:
            return await _ollama_translate(text, src_lang, tgt_lang)
    except Exception as e:
        logger.error(f"Translation failed with {AUDIO_PROVIDER}: {e}")
        
        # Fallback to the other provider
        try:
            if AUDIO_PROVIDER == "bhashini":
                logger.info("Falling back to Ollama for translation")
                return await _ollama_translate(text, src_lang, tgt_lang)
            else:
                logger.info("Falling back to Bhashini for translation")
                return await _bhashini_translate(text, src_lang, tgt_lang)
        except Exception as fallback_error:
            logger.error(f"Fallback translation also failed: {fallback_error}")
            raise AudioProcessingError(f"Both translation providers failed: {e}, {fallback_error}")


# Bhashini API implementations
async def _bhashini_transcribe(audio_data: Union[bytes, str], language: str) -> str:
    """Transcribe audio using Bhashini API."""
    
    if not BHASHINI_API_KEY:
        raise AudioProcessingError("Bhashini API key not configured")
    
    url = f"{BHASHINI_BASE_URL}/asr/transcribe"
    headers = {"Authorization": f"Bearer {BHASHINI_API_KEY}"}
    
    temp_file_path = None
    # Handle both file paths and raw bytes
    if isinstance(audio_data, str):
        # File path
        files = {"file": open(audio_data, "rb")}
    else:
        # Raw bytes - create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            temp_file_path = temp_file.name
            files = {"file": open(temp_file.name, "rb")}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url, 
                files=files, 
                headers=headers,
                data={"language": language}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("text", "")
    finally:
        # Close file handles
        for file_obj in files.values():
            file_obj.close()
        # Cleanup temporary file if created
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


async def _bhashini_synthesize(text: str, language: str) -> bytes:
    """Synthesize speech using Bhashini API."""
    
    if not BHASHINI_API_KEY:
        raise AudioProcessingError("Bhashini API key not configured")
    
    url = f"{BHASHINI_BASE_URL}/tts/synthesize"
    headers = {"Authorization": f"Bearer {BHASHINI_API_KEY}"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            json={"text": text, "language": language},
            headers=headers
        )
        response.raise_for_status()
        return response.content


async def _bhashini_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Translate text using Bhashini API."""
    
    if not BHASHINI_API_KEY:
        raise AudioProcessingError("Bhashini API key not configured")
    
    url = f"{BHASHINI_BASE_URL}/translate/text"
    headers = {"Authorization": f"Bearer {BHASHINI_API_KEY}"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            json={"text": text, "source": src_lang, "target": tgt_lang},
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        return result.get("translatedText", text)


# Ollama API implementations
async def _ollama_transcribe(audio_data: Union[bytes, str], language: str) -> str:
    """Transcribe audio using Ollama Whisper model."""
    
    # For Ollama, we need to handle audio data differently
    # This is a simplified implementation - in practice, you'd need to
    # convert audio to the format Ollama expects
    
    if isinstance(audio_data, bytes):
        # Convert bytes to base64 for Ollama API
        audio_b64 = base64.b64encode(audio_data).decode()
        
        # Ollama API call for audio transcription
        payload = {
            "model": STT_MODEL,
            "prompt": f"Transcribe this audio in {language}:",
            "images": [audio_b64]  # Some Ollama models accept audio via images parameter
        }
    else:
        # File path
        payload = {
            "model": STT_MODEL,
            "prompt": f"Transcribe the audio file at {audio_data} in {language}:"
        }
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


async def _ollama_synthesize(text: str, language: str) -> bytes:
    """Synthesize speech using Ollama TTS model."""
    
    # This is a placeholder - Ollama might not have direct TTS support
    # In practice, you'd use a TTS model or return empty bytes
    
    payload = {
        "model": "mxbai-tts",  # Hypothetical TTS model
        "prompt": f"Convert this text to speech in {language}: {text}"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        # For now, return empty bytes as Ollama TTS is not standard
        return b""


async def _ollama_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Translate text using Ollama language model."""
    
    messages = [
        {
            "role": "user",
            "content": f"Translate the following text from {src_lang} to {tgt_lang}. Only return the translation, no explanations:\n\n{text}"
        }
    ]
    
    payload = {
        "model": TRANSLATION_MODEL,
        "messages": messages
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", text)


# Development mode implementations
async def _dev_mode_transcribe(audio_data: Union[bytes, str], language: str) -> str:
    """Development mode transcription with canned responses."""
    
    # Simulate processing delay
    import asyncio
    await asyncio.sleep(0.5)
    
    responses = {
        "en": "Hello, I have a question about my health symptoms.",
        "hi": "नमस्ते, मेरे स्वास्थ्य के लक्षणों के बारे में मेरा एक प्रश्न है।",
        "ta": "வணக்கம், என் உடல்நலக் குறிப்புகள் பற்றி எனக்கு ஒரு கேள்வி உள்ளது।"
    }
    
    return responses.get(language, responses["en"])


async def _dev_mode_synthesize(text: str, language: str) -> bytes:
    """Development mode speech synthesis - returns empty bytes."""
    
    import asyncio
    await asyncio.sleep(0.3)
    
    # Return empty bytes in dev mode
    return b""


async def _dev_mode_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Development mode translation with simple responses."""
    
    import asyncio
    await asyncio.sleep(0.2)
    
    # Simple translation mapping for common cases
    translations = {
        ("en", "hi"): f"[Hindi translation of: {text}]",
        ("en", "ta"): f"[Tamil translation of: {text}]",
        ("hi", "en"): f"[English translation of: {text}]",
        ("ta", "en"): f"[English translation of: {text}]"
    }
    
    return translations.get((src_lang, tgt_lang), f"[{tgt_lang} translation of: {text}]")


# Utility functions
def save_audio_to_temp_file(audio_data: bytes, suffix: str = ".wav") -> str:
    """
    Save audio bytes to a temporary file and return the path.
    
    Args:
        audio_data: Audio data as bytes
        suffix: File suffix (e.g., '.wav', '.mp3')
        
    Returns:
        Path to the temporary file
    """
    
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_file.flush()
        return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up a temporary file.
    
    Args:
        file_path: Path to the file to delete
    """
    
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")


# Audio format conversion utilities
async def convert_audio_format(
    input_data: bytes, 
    input_format: str = "mp3", 
    output_format: str = "wav",
    sample_rate: int = 16000
) -> bytes:
    """
    Convert audio from one format to another.
    This is a placeholder - in production, you'd use ffmpeg or similar.
    
    Args:
        input_data: Input audio data
        input_format: Input format (mp3, wav, etc.)
        output_format: Output format
        sample_rate: Target sample rate
        
    Returns:
        Converted audio data
    """
    
    # Placeholder implementation
    # In production, use ffmpeg-python or similar library
    logger.info(f"Converting audio from {input_format} to {output_format} at {sample_rate}Hz")
    
    # For now, return the input data unchanged
    return input_data
