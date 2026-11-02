from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import PermissionOverride
from accounts.selectors import permission_override_list
from accounts.serializers.override import PermissionOverrideSerializer
from accounts.permissions import HasPermissionCode


class PermissionOverrideViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = PermissionOverrideSerializer
    queryset = PermissionOverride.objects.all()
    filterset_fields = ['user', 'effect', 'permission_code']
    search_fields = ['permission_code', 'reason', 'granted_by']
    ordering_fields = ['created_at', 'expires_at']

    permission_prefix = 'override'
    action_permissions = {
        'list': 'override_read',
        'retrieve': 'override_read',
        'create': 'override_create',
        'update': 'override_update',
        'partial_update': 'override_update',
        'destroy': 'override_delete',
    }

    def get_queryset(self):
        return permission_override_list()
