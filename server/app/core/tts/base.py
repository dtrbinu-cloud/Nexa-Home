from abc import ABC, abstractmethod
from typing import Tuple


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str | None = None) -> Tuple[bytes, str]:
        """
        Sintesis suara dari teks.
        Mengembalikan tuple: (audio_bytes, mime_type)
        Contoh mime_type: 'audio/mpeg' atau 'audio/wav'
        """
        pass
