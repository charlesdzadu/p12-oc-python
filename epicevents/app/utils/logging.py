import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging
from functools import wraps
from typing import Callable, Any
from ..config import settings


logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry SDK for error tracking"""
    if settings.sentry_dsn:
        sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                sentry_logging,
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0 if settings.debug else 0.1,
            environment=settings.app_env,
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("Sentry DSN not configured")


def log_action(action: str):
    """Decorator to log important actions"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            user = kwargs.get("current_user")
            user_info = f"User: {user.email}" if user else "Anonymous"

            try:
                result = func(*args, **kwargs)
                logger.info(f"{action} - Success - {user_info}")

                if settings.sentry_dsn:
                    sentry_sdk.capture_message(f"{action} - {user_info}", level="info")

                return result
            except Exception as e:
                logger.error(f"{action} - Failed - {user_info} - Error: {e}")

                if settings.sentry_dsn:
                    sentry_sdk.capture_exception(e)

                raise

        return wrapper

    return decorator


def log_user_creation(user_id: int, email: str, department: str):
    """Log user creation event"""
    message = f"User created - ID: {user_id}, Email: {email}, Department: {department}"
    logger.info(message)

    if settings.sentry_dsn:
        sentry_sdk.capture_message(message, level="info")


def log_user_modification(user_id: int, modified_by: str, changes: dict):
    """Log user modification event"""
    message = f"User modified - ID: {user_id}, Modified by: {modified_by}, Changes: {changes}"
    logger.info(message)

    if settings.sentry_dsn:
        sentry_sdk.capture_message(message, level="info")


def log_contract_signed(contract_id: int, client_id: int, signed_by: str):
    """Log contract signature event"""
    message = f"Contract signed - ID: {contract_id}, Client: {client_id}, Signed by: {signed_by}"
    logger.info(message)

    if settings.sentry_dsn:
        sentry_sdk.capture_message(message, level="info")


def log_error(error: Exception, context: dict = None):
    """Log error with context"""
    logger.error(f"Error occurred: {error}", exc_info=True)

    if settings.sentry_dsn:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_exception(error)


def log_security_event(event_type: str, user_email: str, details: str):
    """Log security-related events"""
    message = f"Security Event - Type: {event_type}, User: {user_email}, Details: {details}"
    logger.warning(message)

    if settings.sentry_dsn:
        sentry_sdk.capture_message(message, level="warning")
