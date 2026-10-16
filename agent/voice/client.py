"""agent/voice/client.py - ElevenLabs Conversational Voice Streaming Client."""
import time
from typing import Optional
from core.schemas import VoiceTurnEvent


class ElevenLabsVoiceClient:
    """Streams bidirectional audio via ElevenLabs WebSocket & Turbo model."""

    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        self.api_key = api_key or "mock_key"
        self.voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"

    def synthesize_speech(self, text: str) -> VoiceTurnEvent:
        # In live mode, streams audio chunks via elevenlabs.generate() or websocket
        return VoiceTurnEvent(
            turn_id=f"turn-{int(time.time() * 1000)}",
            speaker="AEGIS",
            text=text,
            audio_chunk=b"\x00\x01\x02\x03",  # Mock PCM buffer
        )


class MockElevenLabsVoiceClient(ElevenLabsVoiceClient):
    """Deterministic Mock ElevenLabs Client for Stage Contingencies."""

    def synthesize_speech(self, text: str) -> VoiceTurnEvent:
        return VoiceTurnEvent(
            turn_id="turn-mock-01",
            speaker="AEGIS",
            text=text,
            audio_chunk=b"\xaa\xbb\xcc\xdd",
        )
