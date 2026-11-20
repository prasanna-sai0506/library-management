from django.contrib import admin
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from .models import Borrowing, UnderDeskBook
@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'status', 'borrowed_at', 'due_date', 'returned_at', 'credits_spent', 'late_fee']
    list_filter = ['status', 'borrowed_at']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['borrowed_at', 'credits_spent', 'borrowing_period']


@admin.register(UnderDeskBook)
class UnderDeskBookAdmin(admin.ModelAdmin):
    list_display = ['book', 'borrower', 'placed_at', 'move_to_shelf']
    list_filter = ['placed_at', 'book']
    search_fields = ['book__title', 'book__isbn', 'borrowing__user__username']
    readonly_fields = ['borrowing', 'book', 'placed_at']
    actions = ['move_selected_to_shelf', 'move_all_to_shelf']

    def borrower(self, obj):
        return obj.borrowing.user

    borrower.admin_order_field = 'borrowing__user'

    def move_to_shelf(self, obj):
        url = reverse('admin:borrowings_underdeskbook_changelist')
        return format_html('<a href="{}">Under desk</a>', url)

    move_to_shelf.short_description = 'Location'

    @admin.action(description='Move selected copies to the shelf')
    def move_selected_to_shelf(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} under-desk copy/copies moved to the shelf.', messages.SUCCESS)

    @admin.action(description='Move all under-desk copies to the shelf')
    def move_all_to_shelf(self, request, queryset):
        count = UnderDeskBook.objects.count()
        UnderDeskBook.objects.all().delete()
        self.message_user(request, f'{count} under-desk copy/copies moved to the shelf.', messages.SUCCESS)