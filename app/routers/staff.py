from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user

router = APIRouter(
    prefix="/staff",
    tags=["Staff"]
)


@router.get("/dashboard")
def staff_dashboard(
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "staff":
        raise HTTPException(
            status_code=403,
            detail="Staff access required"
        )

    return {
        "message": "Welcome to Staff Dashboard",
        "user_id": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"]
    }