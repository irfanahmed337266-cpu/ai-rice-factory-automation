from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password


db = SessionLocal()

try:
    existing_user = db.query(User).filter(
        User.username == "admin"
    ).first()

    if existing_user:
        print("Admin user already exists.")
    else:
        admin = User(
            name="Administrator",
            username="admin",
            hashed_password=hash_password("Admin@123"),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin user created successfully.")
        print("Username: admin")
        print("Password: Admin@123")

finally:
    db.close()
