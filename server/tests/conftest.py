import os
from pathlib import Path
import pytest

# Pastikan pengujian otomatis (pytest) selalu menggunakan database terpisah
# dan tidak menghapus atau mengubah database produksi (rumah.db).
TEST_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "test_rumah.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["APP_ENV"] = "testing"


@pytest.fixture(autouse=True)
async def ensure_db_tables():
    from server.app.core.database import Base, engine, init_sqlite_wal
    import server.app.models.camera  # noqa
    import server.app.models.device  # noqa
    import server.app.models.user  # noqa
    import server.app.models.audit  # noqa
    import server.app.models.automation  # noqa

    await init_sqlite_wal()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from server.app.core.database import check_and_migrate_db
    await check_and_migrate_db()
    yield
