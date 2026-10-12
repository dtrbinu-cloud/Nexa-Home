from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory repo
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "server" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "rumah.db"

ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SECRET_KEY: str = "default_insecure_development_secret_key_change_me_in_env_file"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}"

    # MQTT
    MQTT_BROKER_HOST: str = "127.0.0.1"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "rumah_server"
    MQTT_PASSWORD: str = ""
    MQTT_CLIENT_ID: str = "rumah_core_server"
    MQTT_TOPIC_PREFIX: str = "home"

    # MediaMTX
    MEDIAMTX_API_URL: str = "http://127.0.0.1:9997"
    MEDIAMTX_RTSP_URL: str = "rtsp://127.0.0.1:8554"
    MEDIAMTX_WEBRTC_URL: str = "http://127.0.0.1:8889"

    # DeepSeek LLM
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # TTS
    TTS_PROVIDER: str = "edge-tts"
    EDGE_TTS_VOICE: str = "id-ID-ArdiNeural"
    PIPER_MODEL_PATH: str = "./models/piper/id_ID-indotts-medium.onnx"

    # AI Vision
    VISION_ENABLED: bool = False
    VISION_MAX_CAMERAS: int = 2
    VISION_TARGET_FPS: int = 3
    VISION_INPUT_WIDTH: int = 640
    VISION_INPUT_HEIGHT: int = 640


settings = Settings()
