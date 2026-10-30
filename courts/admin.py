from django.contrib import admin
from .models import Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding, CauseList, CauseListItem

class CasePartyInline(admin.TabularInline):
    model = CaseParty
    extra = 1

class CaseProceedingInline(admin.StackedInline):
    model = CaseProceeding
    extra = 0
    ordering = ('sr_no',)

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('court_name', 'district', 'presiding_officer', 'designation', 'court_room_no', 'is_active')
    list_filter = ('district', 'is_active')
    search_fields = ('court_name', 'presiding_officer', 'designation')
    readonly_fields = ('created_at',)


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'code')
    list_filter = ('district',)
    search_fields = ('name', 'code')


@admin.register(CaseCategory)
class CaseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'nature', 'short_code')
    list_filter = ('nature',)
    search_fields = ('name', 'short_code')


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'case_number', 'case_title', 'court', 'category',
        'managing_organization', 'assigned_case_officer', 'status', 'institution_date'
    )
    list_filter = ('status', 'court', 'category', 'managing_organization')
    search_fields = ('case_number', 'case_title', 'fir_number', 'offence_sections')
    inlines = [CasePartyInline, CaseProceedingInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CaseParty)
class CasePartyAdmin(admin.ModelAdmin):
    list_display = ('party_name', 'party_side', 'case', 'is_primary_party', 'counsel_name', 'cnic', 'contact_number')
    list_filter = ('party_side', 'is_primary_party')
    search_fields = ('party_name', 'counsel_name', 'cnic', 'case__case_number')


@admin.register(CaseProceeding)
class CaseProceedingAdmin(admin.ModelAdmin):
    list_display = ('case', 'sr_no', 'court', 'proceeding_date', 'stage', 'is_case_decided', 'next_proceeding_date')
    list_filter = ('court', 'is_case_decided', 'stage')
    search_fields = ('case__case_number', 'stage', 'today_action', 'short_order')
    readonly_fields = ('created_at',)


class CauseListItemInline(admin.TabularInline):
    model = CauseListItem
    extra = 1
    ordering = ('roster_sr_no',)


@admin.register(CauseList)
class CauseListAdmin(admin.ModelAdmin):
    list_display = ('court', 'cause_list_date', 'day_of_week', 'created_at')
    list_filter = ('court', 'cause_list_date', 'day_of_week')
    search_fields = ('court__court_name', 'day_of_week')
    inlines = [CauseListItemInline]
    readonly_fields = ('created_at',)
