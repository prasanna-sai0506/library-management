from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'credits', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Library Details', {'fields': ('role', 'credits')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library Details', {'fields': ('role', 'credits')}),
    )