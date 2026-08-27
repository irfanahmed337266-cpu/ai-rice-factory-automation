from fastapi import APIRouter, Depends

from app.core.security import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/dashboard")
def admin_dashboard(
    current_user: dict = Depends(require_admin)
):
    return {
        "message": "Welcome to Admin Dashboard",
        "user_id": current_user.get("sub"),
        "username": current_user.get("username"),
        "role": current_user.get("role")
    }