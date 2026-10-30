from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
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

    def perform_create(self, serializer):
        kwargs = {}
        if not serializer.validated_data.get('managing_organization') and getattr(self.request.user, 'organization', None):
            kwargs['managing_organization'] = self.request.user.organization
        if not serializer.validated_data.get('assigned_case_officer'):
            kwargs['assigned_case_officer'] = self.request.user
        serializer.save(**kwargs)

    @action(detail=True, methods=['get', 'post'], url_path='proceedings')
    def proceedings(self, request, pk=None):
        case = self.get_object()
        if request.method == 'GET':
            proceedings = case.proceedings.select_related(
                'court', 'recorded_by'
            ).order_by('sr_no')
            serializer = CaseProceedingSerializer(proceedings, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            data = request.data.copy()
            data['case'] = case.case_id
            if 'court' not in data:
                data['court'] = case.court_id
            serializer = CaseProceedingSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            recorded_by = serializer.validated_data.get('recorded_by') or request.user
            proceeding = serializer.save(recorded_by=recorded_by)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='parties')
    def parties(self, request, pk=None):
        case = self.get_object()
        if request.method == 'GET':
            parties = case.parties.all().order_by('party_name')
            serializer = CasePartySerializer(parties, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            data = request.data.copy()
            data['case'] = case.case_id
            serializer = CasePartySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='close')
    def close_case(self, request, pk=None):
        case = self.get_object()
        new_status = request.data.get('status', Case.CaseStatus.DECIDED)
        decision_date = request.data.get('decision_date', timezone.localdate().isoformat())
        if new_status not in [Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED, Case.CaseStatus.CONSIGNED]:
            return Response(
                {'status': 'error', 'detail': f"Invalid closing status: {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        case.status = new_status
        case.decision_date = decision_date
        case.save(update_fields=['status', 'decision_date', 'updated_at'])
        return Response(CaseSerializer(case).data)


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

    def perform_create(self, serializer):
        kwargs = {}
        if not serializer.validated_data.get('recorded_by') and self.request.user.is_authenticated:
            kwargs['recorded_by'] = self.request.user
        serializer.save(**kwargs)


class CauseListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CauseListSerializer
    queryset = CauseList.objects.all()
    filterset_fields = ['court', 'cause_list_date', 'day_of_week']
    search_fields = ['day_of_week']
    ordering_fields = ['cause_list_date']

    def get_queryset(self):
        return cause_list_queryset()

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        today_date = timezone.localdate()
        cause_lists = self.get_queryset().filter(cause_list_date=today_date)
        serializer = self.get_serializer(cause_lists, many=True)
        return Response(serializer.data)


class CauseListItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CauseListItemSerializer
    queryset = CauseListItem.objects.all()
    filterset_fields = ['cause_list', 'case']
    search_fields = ['category_heading']
    ordering_fields = ['roster_sr_no']
