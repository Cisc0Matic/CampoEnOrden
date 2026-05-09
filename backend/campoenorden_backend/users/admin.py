from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'telefono', 'empresa', 'permisos_especiales')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'telefono', 'empresa')}),
    )
    list_display = ('username', 'email', 'role', 'telefono', 'empresa', 'is_active')
    list_filter = ('role', 'is_active')
