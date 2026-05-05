from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


def seed_demo_data(db: Session) -> None:
    demo_users = [
        ("admin@example.com", "Admin User", UserRole.admin),
        ("agent@example.com", "Support Agent", UserRole.agent),
        ("customer@example.com", "Customer User", UserRole.customer),
    ]

    for email, full_name, role in demo_users:
        existing_user = db.scalar(select(User).where(User.email == email))
        if existing_user:
            continue
        db.add(User(email=email, full_name=full_name, role=role, password_hash=hash_password("password")))

    db.commit()
