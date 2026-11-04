from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import User
from accounts.permissions import HasPermissionCode
from .models import (
    Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding,
    CauseList, CauseListItem, CaseMarkingHistory
)
from .serializers import (
    CourtSerializer, PoliceStationSerializer, CaseCategorySerializer,
    CaseSerializer, CasePartySerializer, CaseProceedingSerializer,
    CauseListSerializer, CauseListItemSerializer,
    CaseMarkingHistorySerializer, CaseMarkSerializer, CaseMarkBackSerializer,
    CaseTimelineEventSerializer
)
from .selectors import (
    court_list, police_station_list, case_category_list,
    case_list, cause_list_queryset, case_marking_history_list,
    case_timeline
)
from .services import case_mark, case_mark_back
from .permissions import CanWorkOnCaseOrReadOnly, can_user_work_on_case
from .filters import CaseFilter, CaseProceedingFilter


class CourtViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = CourtSerializer
    queryset = Court.objects.all()
    filterset_fields = ['district', 'is_active']
    search_fields = ['court_name', 'presiding_officer', 'designation']
    ordering_fields = ['court_name', 'created_at']

    permission_prefix = 'court'
    action_permissions = {
        'list': 'court_read',
        'retrieve': 'court_read',
        'create': 'court_create',
        'update': 'court_update',
        'partial_update': 'court_update',
        'destroy': 'court_delete',
    }

    def get_queryset(self):
        return court_list()


class PoliceStationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = PoliceStationSerializer
    queryset = PoliceStation.objects.all()
    filterset_fields = ['district']
    search_fields = ['name', 'code']
    ordering_fields = ['name']

    permission_prefix = 'police_station'
    action_permissions = {
        'list': 'police_station_read',
        'retrieve': 'police_station_read',
        'create': 'police_station_create',
        'update': 'police_station_update',
        'partial_update': 'police_station_update',
        'destroy': 'police_station_delete',
    }

    def get_queryset(self):
        return police_station_list()


class CaseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = CaseCategorySerializer
    queryset = CaseCategory.objects.all()
    filterset_fields = ['nature']
    search_fields = ['name', 'short_code']
    ordering_fields = ['nature', 'name']

    permission_prefix = 'case_category'
    action_permissions = {
        'list': 'case_category_read',
        'retrieve': 'case_category_read',
        'create': 'case_category_create',
        'update': 'case_category_update',
        'partial_update': 'case_category_update',
        'destroy': 'case_category_delete',
    }

    def get_queryset(self):
        return case_category_list()


class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode, CanWorkOnCaseOrReadOnly]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()
    filterset_class = CaseFilter
    search_fields = ['case_number', 'case_title', 'fir_number', 'offence_sections']
    ordering_fields = ['institution_date', 'case_number', 'created_at']

    permission_prefix = 'case'
    action_permissions = {
        'list': 'case_read',
        'retrieve': 'case_read',
        'create': 'case_create',
        'update': 'case_update',
        'partial_update': 'case_update',
        'destroy': 'case_delete',
        'proceedings': 'case_read',
        'parties': 'case_read',
        'close_case': 'case_close',
        'mark': 'case_mark',
        'mark_back': 'case_mark_back',
        'marking_history': 'case_read',
        'timeline': 'case_read',
    }

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
        return Response(CaseSerializer(case, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='mark')
    def mark(self, request, pk=None):
        case = self.get_object()
        serializer = CaseMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_user_id = serializer.validated_data['to_user_id']
        remarks = serializer.validated_data.get('remarks', '')
        try:
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            return Response(
                {'status': 'error', 'detail': f"Target officer with ID {to_user_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        updated_case = case_mark(
            case=case,
            from_user=request.user,
            to_user=to_user,
            remarks=remarks
        )
        return Response(CaseSerializer(updated_case, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='mark-back')
    def mark_back(self, request, pk=None):
        case = self.get_object()
        serializer = CaseMarkBackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remarks = serializer.validated_data.get('remarks', '')
        updated_case = case_mark_back(
            case=case,
            from_user=request.user,
            remarks=remarks
        )
        return Response(CaseSerializer(updated_case, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='marking-history')
    def marking_history(self, request, pk=None):
        case = self.get_object()
        history = case_marking_history_list(case_id=case.case_id)
        serializer = CaseMarkingHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='timeline')
    def timeline(self, request, pk=None):
        case = self.get_object()
        order = request.query_params.get('order', 'desc')
        events = case_timeline(case=case, order=order)
        serializer = CaseTimelineEventSerializer(events, many=True)
        return Response(serializer.data)


class CasePartyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode, CanWorkOnCaseOrReadOnly]
    serializer_class = CasePartySerializer
    queryset = CaseParty.objects.all()
    filterset_fields = ['case', 'party_side', 'is_primary_party']
    search_fields = ['party_name', 'counsel_name', 'cnic', 'contact_number']
    ordering_fields = ['party_name', 'party_side']

    permission_prefix = 'case_party'
    action_permissions = {
        'list': 'case_party_read',
        'retrieve': 'case_party_read',
        'create': 'case_party_create',
        'update': 'case_party_update',
        'partial_update': 'case_party_update',
        'destroy': 'case_party_delete',
    }

    def perform_create(self, serializer):
        case = serializer.validated_data.get('case')
        if case and not can_user_work_on_case(self.request.user, case):
            raise PermissionDenied("You have view-only access to this case. Only the assigned officer or peers can add parties.")
        serializer.save()


class CaseProceedingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode, CanWorkOnCaseOrReadOnly]
    serializer_class = CaseProceedingSerializer
    queryset = CaseProceeding.objects.all()
    filterset_class = CaseProceedingFilter
    search_fields = ['stage', 'today_action', 'short_order']
    ordering_fields = ['proceeding_date', 'sr_no']

    permission_prefix = 'case_proceeding'
    action_permissions = {
        'list': 'case_proceeding_read',
        'retrieve': 'case_proceeding_read',
        'create': 'case_proceeding_create',
        'update': 'case_proceeding_update',
        'partial_update': 'case_proceeding_update',
        'destroy': 'case_proceeding_delete',
    }

    def perform_create(self, serializer):
        case = serializer.validated_data.get('case')
        if case and not can_user_work_on_case(self.request.user, case):
            raise PermissionDenied("You have view-only access to this case. Only the assigned officer or peers can record proceedings.")
        kwargs = {}
        if not serializer.validated_data.get('recorded_by') and self.request.user.is_authenticated:
            kwargs['recorded_by'] = self.request.user
        serializer.save(**kwargs)


class CauseListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = CauseListSerializer
    queryset = CauseList.objects.all()
    filterset_fields = ['court', 'cause_list_date', 'day_of_week']
    search_fields = ['day_of_week']
    ordering_fields = ['cause_list_date']

    permission_prefix = 'cause_list'
    action_permissions = {
        'list': 'cause_list_read',
        'retrieve': 'cause_list_read',
        'create': 'cause_list_create',
        'update': 'cause_list_update',
        'partial_update': 'cause_list_update',
        'destroy': 'cause_list_delete',
        'today': 'cause_list_read',
    }

    def get_queryset(self):
        return cause_list_queryset()

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        today_date = timezone.localdate()
        cause_lists = self.get_queryset().filter(cause_list_date=today_date)
        serializer = self.get_serializer(cause_lists, many=True)
        return Response(serializer.data)


class CauseListItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = CauseListItemSerializer
    queryset = CauseListItem.objects.all()
    filterset_fields = ['cause_list', 'case']
    search_fields = ['category_heading']
    ordering_fields = ['roster_sr_no']

    permission_prefix = 'cause_list_item'
    action_permissions = {
        'list': 'cause_list_item_read',
        'retrieve': 'cause_list_item_read',
        'create': 'cause_list_item_create',
        'update': 'cause_list_item_update',
        'partial_update': 'cause_list_item_update',
        'destroy': 'cause_list_item_delete',
    }
