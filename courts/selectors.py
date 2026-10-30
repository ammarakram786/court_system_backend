from django.db.models import QuerySet, Prefetch
from .models import Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding, CauseList, CauseListItem

def court_list() -> QuerySet[Court]:
    return Court.objects.all()

def police_station_list() -> QuerySet[PoliceStation]:
    return PoliceStation.objects.all()

def case_category_list() -> QuerySet[CaseCategory]:
    return CaseCategory.objects.all()

def case_list() -> QuerySet[Case]:
    proceedings_qs = CaseProceeding.objects.select_related(
        'court',
        'recorded_by__rank',
        'recorded_by__appointment',
        'recorded_by__organization',
        'recorded_by__role'
    )
    return Case.objects.select_related(
        'court',
        'category',
        'managing_organization',
        'assigned_case_officer__rank',
        'assigned_case_officer__appointment',
        'assigned_case_officer__organization',
        'assigned_case_officer__role',
        'police_station'
    ).prefetch_related(
        'parties',
        Prefetch('proceedings', queryset=proceedings_qs)
    ).all()

def case_get(*, case_id) -> Case:
    proceedings_qs = CaseProceeding.objects.select_related(
        'court',
        'recorded_by__rank',
        'recorded_by__appointment',
        'recorded_by__organization',
        'recorded_by__role'
    )
    return Case.objects.select_related(
        'court',
        'category',
        'managing_organization',
        'assigned_case_officer__rank',
        'assigned_case_officer__appointment',
        'assigned_case_officer__organization',
        'assigned_case_officer__role',
        'police_station'
    ).prefetch_related(
        'parties',
        Prefetch('proceedings', queryset=proceedings_qs)
    ).get(pk=case_id)

def cause_list_queryset() -> QuerySet[CauseList]:
    items_qs = CauseListItem.objects.select_related(
        'case__court',
        'case__category',
        'case__managing_organization',
        'proceeding__court',
        'proceeding__recorded_by'
    )
    return CauseList.objects.select_related('court').prefetch_related(
        Prefetch('items', queryset=items_qs)
    ).all()
