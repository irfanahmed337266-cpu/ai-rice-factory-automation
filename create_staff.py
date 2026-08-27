from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()

try:
    existing_user = db.query(User).filter(
        User.username == "staff"
    ).first()

    if existing_user:
        print("Staff user already exists.")
    else:
        staff = User(
            name="Staff User",
            username="staff",
            hashed_password=hash_password("Staff@123"),
            role="staff",
            is_active=True
        )

        db.add(staff)
        db.commit()
        db.refresh(staff)

        print("Staff user created successfully.")
        print("Username: staff")
        print("Password: Staff@123")
        print("Role: staff")

finally:
    db.close()