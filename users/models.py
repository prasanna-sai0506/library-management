# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class User(AbstractUser):
    ADMIN = 'ADMIN'
    MEMBER = 'MEMBER'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))

    def __str__(self):
        return f"{self.username} ({self.role})"