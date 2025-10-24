# ecommerce/__init__.py
from ecommerce_celery import app as celery_app
__all__ = ('celery_app',)