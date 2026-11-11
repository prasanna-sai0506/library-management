import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'librarymanagement.settings')
app = Celery('librarymanagement')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()