from sqlmodel import Session, select
from typing import Optional, Dict, Any
from .models import User, Department
from .utils import hash_password, verify_password, create_access_token, decode_access_token
from ..database import get_session
from ..utils.logging import log_user_creation, log_user_modification, log_security_event


class AuthService:
    @staticmethod
    def create_user(
        employee_id: str, full_name: str, email: str, password: str, department: Department
    ) -> User:
        with get_session() as session:
            existing_user = session.exec(
                select(User).where((User.email == email) | (User.employee_id == employee_id))
            ).first()

            if existing_user:
                raise ValueError("User with this email or employee ID already exists")

            password_hash = hash_password(password)
            user = User(
                employee_id=employee_id,
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                department=department,
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            log_user_creation(user.id, user.email, user.department.value)

            return user

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[str]:
        with get_session() as session:
            user = session.exec(select(User).where(User.email == email)).first()

            if not user or not user.is_active:
                log_security_event("login_failed", email, "User not found or inactive")
                return None

            if not verify_password(password, user.password_hash):
                log_security_event("login_failed", email, "Invalid password")
                return None

            token_data = {
                "user_id": user.id,
                "email": user.email,
                "department": user.department.value,
                "employee_id": user.employee_id,
            }

            return create_access_token(token_data)

    @staticmethod
    def get_current_user(token: str) -> Optional[User]:
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        with get_session() as session:
            return session.get(User, user_id)

    @staticmethod
    def update_user(
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        department: Optional[Department] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("User not found")

            if full_name:
                user.full_name = full_name
            if email:
                user.email = email
            if department:
                user.department = department
            if is_active is not None:
                user.is_active = is_active

            session.add(user)
            session.commit()
            session.refresh(user)

            changes = {}
            if full_name:
                changes["full_name"] = full_name
            if email:
                changes["email"] = email
            if department:
                changes["department"] = department.value
            if is_active is not None:
                changes["is_active"] = is_active

            log_user_modification(user.id, "system", changes)

            return user

    @staticmethod
    def change_password(user_id: int, new_password: str) -> bool:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False

            user.password_hash = hash_password(new_password)
            session.add(user)
            session.commit()
            return True

    @staticmethod
    def delete_user(user_id: int) -> bool:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False

            session.delete(user)
            session.commit()
            return True
