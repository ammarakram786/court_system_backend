from django.db.models import QuerySet
from .models import Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding, CauseList, CauseListItem

def court_list() -> QuerySet[Court]:
    return Court.objects.all()

def police_station_list() -> QuerySet[PoliceStation]:
    return PoliceStation.objects.all()

def case_category_list() -> QuerySet[CaseCategory]:
    return CaseCategory.objects.all()

def case_list() -> QuerySet[Case]:
    return Case.objects.select_related(
        'court', 'category', 'managing_organization', 'assigned_case_officer', 'police_station'
    ).prefetch_related('parties', 'proceedings').all()

def case_get(*, case_id) -> Case:
    return Case.objects.select_related(
        'court', 'category', 'managing_organization', 'assigned_case_officer', 'police_station'
    ).prefetch_related('parties', 'proceedings', 'parties__case').get(pk=case_id)

def cause_list_queryset() -> QuerySet[CauseList]:
    return CauseList.objects.select_related('court').prefetch_related('items__case', 'items__proceeding').all()
