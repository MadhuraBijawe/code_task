"""
users/admin.py

Register models with the Django admin site.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, Message


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the extended User model."""
    list_display = ('email', 'name', 'mobile', 'is_verified', 'is_staff', 'date_joined')
    list_filter = ('is_verified', 'is_staff', 'is_active')
    search_fields = ('email', 'name', 'mobile')
    ordering = ('-date_joined',)

    # Add custom fields to the detail view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {
            'fields': ('name', 'mobile', 'profile_image', 'latitude', 'longitude', 'is_verified'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile', {
            'fields': ('name', 'email', 'mobile', 'profile_image', 'latitude', 'longitude'),
        }),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'code')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('sender__email', 'content')
