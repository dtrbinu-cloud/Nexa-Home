import asyncio
import io
import logging
from pathlib import Path
import wave
from typing import Tuple

from server.app.core.config import settings
from server.app.core.tts.base import TTSProvider

logger = logging.getLogger("server.tts.piper")


class PiperTTSProvider(TTSProvider):
    def __init__(
        self,
        bin_path: str | None = None,
        model_path: str | None = None,
        config_path: str | None = None,
    ):
        self.bin_path = Path(bin_path or settings.PIPER_BIN_PATH)
        self.model_path = Path(model_path or settings.PIPER_MODEL_PATH)
        self.config_path = Path(config_path or settings.PIPER_CONFIG_PATH)
        self._voice = None

    def is_available(self) -> bool:
        if not self.model_path.exists():
            return False
        try:
            import piper  # noqa: F401
            return True
        except ImportError:
            return self.bin_path.exists()

    def _get_voice(self):
        if self._voice is None:
            from piper import PiperVoice
            cfg = self.config_path if self.config_path.exists() else None
            self._voice = PiperVoice.load(str(self.model_path), config_path=str(cfg) if cfg else None)
        return self._voice

    async def synthesize(self, text: str, voice: str | None = None) -> Tuple[bytes, str]:
        if not self.is_available():
            raise RuntimeError("Suara offline tidak tersedia: Model Piper TTS atau engine runtime tidak ditemukan di server.")

        def _synthesize_blocking() -> bytes:
            try:
                voice_obj = self._get_voice()
                wav_buf = io.BytesIO()
                with wave.open(wav_buf, "wb") as wav_file:
                    voice_obj.synthesize_wav(text, wav_file)
                data = wav_buf.getvalue()
                if not data:
                    raise RuntimeError("Piper TTS menghasilkan output audio kosong.")
                return data
            except Exception as e:
                logger.error(f"Error sintesis Piper TTS: {e}")
                raise RuntimeError(f"Gagal melakukan sintesis suara offline Piper: {e}")

        wav_bytes = await asyncio.to_thread(_synthesize_blocking)
        return wav_bytes, "audio/wav"
