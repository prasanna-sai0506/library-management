from django.contrib import admin
from .models import Borrowing
@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'status', 'borrowed_at', 'due_date', 'returned_at', 'credits_spent', 'late_fee']
    list_filter = ['status', 'borrowed_at']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['borrowed_at', 'credits_spent', 'borrowing_period']