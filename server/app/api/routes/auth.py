import datetime
import json
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.deps import get_current_user, record_audit_log, require_role
from server.app.core.config import settings
from server.app.core.database import get_db
from server.app.core.security import (
    create_access_token,
    create_refresh_token_string,
    create_temp_token,
    decode_token,
    generate_recovery_codes,
    generate_totp_secret,
    get_totp_uri,
    hash_code,
    hash_password,
    verify_password,
    verify_recovery_code,
    verify_totp,
)
from server.app.core.setup_manager import (
    has_proxy_headers,
    init_setup_code_if_needed,
    is_lan_or_localhost,
    verify_and_consume_setup_code,
)
from server.app.models.user import RefreshToken, User

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Pydantic Schemas ---
class SetupAdminRequest(BaseModel):
    setup_code: str = Field(..., description="Kode sekali pakai dari konsol server")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str = Field(..., description="6 digit TOTP atau recovery code")


class RefreshRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: Literal["member", "child"]


# --- Endpoints ---
@router.get("/setup-status")
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Check if initial admin setup has been completed."""
    count_query = select(func.count()).select_from(User).where(User.role == "admin")
    result = await db.execute(count_query)
    admin_count = result.scalar() or 0

    has_admin = admin_count > 0
    init_setup_code_if_needed(has_admin)

    return {
        "is_setup": has_admin,
        "admin_exists": has_admin,
        "setup_code_required": not has_admin,
    }


@router.post("/setup-admin", status_code=status.HTTP_201_CREATED)
async def setup_admin(
    payload: SetupAdminRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # 1. Tolak permintaan dari reverse proxy / tunnel
    if has_proxy_headers(dict(request.headers)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup wizard tidak dapat diakses melalui reverse proxy atau tunnel.",
        )

    # 2. Validasi IP (hanya localhost atau LAN privat)
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not is_lan_or_localhost(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup wizard hanya dapat diakses melalui jaringan lokal (LAN) atau localhost.",
        )

    # 3. Cek apakah admin sudah ada
    count_query = select(func.count()).select_from(User).where(User.role == "admin")
    result = await db.execute(count_query)
    if (result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sistem telah memiliki admin terdaftar. Setup wizard telah ditutup.",
        )

    # 3. Verifikasi kode sekali pakai
    if not verify_and_consume_setup_code(payload.setup_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode setup tidak valid atau telah digunakan.",
        )

    # 4. Hash password dan buat data TOTP 2FA
    pwd_hash = hash_password(payload.password)
    totp_secret = generate_totp_secret()
    totp_uri = get_totp_uri(totp_secret, payload.username)
    plain_codes, hashed_codes = generate_recovery_codes(8)

    admin_user = User(
        username=payload.username.strip(),
        password_hash=pwd_hash,
        role="admin",
        totp_secret=totp_secret,
        recovery_codes=json.dumps(hashed_codes),
        is_active=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    # Catat audit log
    await record_audit_log(
        db=db,
        action="auth.setup_admin",
        user_id=admin_user.id,
        username=admin_user.username,
        target_type="user",
        target_id=str(admin_user.id),
        details={"ip": client_ip, "message": "Inisialisasi akun admin pertama"},
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "message": "Akun admin berhasil diinisialisasi.",
        "user": {
            "id": admin_user.id,
            "username": admin_user.username,
            "role": admin_user.role,
        },
        "totp_secret": totp_secret,
        "totp_uri": totp_uri,
        "recovery_codes": plain_codes,
    }


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with username and password. Returns 2FA challenge for admin."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    query = select(User).where(User.username == payload.username.strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        await record_audit_log(
            db=db,
            action="auth.login_failed",
            username=payload.username,
            details={"ip": client_ip, "reason": "kredensial_salah"},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nama pengguna atau kata sandi tidak sesuai.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun ini telah dinonaktifkan.",
        )

    # Jika admin atau memiliki 2FA aktif: wajib selesaikan tantangan 2FA
    if user.role == "admin" or user.totp_secret:
        temp_token = create_temp_token(user.id, user.username)
        return {
            "status": "2fa_required",
            "temp_token": temp_token,
            "message": "Verifikasi 2FA diperlukan.",
        }

    # Untuk member/child tanpa 2FA
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token_string()
    refresh_hash = hash_code(refresh_token)

    db_rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.datetime.utcnow()
        + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_rt)
    await db.commit()

    await record_audit_log(
        db=db,
        action="auth.login_success",
        user_id=user.id,
        username=user.username,
        details={"ip": client_ip, "role": user.role},
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/verify-2fa")
async def verify_2fa(
    payload: Verify2FARequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP 6-digit code or one-time recovery code."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    try:
        token_data = decode_token(payload.temp_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tantangan 2FA tidak valid atau telah kedaluwarsa.",
        )

    if token_data.get("type") != "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipe token bukan untuk verifikasi 2FA.",
        )

    user_id = int(token_data.get("sub", 0))
    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan.",
        )

    # 1. Coba verifikasi kode TOTP
    code_clean = payload.code.strip()
    is_valid = verify_totp(user.totp_secret, code_clean)
    used_recovery = False

    # 2. Jika TOTP gagal, coba verifikasi recovery code
    if not is_valid and user.recovery_codes:
        ok, updated_json = verify_recovery_code(code_clean, user.recovery_codes)
        if ok:
            is_valid = True
            used_recovery = True
            user.recovery_codes = updated_json

    if not is_valid:
        await record_audit_log(
            db=db,
            action="auth.2fa_failed",
            user_id=user.id,
            username=user.username,
            details={"ip": client_ip},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kode 2FA atau kode pemulihan salah.",
        )

    # Berhasil verifikasi 2FA
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token_string()
    refresh_hash = hash_code(refresh_token)

    db_rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.datetime.utcnow()
        + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_rt)
    await db.commit()

    await record_audit_log(
        db=db,
        action="auth.login_2fa_success",
        user_id=user.id,
        username=user.username,
        details={
            "ip": client_ip,
            "role": user.role,
            "used_recovery_code": used_recovery,
        },
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "used_recovery_code": used_recovery,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/refresh")
async def refresh_access_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token using a valid refresh token."""
    rt_hash = hash_code(payload.refresh_token)
    query = (
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == rt_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.datetime.utcnow(),
        )
    )
    result = await db.execute(query)
    db_rt = result.scalar_one_or_none()

    if not db_rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau telah kedaluwarsa.",
        )

    # Ambil user terkait
    user_query = select(User).where(User.id == db_rt.user_id, User.is_active == True)
    user_res = await db.execute(user_query)
    user = user_res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan atau tidak aktif.",
        )

    # Rotasi Refresh Token: cabut token lama, buat token baru
    db_rt.revoked = True

    new_refresh_token = create_refresh_token_string()
    new_rt_hash = hash_code(new_refresh_token)
    new_db_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_rt_hash,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(new_db_rt)
    await db.commit()

    new_access_token = create_access_token(user.id, user.username, user.role)
    return {
        "status": "ok",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return profile information of current authenticated user."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    current_admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only endpoint to create family members or child accounts."""
    check_query = select(User).where(User.username == payload.username.strip())
    existing = (await db.execute(check_query)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nama pengguna '{payload.username}' sudah terdaftar.",
        )

    new_user = User(
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    await record_audit_log(
        db=db,
        action="user.create",
        user_id=current_admin.id,
        username=current_admin.username,
        target_type="user",
        target_id=str(new_user.id),
        details={"created_user": new_user.username, "role": new_user.role},
    )

    return {
        "status": "ok",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role,
        },
    }
