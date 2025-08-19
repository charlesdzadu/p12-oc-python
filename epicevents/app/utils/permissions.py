from functools import wraps
from typing import Optional, Callable
from contextlib import contextmanager
from ..auth.models import User, Department
from ..auth.utils import load_token, decode_access_token
from ..database import get_session


class SessionBoundUser:
    """A wrapper that ensures User objects stay bound to their session context."""
    
    def __init__(self, user_id: int, session):
        self._user_id = user_id
        self._session = session
        self._user = None
    
    def _get_user(self):
        """Lazy loading of user to ensure it's always bound to the current session."""
        if self._user is None:
            self._user = self._session.get(User, self._user_id)
        return self._user
    
    def __getattr__(self, name):
        """Delegate attribute access to the actual User object."""
        user = self._get_user()
        if user is None:
            raise ValueError("User not found")
        return getattr(user, name)
    
    def __bool__(self):
        """Allow truthiness checks."""
        return self._get_user() is not None


@contextmanager
def get_current_user_with_session():
    """Get current user with an active session context."""
    token = load_token()
    if not token:
        yield None
        return
    
    payload = decode_access_token(token)
    if not payload:
        yield None
        return
    
    user_id = payload.get("user_id")
    if not user_id:
        yield None
        return
    
    with get_session() as session:
        user = session.get(User, user_id)
        yield user


def get_current_user() -> Optional[User]:
    """Get current user with session binding protection."""
    token = load_token()
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    # Return a session-bound user that maintains connection
    # This creates its own session context for each access
    return _SessionSafeUser(user_id)


class _SessionSafeUser:
    """A User proxy that maintains session binding for each attribute access."""
    
    def __init__(self, user_id: int):
        self._user_id = user_id
        self._cached_attrs = {}
    
    def _with_session(self, operation):
        """Execute an operation with a fresh session."""
        with get_session() as session:
            user = session.get(User, self._user_id)
            if not user:
                raise ValueError("User not found")
            return operation(user)
    
    def __getattr__(self, name):
        """Get attribute with session protection."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        
        def get_attr(user):
            return getattr(user, name)
        
        return self._with_session(get_attr)
    
    def __bool__(self):
        """Allow truthiness checks."""
        try:
            with get_session() as session:
                user = session.get(User, self._user_id)
                return user is not None
        except:
            return False
    
    def has_permission(self, action: str, resource: str) -> bool:
        """Check permission with session protection."""
        def check_permission(user):
            return user.has_permission(action, resource)
        
        return self._with_session(check_permission)
    
    @property
    def id(self) -> Optional[int]:
        """Get user ID with session protection."""
        def get_id(user):
            return user.id
        
        return self._with_session(get_id)
    
    @property
    def department(self) -> Optional[Department]:
        """Get user department with session protection."""
        def get_department(user):
            return user.department
        
        return self._with_session(get_department)
    
    @property
    def full_name(self) -> Optional[str]:
        """Get user full name with session protection."""
        def get_full_name(user):
            return user.full_name
        
        return self._with_session(get_full_name)
    
    @property
    def email(self) -> Optional[str]:
        """Get user email with session protection."""
        def get_email(user):
            return user.email
        
        return self._with_session(get_email)
    
    @property
    def employee_id(self) -> Optional[str]:
        """Get user employee ID with session protection."""
        def get_employee_id(user):
            return user.employee_id
        
        return self._with_session(get_employee_id)
    
    @property
    def is_active(self) -> bool:
        """Get user active status with session protection."""
        def get_is_active(user):
            return user.is_active
        
        return self._with_session(get_is_active)
    
    @property
    def is_management(self) -> bool:
        """Check if user is management with session protection."""
        def check_is_management(user):
            return user.is_management
        
        return self._with_session(check_is_management)
    
    @property
    def is_commercial(self) -> bool:
        """Check if user is commercial with session protection."""
        def check_is_commercial(user):
            return user.is_commercial
        
        return self._with_session(check_is_commercial)
    
    @property
    def is_support(self) -> bool:
        """Check if user is support with session protection."""
        def check_is_support(user):
            return user.is_support
        
        return self._with_session(check_is_support)


def require_auth(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_current_user_with_session() as user:
            if not user:
                raise PermissionError("Authentication required. Please login first.")
            kwargs["current_user"] = user
            return func(*args, **kwargs)

    return wrapper


def require_department(*departments: Department):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with get_current_user_with_session() as user:
                if not user:
                    raise PermissionError("Authentication required. Please login first.")

                if user.department not in departments:
                    allowed = ", ".join([d.value for d in departments])
                    raise PermissionError(
                        f"This action requires one of the following departments: {allowed}"
                    )

                kwargs["current_user"] = user
                return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(action: str, resource: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with get_current_user_with_session() as user:
                if not user:
                    raise PermissionError("Authentication required. Please login first.")

                if not user.has_permission(action, resource):
                    raise PermissionError(f"You don't have permission to {action} {resource}")

                kwargs["current_user"] = user
                return func(*args, **kwargs)

        return wrapper

    return decorator
