import hashlib
import logging
from pathlib import Path
import time
from typing import Tuple

from server.app.core.config import settings
from server.app.core.tts.base import TTSProvider
from server.app.core.tts.edge import EdgeTTSProvider
from server.app.core.tts.piper import PiperTTSProvider

logger = logging.getLogger("server.tts.service")


class TTSService:
    def __init__(
        self,
        edge_provider: TTSProvider | None = None,
        piper_provider: TTSProvider | None = None,
        cache_dir: str | None = None,
    ):
        self.edge_provider = edge_provider or EdgeTTSProvider()
        self.piper_provider = piper_provider or PiperTTSProvider()
        self.cache_dir = Path(cache_dir or settings.TTS_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, text: str, voice: str, provider: str) -> str:
        content = f"{provider}:{voice}:{text}".strip().lower()
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def synthesize(
        self,
        text: str,
        preferred_provider: str | None = None,
        voice: str | None = None,
    ) -> Tuple[bytes, str, str, float]:
        """
        Sintesis suara dengan auto-fallback dan disk caching.
        Mengembalikan tuple: (audio_bytes, mime_type, provider_used, elapsed_seconds)
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Teks tidak boleh kosong.")

        if len(clean_text) > settings.TTS_MAX_TEXT_LENGTH:
            raise ValueError(f"Teks melebihi batas maksimum {settings.TTS_MAX_TEXT_LENGTH} karakter.")

        prov_choice = (preferred_provider or settings.TTS_PROVIDER).lower()
        selected_voice = voice or (settings.EDGE_TTS_VOICE if prov_choice == "edge-tts" else "id_ID-indotts-medium")

        # 1. Cek disk cache
        cache_key = self._get_cache_key(clean_text, selected_voice, prov_choice)
        cached_file_mp3 = self.cache_dir / f"{cache_key}.mp3"
        cached_file_wav = self.cache_dir / f"{cache_key}.wav"

        if cached_file_mp3.exists():
            return cached_file_mp3.read_bytes(), "audio/mpeg", prov_choice, 0.001
        if cached_file_wav.exists():
            return cached_file_wav.read_bytes(), "audio/wav", prov_choice, 0.001

        start_time = time.perf_counter()

        # 2. Coba provider utama (default edge-tts)
        if prov_choice == "edge-tts":
            try:
                audio_bytes, mime_type = await self.edge_provider.synthesize(clean_text, voice=selected_voice)
                elapsed = time.perf_counter() - start_time
                self._save_cache(cache_key, audio_bytes, mime_type)
                return audio_bytes, mime_type, "edge-tts", elapsed
            except Exception as exc:
                logger.warning(f"Edge TTS gagal ({exc}). Otomatis beralih (fallback) ke Piper TTS offline...")
                prov_choice = "piper"

        # 3. Provider Piper (baik sebagai pilihan utama atau fallback dari Edge TTS)
        if prov_choice == "piper":
            try:
                piper_voice = voice if (preferred_provider == "piper" and voice) else "id_ID-news_tts-medium"
                audio_bytes, mime_type = await self.piper_provider.synthesize(clean_text, voice=piper_voice)
                elapsed = time.perf_counter() - start_time
                self._save_cache(cache_key, audio_bytes, mime_type)
                return audio_bytes, mime_type, "piper", elapsed
            except Exception as exc:
                logger.error(f"Piper TTS juga gagal ({exc}).")

                # Jika piper awalnya dipilih dan gagal, coba edge-tts sebagai fallback terakhir
                try:
                    audio_bytes, mime_type = await self.edge_provider.synthesize(clean_text, voice=selected_voice)
                    elapsed = time.perf_counter() - start_time
                    self._save_cache(cache_key, audio_bytes, mime_type)
                    return audio_bytes, mime_type, "edge-tts", elapsed
                except Exception:
                    raise RuntimeError(f"Gagal melakukan sintesis suara dengan seluruh provider: {exc}")

        raise ValueError(f"Provider TTS '{prov_choice}' tidak dikenal.")

    def _save_cache(self, key: str, data: bytes, mime_type: str) -> None:
        try:
            ext = ".mp3" if "mpeg" in mime_type else ".wav"
            target_path = self.cache_dir / f"{key}{ext}"
            target_path.write_bytes(data)
        except Exception as exc:
            logger.warning(f"Gagal menyimpan cache TTS: {exc}")


_default_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    global _default_tts_service
    if _default_tts_service is None:
        _default_tts_service = TTSService()
    return _default_tts_service
