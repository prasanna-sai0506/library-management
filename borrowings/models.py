from django.db import models
from django.conf import settings
from books.models import Book
from decimal import Decimal
from django.utils import timezone

class Borrowing(models.Model):
    BORROWED = 'BORROWED'
    RETURNED = 'RETURNED'
    STATUS_CHOICES = [
        (BORROWED, 'Borrowed'),
        (RETURNED, 'Returned'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    

    credits_spent = models.DecimalField(max_digits=6, decimal_places=2)      # Snapshots of rules at the time of borrowing
    borrowing_period = models.PositiveIntegerField()
    late_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=BORROWED)
    
    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title} [{self.status}]"

    def calculate_late_fee(self, return_time=None):
    
        if not return_time:
            return_time = timezone.now()

        if return_time <= self.due_date:
            return Decimal("0.00")
        overdue_days = (return_time - self.due_date).days

        if overdue_days <= 0:
            overdue_days = 1

        daily_charge = (self.credits_spent / Decimal(self.borrowing_period))

        if overdue_days <= 7:
            late_fee = daily_charge * overdue_days

        else:
            first_seven_days = daily_charge * 7
            extra_days = overdue_days - 7
            discounted_charge = (daily_charge * Decimal("0.50") * extra_days)
            late_fee = first_seven_days + discounted_charge
        return late_fee.quantize(Decimal("0.01"))