from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, RolePermission, PermissionOverride

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'name', 'svc_number', 'rank', 'appointment',
        'organization', 'role', 'profile_status', 'is_staff', 'is_active'
    )
    list_filter = ('profile_status', 'is_staff', 'is_active', 'organization', 'role', 'rank')
    search_fields = ('username', 'name', 'svc_number')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'svc_number', 'rank', 'appointment', 'profile_image')}),
        ('Organization & Role', {'fields': ('organization', 'role', 'profile_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'svc_number', 'name', 'password',
                'organization', 'role', 'is_staff', 'is_superuser'
            ),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    inlines = [RolePermissionInline]
    readonly_fields = ('created_at',)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'module', 'description', 'created_at')
    list_filter = ('module',)
    search_fields = ('code', 'module', 'description')
    readonly_fields = ('created_at',)


@admin.register(PermissionOverride)
class PermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission_code', 'effect', 'granted_by', 'expires_at', 'created_at')
    list_filter = ('effect', 'permission_code')
    search_fields = ('user__username', 'permission_code', 'reason', 'granted_by')
    readonly_fields = ('created_at',)
