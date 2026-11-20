from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Book, Shelf

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'shelf_location', 'total_copies',
        'available_copies', 'availability', 'borrowing_cost',
    ]
    list_filter = ['category', 'availability']
    autocomplete_fields = ['shelf']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['created_at', 'shelf_location']
    list_display = [
        'title', 'author', 'category', 'shelf_location', 'total_copies',
        'available_copies', 'under_desk_count', 'shelf_copy_count',
        'availability', 'borrowing_cost',
    ]

    def under_desk_count(self, obj):
        count = obj.under_desk_copies.count()
        if not count:
            return '0'
        url = reverse('admin:borrowings_underdeskbook_changelist') + f'?book__id__exact={obj.id}'
        return format_html('<a href="{}">{} under desk</a>', url, count)

    under_desk_count.short_description = 'Under desk'

    def shelf_copy_count(self, obj):
        count = max(obj.available_copies - obj.under_desk_copies.count(), 0)
        return count

    shelf_copy_count.short_description = 'Shelf copies'


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'placements']