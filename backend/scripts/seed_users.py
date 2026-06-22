import os
import sys

# Add backend directory to sys path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.user import User, RoleEnum
from app.core.security import get_password_hash

def seed_users():
    # Explicitly create the users table if it doesn't exist
    from app.core.database import engine
    User.__table__.create(engine, checkfirst=True)

    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).count() > 0:
            print("Users already exist. Skipping seed.")
            return

        print("Seeding Users...")
        users_to_add = []

        # 1. Create Super Admin
        admin = User(
            username="admin",
            hashed_password=get_password_hash("Admin@123"),
            first_name="System",
            last_name="Admin",
            role=RoleEnum.super_admin
        )
        users_to_add.append(admin)

        # 2. Generate 100 Practitioners (Doctors/Nurses)
        for i in range(1, 101):
            role = RoleEnum.doctor if i % 2 == 0 else RoleEnum.nurse
            practitioner = User(
                username=f"practitioner{i}",
                hashed_password=get_password_hash("Password123!"),
                first_name="Dr." if role == RoleEnum.doctor else "Nurse",
                last_name=f"Mock{i}",
                role=role
            )
            users_to_add.append(practitioner)

        db.add_all(users_to_add)
        db.commit()
        print(f"Successfully generated {len(users_to_add)} user accounts!")
        
    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
