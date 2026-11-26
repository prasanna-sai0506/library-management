from django.db import models
from decimal import Decimal

AVAILABLE = "AVAILABLE"
UNAVAILABLE = "UNAVAILABLE"
AVAILABILITY_CHOICES = [
    (AVAILABLE, "Available"),
    (UNAVAILABLE, "Unavailable"),
]


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.CharField(max_length=100)
    shelf_location = models.CharField(max_length=1000, blank=True, default="")
    shelf = models.ForeignKey(
        "Shelf",
        on_delete=models.PROTECT,
        related_name="books",
        blank=True,
        null=True,
    )
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    availability = models.CharField(
        max_length=20, choices=AVAILABILITY_CHOICES, default=AVAILABLE
    )
    borrowing_cost = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("5.00")
    )
    borrowing_period = models.PositiveIntegerField(default=7)  # in days
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.shelf_id:
            shelf_name = (
                type(self)
                .shelf.field.remote_field.model.objects.filter(pk=self.shelf_id)
                .values_list("name", flat=True)
                .first()
            )
            if shelf_name:
                self.shelf_location = shelf_name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.author}"


class Shelf(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=True, default="")
    column_name = models.CharField(max_length=10, default="A")
    shelf_number = models.PositiveIntegerField(default=1)
    capacity = models.PositiveIntegerField()
    placements = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.column_name = self.column_name.strip().upper()
        self.name = f"{self.column_name}-{self.shelf_number:02d}"
        super().save(*args, **kwargs)
