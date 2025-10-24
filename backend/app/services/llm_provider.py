"""
LLM Provider service for Veda Healthcare Chatbot.
Orchestrates multiple specialized models using Ollama as the unified model host.
"""

import os
import asyncio
import httpx
from typing import Optional, List, Dict, AsyncGenerator
from app.core.config import OLLAMA_URL, OLLAMA_API_KEY, LLM_PROVIDER, DEBUG
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
    Supports both development mode (canned responses) and production mode (Ollama).
    """
    
    def __init__(self, use_dev_mode: bool = None):
        self.use_dev_mode = use_dev_mode if use_dev_mode is not None else DEBUG
        self.client = OllamaClient() if not self.use_dev_mode else None
        
        # Healthcare disclaimer to append to all assistant messages
        self.disclaimer = ("\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only "
                          "and should not replace professional medical advice. Please consult with a "
                          "healthcare provider for medical concerns.")

    async def process_pipeline(
        self, 
        audio: Optional[bytes] = None, 
        image: Optional[bytes] = None,
        text: Optional[str] = None, 
        opts: Optional[Dict] = None
    ) -> str:
        """
        Process input through the AI pipeline.
        
        Args:
            audio: Audio data for transcription
            image: Image data for analysis
            text: Text input
            opts: Additional options (skip_summarizer, skip_rag, etc.)
            
        Returns:
            Final response text with disclaimer
        """
        opts = opts or {}
        
        if self.use_dev_mode:
            return await self._dev_mode_response(text, audio, image)
        
        # 1) STT via Ollama (if audio)
        if audio:
            # For now, simulate audio transcription
            # In production, this would call Ollama whisper model
            text = "Transcribed audio: " + (text or "Hello, I have a health question.")
            logger.info("Audio transcription simulated")

        # 2) Image analysis via Ollama (if image)
        if image:
            # For now, simulate image analysis
            # In production, this would call Ollama vision model (llava, bakllava)
            image_description = "Image shows medical-related content."
            text = f"{text or ''}\n\nImage analysis: {image_description}"
            logger.info("Image analysis simulated")

        if not text:
            raise ValueError("No text provided for processing")

        # 3) Summarize with Llama (optional)
        if not opts.get("skip_summarizer") and len(text) > 500:
            try:
                summary_messages = [
                    {"role": "user", "content": f"Summarize this medical query concisely: {text}"}
                ]
                resp = await self.client.chat("llama3.2", summary_messages)
                summary = resp.get("message", {}).get("content", text)
                logger.info("Text summarized")
            except Exception as e:
                logger.warning(f"Summarization failed: {e}, using original text")
                summary = text
        else:
            summary = text

        # 4) RAG retrieval (Pinecone) - placeholder for now
        docs = []
        if not opts.get("skip_rag"):
            # TODO: Implement RAG pipeline in next phase
            docs = ["Sample medical knowledge from database"]
            logger.info("RAG retrieval simulated")

        # 5) Final medical response
        prompt = summary
        if docs:
            context = "\n\n".join(docs)
            prompt = f"Context:\n{context}\n\nPatient Query: {summary}\n\nProvide a helpful medical response:"

        try:
            final_messages = [
                {"role": "system", "content": "You are a helpful medical assistant. Provide accurate, helpful information while emphasizing the importance of professional medical consultation."},
                {"role": "user", "content": prompt}
            ]
            
            # Use a medical model if available, fallback to general model
            model = "medgemma-4b-it"  # or "llama3.2" as fallback
            final_resp = await self.client.chat(model, final_messages)
            final_text = final_resp.get("message", {}).get("content", "I apologize, but I'm unable to process your request at the moment.")
            
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            final_text = "I apologize, but I'm experiencing technical difficulties. Please try again later."

        # Add healthcare disclaimer
        return final_text + self.disclaimer

    async def process_pipeline_stream(
        self,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None,
        text: Optional[str] = None,
        opts: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process input through the AI pipeline with streaming response.
        
        Args:
            audio: Audio data for transcription
            image: Image data for analysis  
            text: Text input
            opts: Additional options
            
        Yields:
            Chunks of the response text
        """
        opts = opts or {}
        
        if self.use_dev_mode:
            async for chunk in self._dev_mode_stream(text, audio, image):
                yield chunk
            return

        # Process input similar to non-streaming version
        if audio:
            text = "Transcribed audio: " + (text or "Hello, I have a health question.")
            
        if image:
            image_description = "Image shows medical-related content."
            text = f"{text or ''}\n\nImage analysis: {image_description}"

        if not text:
            raise ValueError("No text provided for processing")

        # For streaming, we'll skip summarization and RAG for now
        # and go directly to the final model
        try:
            final_messages = [
                {"role": "system", "content": "You are a helpful medical assistant. Provide accurate, helpful information while emphasizing the importance of professional medical consultation."},
                {"role": "user", "content": text}
            ]
            
            model = "medgemma-4b-it"  # or "llama3.2" as fallback
            
            # Stream the response
            async for chunk in self.client.chat_stream(model, final_messages):
                yield chunk
                
            # Add disclaimer at the end
            yield self.disclaimer
            
        except Exception as e:
            logger.error(f"Streaming response generation failed: {e}")
            yield "I apologize, but I'm experiencing technical difficulties. Please try again later."
            yield self.disclaimer

    async def _dev_mode_response(self, text: Optional[str], audio: Optional[bytes], image: Optional[bytes]) -> str:
        """Generate canned response for development mode."""
        
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        responses = [
            "Thank you for your health question. Based on your symptoms, I recommend consulting with a healthcare professional for proper evaluation.",
            "I understand your concern. While I can provide general information, it's important to speak with a doctor who can examine you properly.",
            "Your symptoms could have various causes. A healthcare provider would be the best person to give you an accurate diagnosis and treatment plan.",
            "I appreciate you sharing your health concerns with me. For the most accurate advice, please consider scheduling an appointment with your doctor.",
            "Based on what you've described, there are several possibilities. A medical professional can help determine the best course of action for your situation."
        ]
        
        # Simple hash-based selection for consistent responses
        import hashlib
        text_hash = hashlib.md5((text or "default").encode()).hexdigest()
        response_index = int(text_hash[:2], 16) % len(responses)
        
        base_response = responses[response_index]
        
        # Add context based on input type
        if audio:
            base_response = f"I've processed your voice message. {base_response}"
        if image:
            base_response = f"I've analyzed your image. {base_response}"
            
        return base_response + self.disclaimer

    async def _dev_mode_stream(self, text: Optional[str], audio: Optional[bytes], image: Optional[bytes]) -> AsyncGenerator[str, None]:
        """Generate streaming canned response for development mode."""
        
        full_response = await self._dev_mode_response(text, audio, image)
        
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
