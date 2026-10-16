"""tests/test_voice_stream.py - Tests for ElevenLabs Voice Synthesis."""
from agent.voice.client import MockElevenLabsVoiceClient


def test_voice_synthesis_mock():
    client = MockElevenLabsVoiceClient()
    event = client.synthesize_speech("Ayush, wake up. auth-gateway is erroring at 94%.")

    assert event.speaker == "AEGIS"
    assert "auth-gateway" in event.text
    assert event.audio_chunk is not None
    assert len(event.audio_chunk) > 0
