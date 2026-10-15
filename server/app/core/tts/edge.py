import asyncio
import logging
from typing import Tuple

import edge_tts

from server.app.core.config import settings
from server.app.core.tts.base import TTSProvider

logger = logging.getLogger("server.tts.edge")

ALLOWED_EDGE_VOICES = {
    "id-ID-ArdiNeural",
    "id-ID-GadisNeural",
}


class EdgeTTSProvider(TTSProvider):
    def __init__(self, default_voice: str | None = None):
        self.default_voice = default_voice or settings.EDGE_TTS_VOICE
        if self.default_voice not in ALLOWED_EDGE_VOICES:
            self.default_voice = "id-ID-ArdiNeural"

    async def synthesize(self, text: str, voice: str | None = None) -> Tuple[bytes, str]:
        selected_voice = voice if (voice and voice in ALLOWED_EDGE_VOICES) else self.default_voice
        communicate = edge_tts.Communicate(text=text, voice=selected_voice)
        audio_stream = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.extend(chunk["data"])

        if not audio_stream:
            raise RuntimeError("Edge TTS menghasilkan output audio kosong.")

        return bytes(audio_stream), "audio/mpeg"
