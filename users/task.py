from celery import shared_task
from django.db.models import F
from .models import User

@shared_task
def increase_daily_credits():      # increase 10 credits everyday
    updated_count = User.objects.update(credits=F('credits') + 10)
    return f"Successfully increased credits by 10 for {updated_count} users."