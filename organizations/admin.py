from django.contrib import admin
from .models import Organization, Rank, Appointment

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
