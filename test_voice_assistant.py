# test_voice_assistant.py
"""Test script to verify Voice Assistant functionality."""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys will be loaded from .env file
# Make sure your .env file has:
# DEEPSEEK_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here

async def test_voice_assistant():
    """Test the voice assistant with a simple query."""
    from features.voice_assistant import VoiceAssistant
    
    print("=" * 60)
    print("Testing Voice Assistant")
    print("=" * 60)
    
    # Initialize assistant
    assistant = VoiceAssistant()
    print("\n✅ Voice Assistant initialized")
    
    # Test query
    test_query = "tell me about aspirin side effects"
    print(f"\n📝 Query: {test_query}")
    print("-" * 60)
    
    # Process command
    result = await assistant.process_voice_command(test_query)
    
    # Display results
    print(f"\n🎯 Intent: {result.intent}")
    print(f"📊 Confidence: {result.confidence:.0%}")
    
    if result.entities:
        print(f"\n🔍 Detected Entities:")
        for key, value in result.entities.items():
            print(f"  - {key}: {value}")
    
    print(f"\n💬 Response:")
    print("-" * 60)
    print(result.response)
    print("-" * 60)
    
    if result.suggested_actions:
        print(f"\n💡 Suggested Actions:")
        for action in result.suggested_actions:
            print(f"  - {action}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_voice_assistant())
