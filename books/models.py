from django.db import models
from decimal import Decimal
class Book(models.Model):
    AVAILABLE = 'AVAILABLE'
    UNAVAILABLE = 'UNAVAILABLE'
    AVAILABILITY_CHOICES = [
        (AVAILABLE, 'Available'),
        (UNAVAILABLE, 'Unavailable'),
    ]
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.CharField(max_length=100)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default=AVAILABLE)
    borrowing_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    borrowing_period = models.PositiveIntegerField(default=7)  # in days
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"