from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding, CauseList, CauseListItem
from .serializers import (
    CourtSerializer, PoliceStationSerializer, CaseCategorySerializer,
    CaseSerializer, CasePartySerializer, CaseProceedingSerializer,
    CauseListSerializer, CauseListItemSerializer
)
from .selectors import court_list, police_station_list, case_category_list, case_list, cause_list_queryset
from .filters import CaseFilter, CaseProceedingFilter

class CourtViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourtSerializer
    queryset = Court.objects.all()
    filterset_fields = ['district', 'is_active']
    search_fields = ['court_name', 'presiding_officer', 'designation']
    ordering_fields = ['court_name', 'created_at']

    def get_queryset(self):
        return court_list()


class PoliceStationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PoliceStationSerializer
    queryset = PoliceStation.objects.all()
    filterset_fields = ['district']
    search_fields = ['name', 'code']
    ordering_fields = ['name']

    def get_queryset(self):
        return police_station_list()


class CaseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseCategorySerializer
    queryset = CaseCategory.objects.all()
    filterset_fields = ['nature']
    search_fields = ['name', 'short_code']
    ordering_fields = ['nature', 'name']

    def get_queryset(self):
        return case_category_list()


class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filterset_class = CaseFilter
    search_fields = ['case_number', 'case_title', 'fir_number', 'offence_sections']
    ordering_fields = ['institution_date', 'case_number', 'created_at']

    def get_queryset(self):
        return case_list()


class CasePartyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CasePartySerializer
    queryset = CaseParty.objects.all()
    filterset_fields = ['case', 'party_side', 'is_primary_party']
    search_fields = ['party_name', 'counsel_name', 'cnic', 'contact_number']
    ordering_fields = ['party_name', 'party_side']


class CaseProceedingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseProceedingSerializer
    queryset = CaseProceeding.objects.all()
    filterset_class = CaseProceedingFilter
    search_fields = ['stage', 'today_action', 'short_order']
    ordering_fields = ['proceeding_date', 'sr_no']


class CauseListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CauseListSerializer
    queryset = CauseList.objects.all()
    filterset_fields = ['court', 'cause_list_date', 'day_of_week']
    search_fields = ['day_of_week']
    ordering_fields = ['cause_list_date']

    def get_queryset(self):
        return cause_list_queryset()


class CauseListItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CauseListItemSerializer
    queryset = CauseListItem.objects.all()
    filterset_fields = ['cause_list', 'case']
    search_fields = ['category_heading']
    ordering_fields = ['roster_sr_no']
