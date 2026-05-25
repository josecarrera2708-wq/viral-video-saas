"""
Audio generation service - TTS (Text-to-Speech)
Supports gTTS (free) and ElevenLabs (premium)
"""

import asyncio
import os
from typing import Optional
from gtts import gTTS
import logging

logger = logging.getLogger(__name__)

class AudioService:
    """Text-to-Speech audio generation service"""

    def __init__(self):
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.use_elevenlabs = bool(self.elevenlabs_api_key)

    async def generate_audio(
        self,
        text: str,
        language: str = "en",
        voice_id: Optional[str] = None
    ) -> bytes:
        """
        Generate audio from text using TTS

        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'es', 'fr')
            voice_id: Optional ElevenLabs voice ID (if using premium)

        Returns:
            Audio bytes (MP3 format)
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for TTS")
            return b""

        try:
            if self.use_elevenlabs and voice_id:
                return await self._generate_elevenlabs_audio(text, voice_id)
            else:
                return await self._generate_gtts_audio(text, language)
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            raise

    async def _generate_gtts_audio(self, text: str, language: str) -> bytes:
        """Generate audio using Google Text-to-Speech (free)"""
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            # Save to bytes buffer
            import io
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.getvalue()
        except Exception as e:
            logger.error(f"gTTS error: {str(e)}")
            raise

    async def _generate_elevenlabs_audio(
        self,
        text: str,
        voice_id: str
    ) -> bytes:
        """Generate audio using ElevenLabs API (premium)"""
        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"ElevenLabs error: {str(e)}")
            raise

    def get_available_languages(self) -> list[str]:
        """Get list of supported languages for gTTS"""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh-cn", "ar", "hi"
        ]

    def get_elevenlabs_voices(self) -> dict:
        """Get available ElevenLabs voices (cached list)"""
        if not self.use_elevenlabs:
            return {}

        return {
            "adam": "pNInY6obpgDQGcFmaJgB",  # Young male, American
            "bella": "EXAVITQu4vr4xnSDxMaL",  # Young female, American
            "chris": "iP95p4xoKVk53GoZ742B",  # Young male, British
            "default": "21m00Tcm4TlvDq8ikWAM",  # Default voice
        }


# Singleton instance
_audio_service = AudioService()

async def get_audio_service() -> AudioService:
    """Dependency injection for AudioService"""
    return _audio_service
