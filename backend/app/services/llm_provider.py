"""
LLM Provider service for Veda Healthcare Chatbot.
Orchestrates multiple specialized models using Ollama as the unified model host.
Supports multi-modal input (text, audio, image) and RAG integration.
"""

import os
import asyncio
import httpx
import tempfile
from typing import Optional, List, Dict, AsyncGenerator, Union, Any
from pathlib import Path

from app.core.config import (
    OLLAMA_URL, OLLAMA_API_KEY, LLM_PROVIDER, DEBUG,
    STT_MODEL, SUMMARIZER_MODEL, MAIN_MODEL, TRANSLATION_MODEL,
    SKIP_SUMMARIZER, SKIP_RAG, USE_DEV_LLM
)
from .rag.pipeline import RAGPipeline
from .audio_utils import transcribe_audio, translate_text
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_URL, api_key: Optional[str] = None):
        self.base = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.timeout = 60

    async def chat(self, model: str, messages: List[Dict], timeout: int = 60) -> Dict:
        """
        Send a chat request to Ollama API.
        
        Args:
            model: Model name (e.g., 'llama-3.2', 'medgemma-4b-it')
            messages: List of message objects with role and content
            timeout: Request timeout in seconds
            
        Returns:
            Response from Ollama API
        """
        url = f"{self.base}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def chat_stream(self, model: str, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Ollama API.
        
        Args:
            model: Model name
            messages: List of message objects
            
        Yields:
            Chunks of the response text
        """
        url = f"{self.base}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", url, json=payload, headers=self.headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                import json
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    content = data["message"]["content"]
                                    if content:
                                        yield content
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise


class LLMProvider:
    """
    Main LLM provider that orchestrates the AI pipeline.
    Supports multi-modal input, RAG integration, and both development/production modes.
    
    Pipeline flow:
    1. Audio → STT (Whisper/Bhashini) → Text
    2. Image → Vision Model → Description → Text
    3. Text → Summarizer (optional) → Summary
    4. Summary → RAG Retrieval → Context Documents
    5. Context + Summary → Main Model → Final Response
    """
    
    def __init__(self, use_dev_mode: bool = None):
        self.use_dev_mode = use_dev_mode if use_dev_mode is not None else USE_DEV_LLM
        self.client = OllamaClient() if not self.use_dev_mode else None
        
        # Initialize RAG pipeline
        try:
            self.rag = RAGPipeline()
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.rag = None
        
        # Healthcare disclaimer to append to all assistant messages
        self.disclaimer = ("\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only "
                          "and should not replace professional medical advice. Please consult with a "
                          "healthcare provider for medical concerns.")

    async def process_pipeline(
        self, 
        audio: Optional[bytes] = None, 
        image: Optional[bytes] = None,
        text: Optional[str] = None, 
        opts: Optional[Dict] = None,
        language: str = "en"
    ) -> str:
        """
        Process input through the full AI pipeline.
        
        Pipeline: Audio/Image → Text → Summarizer → RAG → Main Model → Response
        
        Args:
            audio: Audio data for transcription
            image: Image data for analysis
            text: Text input
            opts: Additional options (skip_summarizer, skip_rag, etc.)
            language: Language code for audio processing
            
        Returns:
            Final response text with disclaimer
        """
        opts = opts or {}
        
        if self.use_dev_mode:
            return await self._dev_mode_response(text, audio, image, language)
        
        try:
            # Step 1: Process audio input (STT)
            if audio:
                logger.info("Processing audio input...")
                transcribed_text = await self._process_audio_input(audio, language)
                text = self._combine_text_inputs(text, transcribed_text)
            
            # Step 2: Process image input (Vision)
            if image:
                logger.info("Processing image input...")
                image_description = await self._process_image_input(image)
                text = self._combine_text_inputs(text, image_description)
            
            if not text:
                raise ValueError("No text provided for processing")
            
            # Step 3: Text summarization (optional)
            summary = await self._summarize_text(text, opts)
            
            # Step 4: RAG retrieval
            context_docs = await self._retrieve_context(summary, opts)
            
            # Step 5: Generate final response
            final_response = await self._generate_final_response(summary, context_docs, opts)
            
            # Step 6: Add healthcare disclaimer
            return final_response + self.disclaimer
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return await self._handle_pipeline_error(e)
    
    async def _process_audio_input(self, audio: bytes, language: str) -> str:
        """Process audio input through STT."""
        try:
            # Save audio to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio)
                temp_file.flush()
                temp_path = temp_file.name
            
            try:
                # Transcribe audio
                transcribed_text = await transcribe_audio(temp_path, language)
                logger.info(f"Audio transcribed successfully: {transcribed_text[:100]}...")
                return transcribed_text
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return "[Audio transcription failed]"
    
    async def _process_image_input(self, image: bytes) -> str:
        """Process image input through vision model."""
        try:
            if self.use_dev_mode:
                return "Image analysis: The image appears to show medical-related content or symptoms."
            
            # For production, use Ollama vision model (llava, bakllava)
            # Convert image to base64 for Ollama API
            import base64
            image_b64 = base64.b64encode(image).decode()
            
            messages = [
                {
                    "role": "user",
                    "content": "Analyze this medical image and describe what you see. Focus on any visible symptoms, conditions, or medical relevance.",
                    "images": [image_b64]
                }
            ]
            
            # Use vision-capable model
            resp = await self.client.chat("llava", messages)
            description = resp.get("message", {}).get("content", "Image analysis unavailable")
            
            logger.info(f"Image analyzed successfully: {description[:100]}...")
            return f"Image analysis: {description}"
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return "Image analysis: Unable to process the provided image."
    
    def _combine_text_inputs(self, existing_text: Optional[str], new_text: str) -> str:
        """Combine multiple text inputs."""
        if not existing_text:
            return new_text
        return f"{existing_text}\n\n{new_text}"
    
    async def _summarize_text(self, text: str, opts: Dict) -> str:
        """Summarize text using language model (optional step)."""
        
        # Skip summarization if requested or text is short
        if opts.get("skip_summarizer", SKIP_SUMMARIZER) or len(text) < 500:
            return text
        
        try:
            if self.use_dev_mode:
                # Simple truncation for dev mode
                return text[:500] + "..." if len(text) > 500 else text
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a medical text summarizer. Summarize the following medical query or information concisely while preserving all important medical details."
                },
                {
                    "role": "user",
                    "content": f"Summarize this medical text:\n\n{text}"
                }
            ]
            
            resp = await self.client.chat(SUMMARIZER_MODEL, messages)
            summary = resp.get("message", {}).get("content", text)
            
            logger.info("Text summarized successfully")
            return summary
            
        except Exception as e:
            logger.warning(f"Text summarization failed: {e}, using original text")
            return text
    
    async def _retrieve_context(self, query: str, opts: Dict) -> List[str]:
        """Retrieve relevant context documents using RAG."""
        
        if opts.get("skip_rag", SKIP_RAG) or not self.rag:
            return []
        
        try:
            # Retrieve relevant documents
            docs = await self.rag.retrieve(query, top_k=5)
            
            # Extract text content
            context_texts = []
            for doc in docs:
                context_texts.append(doc["text"])
            
            logger.info(f"Retrieved {len(context_texts)} context documents")
            return context_texts
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []
    
    async def _generate_final_response(self, query: str, context_docs: List[str], opts: Dict) -> str:
        """Generate final response using main language model."""
        
        try:
            # Build prompt with context
            if context_docs:
                context = "\n\n".join(context_docs)
                prompt = f"""Context Information:
{context}

Patient Query: {query}

Based on the context information above and your medical knowledge, provide a helpful, accurate response to the patient's query. Always emphasize the importance of consulting with healthcare professionals for proper diagnosis and treatment."""
            else:
                prompt = f"""Patient Query: {query}

Provide a helpful, accurate response to this medical query. Always emphasize the importance of consulting with healthcare professionals for proper diagnosis and treatment."""
            
            if self.use_dev_mode:
                return await self._dev_mode_final_response(query, context_docs)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are Veda, a helpful medical AI assistant. Provide accurate, compassionate, and informative responses while always emphasizing the importance of professional medical consultation. Never provide specific diagnoses or treatment recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            resp = await self.client.chat(MAIN_MODEL, messages)
            response = resp.get("message", {}).get("content", "I apologize, but I'm unable to process your request at the moment.")
            
            logger.info("Final response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later or consult with a healthcare professional."
    
    async def _handle_pipeline_error(self, error: Exception) -> str:
        """Handle pipeline errors gracefully."""
        error_msg = "I apologize, but I encountered an error while processing your request. "
        
        if "audio" in str(error).lower():
            error_msg += "There was an issue processing your audio input. "
        elif "image" in str(error).lower():
            error_msg += "There was an issue processing your image input. "
        
        error_msg += "Please try again or consult with a healthcare professional for assistance."
        
        return error_msg + self.disclaimer

    async def process_pipeline_stream(
        self,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None,
        text: Optional[str] = None,
        opts: Optional[Dict] = None,
        language: str = "en"
    ) -> AsyncGenerator[str, None]:
        """
        Process input through the AI pipeline with streaming response.
        
        Args:
            audio: Audio data for transcription
            image: Image data for analysis  
            text: Text input
            opts: Additional options
            language: Language code for audio processing
            
        Yields:
            Chunks of the response text
        """
        opts = opts or {}
        
        if self.use_dev_mode:
            async for chunk in self._dev_mode_stream(text, audio, image, language):
                yield chunk
            return

        try:
            # Step 1: Process audio input (STT)
            if audio:
                transcribed_text = await self._process_audio_input(audio, language)
                text = self._combine_text_inputs(text, transcribed_text)
            
            # Step 2: Process image input (Vision)
            if image:
                image_description = await self._process_image_input(image)
                text = self._combine_text_inputs(text, image_description)
            
            if not text:
                raise ValueError("No text provided for processing")
            
            # Step 3: Text summarization (optional)
            summary = await self._summarize_text(text, opts)
            
            # Step 4: RAG retrieval
            context_docs = await self._retrieve_context(summary, opts)
            
            # Step 5: Stream final response
            async for chunk in self._stream_final_response(summary, context_docs, opts):
                yield chunk
                
            # Step 6: Add disclaimer at the end
            yield self.disclaimer
            
        except Exception as e:
            logger.error(f"Streaming pipeline processing failed: {e}")
            yield "I apologize, but I encountered an error while processing your request. Please try again or consult with a healthcare professional."
            yield self.disclaimer
    
    async def _stream_final_response(self, query: str, context_docs: List[str], opts: Dict) -> AsyncGenerator[str, None]:
        """Stream final response using main language model."""
        
        try:
            # Build prompt with context
            if context_docs:
                context = "\n\n".join(context_docs)
                prompt = f"""Context Information:
{context}

Patient Query: {query}

Based on the context information above and your medical knowledge, provide a helpful, accurate response to the patient's query. Always emphasize the importance of consulting with healthcare professionals for proper diagnosis and treatment."""
            else:
                prompt = f"""Patient Query: {query}

Provide a helpful, accurate response to this medical query. Always emphasize the importance of consulting with healthcare professionals for proper diagnosis and treatment."""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are Veda, a helpful medical AI assistant. Provide accurate, compassionate, and informative responses while always emphasizing the importance of professional medical consultation. Never provide specific diagnoses or treatment recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Stream the response
            async for chunk in self.client.chat_stream(MAIN_MODEL, messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming final response failed: {e}")
            yield "I apologize, but I'm experiencing technical difficulties. Please try again later or consult with a healthcare professional."

    async def _dev_mode_response(self, text: Optional[str], audio: Optional[bytes], image: Optional[bytes], language: str = "en") -> str:
        """Generate canned response for development mode."""
        
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        # Process inputs in dev mode
        processed_text = text or ""
        
        if audio:
            # Simulate audio transcription
            from .audio_utils import _dev_mode_transcribe
            transcribed = await _dev_mode_transcribe(audio, language)
            processed_text = self._combine_text_inputs(processed_text, f"[Transcribed]: {transcribed}")
        
        if image:
            # Simulate image analysis
            processed_text = self._combine_text_inputs(processed_text, "[Image Analysis]: Medical-related image detected")
        
        # Generate contextual response based on content
        response = await self._dev_mode_final_response(processed_text, [])
        return response + self.disclaimer
    
    async def _dev_mode_final_response(self, query: str, context_docs: List[str]) -> str:
        """Generate final response in development mode."""
        
        # Simulate processing delay
        await asyncio.sleep(0.3)
        
        responses = [
            "Thank you for your health question. Based on your symptoms, I recommend consulting with a healthcare professional for proper evaluation.",
            "I understand your concern. While I can provide general information, it's important to speak with a doctor who can examine you properly.",
            "Your symptoms could have various causes. A healthcare provider would be the best person to give you an accurate diagnosis and treatment plan.",
            "I appreciate you sharing your health concerns with me. For the most accurate advice, please consider scheduling an appointment with your doctor.",
            "Based on what you've described, there are several possibilities. A medical professional can help determine the best course of action for your situation."
        ]
        
        # Simple hash-based selection for consistent responses
        import hashlib
        query_hash = hashlib.md5((query or "default").encode()).hexdigest()
        response_index = int(query_hash[:2], 16) % len(responses)
        
        base_response = responses[response_index]
        
        # Add context information if available
        if context_docs:
            base_response = f"Based on the available medical information, {base_response.lower()}"
        
        return base_response

    async def _dev_mode_stream(self, text: Optional[str], audio: Optional[bytes], image: Optional[bytes], language: str = "en") -> AsyncGenerator[str, None]:
        """Generate streaming canned response for development mode."""
        
        full_response = await self._dev_mode_response(text, audio, image, language)
        
        # Split response into chunks and stream with delay
        words = full_response.split()
        current_chunk = ""
        
        for i, word in enumerate(words):
            current_chunk += word + " "
            
            # Send chunk every 3-5 words
            if (i + 1) % 4 == 0 or i == len(words) - 1:
                yield current_chunk.strip()
                current_chunk = ""
                await asyncio.sleep(0.1)  # Small delay between chunks
    
    # Additional utility methods for pipeline management
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline components."""
        
        stats = {
            "mode": "development" if self.use_dev_mode else "production",
            "ollama_url": OLLAMA_URL,
            "models": {
                "stt": STT_MODEL,
                "summarizer": SUMMARIZER_MODEL,
                "main": MAIN_MODEL,
                "translation": TRANSLATION_MODEL
            },
            "flags": {
                "skip_summarizer": SKIP_SUMMARIZER,
                "skip_rag": SKIP_RAG,
                "use_dev_llm": USE_DEV_LLM
            }
        }
        
        # Add RAG stats if available
        if self.rag:
            try:
                rag_stats = self.rag.get_stats()
                stats["rag"] = rag_stats
            except Exception as e:
                stats["rag_error"] = str(e)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all pipeline components."""
        
        health = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }
        
        # Check LLM provider
        try:
            if not self.use_dev_mode and self.client:
                # Test Ollama connection
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{OLLAMA_URL}/api/tags")
                    if response.status_code == 200:
                        health["components"]["ollama"] = "connected"
                    else:
                        health["components"]["ollama"] = "error"
            else:
                health["components"]["ollama"] = "dev_mode"
        except Exception as e:
            health["components"]["ollama"] = f"error: {e}"
            health["status"] = "degraded"
        
        # Check RAG pipeline
        if self.rag:
            try:
                rag_health = await self.rag.health_check()
                health["components"]["rag"] = rag_health["status"]
            except Exception as e:
                health["components"]["rag"] = f"error: {e}"
                health["status"] = "degraded"
        else:
            health["components"]["rag"] = "not_initialized"
        
        return health
