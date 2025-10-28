"""
Tests for B07.5 - Multi-Model Orchestration (LLM Pipeline).
Tests the full pipeline including STT, RAG, LLM orchestration, and audio utils.
"""

import pytest
import asyncio
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from app.services.llm_provider import LLMProvider
from app.services.rag.pipeline import RAGPipeline
from app.services.audio_utils import (
    transcribe_audio, 
    translate_text, 
    synthesize_speech,
    AudioProcessingError
)


class TestAudioUtils:
    """Test audio utilities for STT, TTS, and translation."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_dev_mode(self):
        """Test audio transcription in development mode."""
        
        # Create fake audio data
        fake_audio = b"fake_audio_data"
        
        # Test transcription
        result = await transcribe_audio(fake_audio, "en")
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "health" in result.lower() or "question" in result.lower()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_different_languages(self):
        """Test audio transcription with different languages."""
        
        fake_audio = b"fake_audio_data"
        
        # Test English
        result_en = await transcribe_audio(fake_audio, "en")
        assert isinstance(result_en, str)
        
        # Test Hindi
        result_hi = await transcribe_audio(fake_audio, "hi")
        assert isinstance(result_hi, str)
        
        # Test Tamil
        result_ta = await transcribe_audio(fake_audio, "ta")
        assert isinstance(result_ta, str)
    
    @pytest.mark.asyncio
    async def test_translate_text_dev_mode(self):
        """Test text translation in development mode."""
        
        text = "Hello, I have a health question"
        
        # Test English to Hindi
        result = await translate_text(text, "en", "hi")
        assert isinstance(result, str)
        assert "Hindi translation" in result or text in result
        
        # Test English to Tamil
        result = await translate_text(text, "en", "ta")
        assert isinstance(result, str)
        assert "Tamil translation" in result or text in result
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_dev_mode(self):
        """Test speech synthesis in development mode."""
        
        text = "This is a test message"
        
        result = await synthesize_speech(text, "en")
        assert isinstance(result, bytes)
        # In dev mode, returns empty bytes
        assert result == b""
    
    @pytest.mark.asyncio
    async def test_audio_error_handling(self):
        """Test audio processing error handling."""
        
        with patch('app.services.audio_utils.USE_DEV_LLM', False):
            with patch('app.services.audio_utils.AUDIO_PROVIDER', 'invalid_provider'):
                with pytest.raises(AudioProcessingError):
                    await transcribe_audio(b"invalid", "en")

class TestRAGPipeline:
    """Test RAG pipeline functionality."""
    
    @pytest.fixture
    def rag_pipeline(self):
        """Create RAG pipeline instance."""
        return RAGPipeline()
    
    @pytest.mark.asyncio
    async def test_rag_initialization(self, rag_pipeline):
        """Test RAG pipeline initialization."""
        
        assert rag_pipeline is not None
        assert hasattr(rag_pipeline, 'use_dev_mode')
        assert hasattr(rag_pipeline, 'vectorstore')
    
    @pytest.mark.asyncio
    async def test_rag_retrieve_dev_mode(self, rag_pipeline):
        """Test document retrieval in development mode."""
        
        query = "headache symptoms"
        results = await rag_pipeline.retrieve(query, top_k=3)
        
        assert isinstance(results, list)
        assert len(results) <= 3
        
        if results:
            for result in results:
                assert "text" in result
                assert "metadata" in result
                assert isinstance(result["text"], str)
    
    @pytest.mark.asyncio
    async def test_rag_search_by_topic(self, rag_pipeline):
        """Test topic-based search."""
        
        topics = ["headache", "fever", "diabetes", "hypertension"]
        
        for topic in topics:
            results = await rag_pipeline.search_by_topic(topic, top_k=2)
            assert isinstance(results, list)
            assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_rag_health_check(self, rag_pipeline):
        """Test RAG pipeline health check."""
        
        health = await rag_pipeline.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
        assert "mode" in health
    
    def test_rag_get_stats(self, rag_pipeline):
        """Test RAG pipeline statistics."""
        
        stats = rag_pipeline.get_stats()
        
        assert isinstance(stats, dict)
        assert "mode" in stats
        assert "embedding_model" in stats
        assert "chunk_size" in stats
        assert "chunk_overlap" in stats


class TestLLMProvider:
    """Test LLM Provider with multi-model orchestration."""
    
    @pytest.fixture
    def llm_provider(self):
        """Create LLM provider instance."""
        return LLMProvider(use_dev_mode=True)
    
    @pytest.mark.asyncio
    async def test_llm_provider_initialization(self, llm_provider):
        """Test LLM provider initialization."""
        
        assert llm_provider is not None
        assert llm_provider.use_dev_mode is True
        assert hasattr(llm_provider, 'rag')
        assert hasattr(llm_provider, 'disclaimer')
        assert "⚠️" in llm_provider.disclaimer
    
    @pytest.mark.asyncio
    async def test_text_only_pipeline(self, llm_provider):
        """Test pipeline with text input only."""
        
        text = "I have a headache and feel dizzy"
        result = await llm_provider.process_pipeline(text=text)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "⚠️" in result  # Disclaimer included
        assert "medical" in result.lower() or "healthcare" in result.lower()
    
    @pytest.mark.asyncio
    async def test_audio_pipeline(self, llm_provider):
        """Test pipeline with audio input."""
        
        fake_audio = b"fake_audio_data"
        result = await llm_provider.process_pipeline(audio=fake_audio)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "⚠️" in result  # Disclaimer included
    
    @pytest.mark.asyncio
    async def test_image_pipeline(self, llm_provider):
        """Test pipeline with image input."""
        
        fake_image = b"fake_image_data"
        result = await llm_provider.process_pipeline(image=fake_image)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "⚠️" in result  # Disclaimer included
    
    @pytest.mark.asyncio
    async def test_multimodal_pipeline(self, llm_provider):
        """Test pipeline with multiple input types."""
        
        text = "I have symptoms"
        fake_audio = b"fake_audio_data"
        fake_image = b"fake_image_data"
        
        result = await llm_provider.process_pipeline(
            text=text,
            audio=fake_audio,
            image=fake_image
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "⚠️" in result  # Disclaimer included
    
    @pytest.mark.asyncio
    async def test_pipeline_with_options(self, llm_provider):
        """Test pipeline with various options."""
        
        text = "I have a long medical history with multiple symptoms and conditions that need to be addressed"
        
        # Test with summarizer skipped
        result1 = await llm_provider.process_pipeline(
            text=text,
            opts={"skip_summarizer": True}
        )
        assert isinstance(result1, str)
        
        # Test with RAG skipped
        result2 = await llm_provider.process_pipeline(
            text=text,
            opts={"skip_rag": True}
        )
        assert isinstance(result2, str)
        
        # Test with both skipped
        result3 = await llm_provider.process_pipeline(
            text=text,
            opts={"skip_summarizer": True, "skip_rag": True}
        )
        assert isinstance(result3, str)
    
    @pytest.mark.asyncio
    async def test_streaming_pipeline(self, llm_provider):
        """Test streaming pipeline."""
        
        text = "I have health concerns"
        chunks = []
        
        async for chunk in llm_provider.process_pipeline_stream(text=text):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "⚠️" in full_response  # Disclaimer included
    
    @pytest.mark.asyncio
    async def test_streaming_with_audio(self, llm_provider):
        """Test streaming pipeline with audio."""
        
        fake_audio = b"fake_audio_data"
        chunks = []
        
        async for chunk in llm_provider.process_pipeline_stream(audio=fake_audio):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "⚠️" in full_response
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, llm_provider):
        """Test pipeline error handling."""
        
        # Test with no input
        result = await llm_provider.process_pipeline()
        assert isinstance(result, str)
        assert "error" in result.lower() or "apologize" in result.lower()
        assert "⚠️" in result
    
    @pytest.mark.asyncio
    async def test_pipeline_stats(self, llm_provider):
        """Test pipeline statistics."""
        
        stats = await llm_provider.get_pipeline_stats()
        
        assert isinstance(stats, dict)
        assert "mode" in stats
        assert "models" in stats
        assert "flags" in stats
        assert stats["mode"] == "development"
    
    @pytest.mark.asyncio
    async def test_pipeline_health_check(self, llm_provider):
        """Test pipeline health check."""
        
        health = await llm_provider.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "components" in health
        assert health["status"] in ["healthy", "degraded"]


class TestPipelineIntegration:
    """Test integration between pipeline components."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self):
        """Test complete pipeline flow from input to output."""
        
        # Initialize components
        llm_provider = LLMProvider(use_dev_mode=True)
        
        # Test various input combinations
        test_cases = [
            {"text": "I have a headache"},
            {"audio": b"fake_audio", "language": "en"},
            {"image": b"fake_image"},
            {"text": "symptoms", "audio": b"audio", "image": b"image"}
        ]
        
        for case in test_cases:
            result = await llm_provider.process_pipeline(**case)
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "⚠️" in result
            
            # Test streaming version
            chunks = []
            async for chunk in llm_provider.process_pipeline_stream(**case):
                chunks.append(chunk)
            
            assert len(chunks) > 0
            full_streaming_result = "".join(chunks)
            assert "⚠️" in full_streaming_result
    
    @pytest.mark.asyncio
    async def test_rag_integration(self):
        """Test RAG integration with LLM provider."""
        
        llm_provider = LLMProvider(use_dev_mode=True)
        
        # Test that RAG is initialized
        assert llm_provider.rag is not None
        
        # Test retrieval through pipeline
        result = await llm_provider.process_pipeline(
            text="What are the symptoms of diabetes?",
            opts={"skip_rag": False}
        )
        
        assert isinstance(result, str)
        assert "⚠️" in result
    
    @pytest.mark.asyncio
    async def test_audio_integration(self):
        """Test audio processing integration."""
        
        llm_provider = LLMProvider(use_dev_mode=True)
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            temp_file.write(b"fake_audio_data")
            temp_file.flush()
            
            # Test with file path
            result = await transcribe_audio(temp_file.name, "en")
            assert isinstance(result, str)
        
        # Test with raw bytes
        result = await transcribe_audio(b"fake_audio_data", "en")
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self):
        """Test multilingual support across components."""
        
        languages = ["en", "hi", "ta"]
        
        for lang in languages:
            # Test audio transcription
            result = await transcribe_audio(b"fake_audio", lang)
            assert isinstance(result, str)
            
            # Test translation
            translated = await translate_text("Hello", "en", lang)
            assert isinstance(translated, str)
            
            # Test pipeline with language
            llm_provider = LLMProvider(use_dev_mode=True)
            pipeline_result = await llm_provider.process_pipeline(
                audio=b"fake_audio",
                language=lang
            )
            assert isinstance(pipeline_result, str)
            assert "⚠️" in pipeline_result


class TestConfigurationFlags:
    """Test configuration flags and their effects."""
    
    @pytest.mark.asyncio
    async def test_skip_flags(self):
        """Test skip flags for pipeline components."""
        
        llm_provider = LLMProvider(use_dev_mode=True)
        text = "This is a long medical query that would normally be summarized"
        
        # Test skip summarizer
        result1 = await llm_provider.process_pipeline(
            text=text,
            opts={"skip_summarizer": True}
        )
        assert isinstance(result1, str)
        
        # Test skip RAG
        result2 = await llm_provider.process_pipeline(
            text=text,
            opts={"skip_rag": True}
        )
        assert isinstance(result2, str)
    
    @pytest.mark.asyncio
    async def test_dev_mode_vs_production_mode(self):
        """Test differences between dev and production modes."""
        
        # Dev mode provider
        dev_provider = LLMProvider(use_dev_mode=True)
        assert dev_provider.use_dev_mode is True
        
        # Production mode provider (but will fallback to dev due to missing Ollama)
        prod_provider = LLMProvider(use_dev_mode=False)
        # Note: In test environment, this will likely fallback to dev mode
        
        # Both should work
        text = "Test medical query"
        
        dev_result = await dev_provider.process_pipeline(text=text)
        prod_result = await prod_provider.process_pipeline(text=text)
        
        assert isinstance(dev_result, str)
        assert isinstance(prod_result, str)
        assert "⚠️" in dev_result
        assert "⚠️" in prod_result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
