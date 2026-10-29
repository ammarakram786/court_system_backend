import django_filters
from .models import Case, CaseProceeding, CauseList

class CaseFilter(django_filters.FilterSet):
    institution_date_after = django_filters.DateFilter(field_name='institution_date', lookup_expr='gte')
    institution_date_before = django_filters.DateFilter(field_name='institution_date', lookup_expr='lte')
    fir_year = django_filters.NumberFilter(field_name='fir_year')

    class Meta:
        model = Case
        fields = {
            'status': ['exact', 'in'],
            'court': ['exact'],
            'category': ['exact'],
            'managing_organization': ['exact'],
            'assigned_case_officer': ['exact'],
            'police_station': ['exact'],
            'fir_number': ['exact', 'icontains'],
        }


class CaseProceedingFilter(django_filters.FilterSet):
    proceeding_date_after = django_filters.DateFilter(field_name='proceeding_date', lookup_expr='gte')
    proceeding_date_before = django_filters.DateFilter(field_name='proceeding_date', lookup_expr='lte')

    class Meta:
        model = CaseProceeding
        fields = {
            'case': ['exact'],
            'court': ['exact'],
            'stage': ['exact', 'icontains'],
            'is_case_decided': ['exact'],
        }
