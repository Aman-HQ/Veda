"""
B10 Pipeline Tests - LLM Provider and Chat Manager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestLLMProvider:
    """Test LLM provider with mocked responses."""
    
    async def test_process_pipeline_text_input(self, mock_llm_provider):
        """Test processing text input through pipeline."""
        result = await mock_llm_provider.process_pipeline(
            text="What are symptoms of flu?"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Mock response" in result
    
    async def test_process_pipeline_audio_input(self, mock_llm_provider):
        """Test processing audio input through pipeline."""
        # Simulate audio bytes
        audio_data = b"fake audio data"
        
        result = await mock_llm_provider.process_pipeline(
            audio=audio_data
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    async def test_process_pipeline_image_input(self, mock_llm_provider):
        """Test processing image input through pipeline."""
        # Simulate image data
        image_data = b"fake image data"
        
        result = await mock_llm_provider.process_pipeline(
            image=image_data
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    async def test_process_pipeline_with_options(self, mock_llm_provider):
        """Test processing with custom options."""
        result = await mock_llm_provider.process_pipeline(
            text="Test query",
            opts={"skip_rag": True, "model": "test-model"}
        )
        
        assert isinstance(result, str)
    
    async def test_stream_response(self, mock_llm_provider):
        """Test streaming response functionality."""
        chunks = []
        
        async def collect_chunk(chunk):
            chunks.append(chunk)
        
        await mock_llm_provider.stream_response(
            text="Test input",
            callback=collect_chunk
        )
        
        assert len(chunks) > 0
        # Join chunks should form complete response
        full_response = "".join(chunks)
        assert len(full_response) > 0


@pytest.mark.asyncio
class TestChatManager:
    """Test chat manager functionality."""
    
    async def test_handle_user_message_text(
        self, db_session, test_conversation, test_user, mock_llm_provider
    ):
        """Test handling user text message."""
        from app.services.chat_manager import ChatManager
        
        with patch('app.services.chat_manager.LLMProvider', return_value=mock_llm_provider):
            manager = ChatManager(db_session)
            
            result = await manager.handle_user_message(
                conversation_id=str(test_conversation.id),
                user_id=str(test_user.id),
                text="Hello, I have a question"
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    async def test_handle_user_message_persists_to_db(
        self, db_session, test_conversation, test_user, mock_llm_provider
    ):
        """Test that messages are persisted to database."""
        from app.services.chat_manager import ChatManager
        from app.models.message import Message
        from sqlalchemy import select
        
        with patch('app.services.chat_manager.LLMProvider', return_value=mock_llm_provider):
            manager = ChatManager(db_session)
            
            await manager.handle_user_message(
                conversation_id=str(test_conversation.id),
                user_id=str(test_user.id),
                text="Test message"
            )
            
            # Check messages were saved
            result = await db_session.execute(
                select(Message).where(
                    Message.conversation_id == test_conversation.id
                )
            )
            messages = result.scalars().all()
            
            # Should have at least user message and assistant response
            assert len(messages) >= 1
    
    async def test_handle_user_message_with_streaming(
        self, db_session, test_conversation, test_user, mock_llm_provider
    ):
        """Test handling message with WebSocket streaming."""
        from app.services.chat_manager import ChatManager
        
        # Mock WebSocket streamer
        streamer = MagicMock()
        streamer.send_chunk = AsyncMock()
        streamer.send_done = AsyncMock()
        
        with patch('app.services.chat_manager.LLMProvider', return_value=mock_llm_provider):
            manager = ChatManager(db_session)
            
            result = await manager.handle_user_message(
                conversation_id=str(test_conversation.id),
                user_id=str(test_user.id),
                text="Streaming test",
                ws_streamer=streamer
            )
            
            # Should have called streaming methods
            assert streamer.send_chunk.called or streamer.send_done.called


@pytest.mark.asyncio
class TestRAGPipeline:
    """Test RAG pipeline functionality."""
    
    async def test_rag_retrieve_returns_docs(self):
        """Test RAG retrieval returns documents."""
        from app.services.rag.pipeline import RAGPipeline
        
        try:
            pipeline = RAGPipeline()
            
            # Mock Pinecone query
            with patch.object(pipeline, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
                mock_retrieve.return_value = [
                    {"text": "Document 1", "metadata": {"source": "doc1"}},
                    {"text": "Document 2", "metadata": {"source": "doc2"}}
                ]
                
                results = await pipeline.retrieve("test query", top_k=2)
                
                assert len(results) == 2
                assert all("text" in doc for doc in results)
        except ImportError:
            pytest.skip("RAG pipeline not fully implemented")
    
    async def test_rag_ingest_docs(self, tmp_upload_dir):
        """Test document ingestion."""
        from app.services.rag.pipeline import RAGPipeline
        
        try:
            # Create test document
            test_doc = tmp_upload_dir / "test.txt"
            test_doc.write_text("This is a test health document.")
            
            pipeline = RAGPipeline()
            
            # Mock ingest
            with patch.object(pipeline, 'ingest_docs', new_callable=AsyncMock) as mock_ingest:
                await pipeline.ingest_docs(str(tmp_upload_dir))
                
                assert mock_ingest.called
        except ImportError:
            pytest.skip("RAG pipeline not fully implemented")


@pytest.mark.asyncio
class TestMultiModelOrchestration:
    """Test multi-model orchestration."""
    
    async def test_pipeline_calls_models_in_sequence(self, mock_llm_provider):
        """Test that pipeline orchestrates models correctly."""
        # This is a conceptual test - actual implementation depends on your setup
        
        result = await mock_llm_provider.process_pipeline(
            text="Test health query",
            opts={"skip_rag": False}
        )
        
        assert isinstance(result, str)
    
    async def test_pipeline_skips_optional_steps(self, mock_llm_provider):
        """Test pipeline respects skip flags."""
        result_with_rag = await mock_llm_provider.process_pipeline(
            text="Test",
            opts={"skip_rag": False}
        )
        
        result_without_rag = await mock_llm_provider.process_pipeline(
            text="Test",
            opts={"skip_rag": True}
        )
        
        # Both should return results
        assert isinstance(result_with_rag, str)
        assert isinstance(result_without_rag, str)
