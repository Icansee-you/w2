# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# Make Celery import optional for Streamlit compatibility
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except (ImportError, ModuleNotFoundError):
    # Celery not available or not needed (e.g., when running Streamlit)
    celery_app = None
    __all__ = ()

