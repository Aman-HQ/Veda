#!/usr/bin/env python3
"""Test development mode functionality."""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_provider import LLMProvider
from app.services.rag.pipeline import RAGPipeline
from app.services.audio_utils import transcribe_audio, translate_text

async def test_dev_mode():
    """Test development mode functionality."""
    
    print("Testing B07.5 Multi-Model Orchestration - Development Mode")
    print("=" * 60)
    
    # Test LLM Provider in dev mode
    print("\n1. Testing LLM Provider (Dev Mode)")
    llm = LLMProvider(use_dev_mode=True)
    
    # Test text pipeline
    print("   - Text pipeline...")
    result = await llm.process_pipeline(text="I have a headache")
    print(f"   Result: {result[:100]}...")
    
    # Test audio pipeline
    print("   - Audio pipeline...")
    result = await llm.process_pipeline(audio=b"fake_audio_data")
    print(f"   Result: {result[:100]}...")
    
    # Test image pipeline
    print("   - Image pipeline...")
    result = await llm.process_pipeline(image=b"fake_image_data")
    print(f"   Result: {result[:100]}...")
    
    # Test RAG Pipeline
    print("\n2. Testing RAG Pipeline (Dev Mode)")
    rag = RAGPipeline()
    stats = rag.get_stats()
    print(f"   Mode: {stats['mode']}")
    print(f"   Document count: {stats.get('document_count', 'N/A')}")
    
    # Test retrieval
    results = await rag.retrieve("headache symptoms", top_k=2)
    print(f"   Retrieved {len(results)} documents")
    if results:
        print(f"   Sample: {results[0]['text'][:80]}...")
    
    # Test Audio Utils
    print("\n3. Testing Audio Utils (Dev Mode)")
    
    # Test transcription
    transcription = await transcribe_audio(b"fake_audio", "en")
    print(f"   Transcription: {transcription}")
    
    # Test translation
    translation = await translate_text("Hello", "en", "hi")
    print(f"   Translation: {translation}")
    
    # Test pipeline stats
    print("\n4. Testing Pipeline Stats")
    stats = await llm.get_pipeline_stats()
    print(f"   Mode: {stats['mode']}")
    print(f"   Models: {stats['models']}")
    print(f"   Flags: {stats['flags']}")
    
    # Test health check
    print("\n5. Testing Health Check")
    health = await llm.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Components: {health['components']}")
    
    print("\n✅ All development mode tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_dev_mode())