from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'total_copies', 'available_copies', 'availability', 'borrowing_cost']
    list_filter = ['category', 'availability']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['created_at']