from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import Organization, Rank, Appointment
from accounts.serializers.organization import OrganizationSerializer, RankSerializer, AppointmentSerializer
from accounts.selectors import organization_list, rank_list, appointment_list
from accounts.permissions import HasPermissionCode


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    filterset_fields = ['is_active', 'org_level', 'parent_organization', 'is_root']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'org_level', 'created_at']

    permission_prefix = 'organization'
    action_permissions = {
        'list': 'organization_read',
        'retrieve': 'organization_read',
        'create': 'organization_create',
        'update': 'organization_update',
        'partial_update': 'organization_update',
        'destroy': 'organization_delete',
        'root': 'organization_read',
        'sub_organizations': 'organization_read',
    }

    def get_queryset(self):
        return organization_list()

    @action(detail=False, methods=['get'], url_path='root')
    def root(self, request):
        root_org = Organization.objects.filter(parent_organization__isnull=True).first()
        if not root_org:
            return Response(
                {'status': 'error', 'detail': 'No root organization configured.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(root_org)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='sub-organizations')
    def sub_organizations(self, request, pk=None):
        org = self.get_object()
        subs = org.sub_organizations.filter(is_active=True)
        serializer = self.get_serializer(subs, many=True)
        return Response(serializer.data)


class RankViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = RankSerializer
    queryset = Rank.objects.all()
    search_fields = ['title', 'abbreviation']
    ordering_fields = ['seniority_index', 'title', 'created_at']

    permission_prefix = 'rank'
    action_permissions = {
        'list': 'rank_read',
        'retrieve': 'rank_read',
        'create': 'rank_create',
        'update': 'rank_update',
        'partial_update': 'rank_update',
        'destroy': 'rank_delete',
    }

    def get_queryset(self):
        return rank_list()


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    search_fields = ['title', 'appointment_code']
    ordering_fields = ['title', 'created_at']

    permission_prefix = 'appointment'
    action_permissions = {
        'list': 'appointment_read',
        'retrieve': 'appointment_read',
        'create': 'appointment_create',
        'update': 'appointment_update',
        'partial_update': 'appointment_update',
        'destroy': 'appointment_delete',
    }

    def get_queryset(self):
        return appointment_list()
