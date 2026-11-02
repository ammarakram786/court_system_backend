from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import Role
from accounts.selectors import role_list
from accounts.serializers.role import RoleSerializer
from accounts.permissions import HasPermissionCode


class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    permission_prefix = 'role'
    action_permissions = {
        'list': 'role_read',
        'retrieve': 'role_read',
        'create': 'role_create',
        'update': 'role_update',
        'partial_update': 'role_update',
        'destroy': 'role_delete',
    }

    def get_queryset(self):
        return role_list()
