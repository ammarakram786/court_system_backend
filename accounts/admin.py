from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, RolePermission, PermissionOverride, Organization, Rank, Appointment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'name', 'svc_number', 'rank', 'organization', 'role', 'profile_status', 'is_staff', 'is_active')
    list_filter = ('profile_status', 'is_staff', 'is_active', 'organization', 'rank')
    search_fields = ('username', 'name', 'svc_number')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'svc_number', 'rank', 'appointment', 'organization', 'role', 'profile_image', 'profile_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code_name', 'name', 'app_name', 'module_name', 'created_at')
    list_filter = ('app_name', 'module_name')
    search_fields = ('code_name', 'name', 'module_name', 'app_name', 'description')
    ordering = ('app_name', 'module_name', 'name')


@admin.register(PermissionOverride)
class PermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission_code', 'effect', 'granted_by', 'expires_at', 'created_at')
    list_filter = ('effect', 'created_at')
    search_fields = ('permission_code', 'reason', 'granted_by')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'org_level', 'parent_organization', 'is_root', 'is_active', 'created_at')
    list_filter = ('is_active', 'org_level', 'is_root')
    search_fields = ('name', 'code')
    ordering = ('org_level', 'name')
    readonly_fields = ('org_level', 'is_root', 'created_at')


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('title', 'abbreviation', 'seniority_index', 'created_at')
    search_fields = ('title', 'abbreviation')
    ordering = ('seniority_index',)
    readonly_fields = ('created_at',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'appointment_code', 'created_at')
    search_fields = ('title', 'appointment_code')
    readonly_fields = ('created_at',)
