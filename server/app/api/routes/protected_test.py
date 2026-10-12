from fastapi import APIRouter, Depends

from server.app.api.deps import require_role
from server.app.models.user import User

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/admin-only")
async def test_admin_only(current_user: User = Depends(require_role("admin"))):
    return {"message": "Selamat datang, Admin.", "user": current_user.username}


@router.get("/member-only")
async def test_member_only(
    current_user: User = Depends(require_role("admin", "member"))
):
    return {
        "message": "Selamat datang, Anggota Keluarga.",
        "user": current_user.username,
    }


@router.get("/child-allowed")
async def test_child_allowed(
    current_user: User = Depends(require_role("admin", "member", "child"))
):
    return {"message": "Akses diberikan.", "user": current_user.username}
