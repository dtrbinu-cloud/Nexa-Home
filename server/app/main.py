import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from server.app.api.routes.audit import router as audit_router
from server.app.api.routes.auth import router as auth_router
from server.app.api.routes.devices import router as devices_router
from server.app.api.routes.health import router as health_router
from server.app.api.routes.protected_test import router as test_router
from server.app.core.config import settings
from server.app.core.database import AsyncSessionLocal, Base, engine, init_sqlite_wal
from server.app.core.mqtt_auth import ensure_mosquitto_config
from server.app.core.mqtt_client import mqtt_service
from server.app.core.setup_manager import init_setup_code_if_needed
from server.app.models.audit import AuditLog
from server.app.models.automation import Automation, NotificationLog
from server.app.models.device import Channel, Device, TelemetryLog
from server.app.models.user import RefreshToken, User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Inisialisasi pragmas SQLite WAL
    await init_sqlite_wal()

    # 2. Buat tabel database jika belum ada
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. Konfigurasi awal file Mosquitto
    try:
        ensure_mosquitto_config()
    except Exception as e:
        print(f"[Mosquitto] Init config warning: {e}")

    # 4. Mulai background worker MQTT client
    loop = asyncio.get_running_loop()
    try:
        mqtt_service.start(loop)
    except Exception as e:
        print(f"[MQTT] Service start warning: {e}")

    # 5. Periksa apakah admin sudah ada, jika belum cetak kode setup sekali pakai
    async with AsyncSessionLocal() as session:
        count_query = select(func.count()).select_from(User).where(User.role == "admin")
        result = await session.execute(count_query)
        admin_count = result.scalar() or 0
        init_setup_code_if_needed(admin_count > 0)

    yield

    # Shutdown
    mqtt_service.stop()


app = FastAPI(
    title="Rumah — Smart Home API",
    description="Backend API inti untuk sistem Smart Home & Pengawasan Keluarga",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",  # Izinkan Flutter client lokal
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(devices_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(test_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Rumah Smart Home Backend",
        "status": "online",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/api/health",
        "setup_status": "/api/auth/setup-status",
    }
