from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import Permission
from accounts.selectors import permission_list
from accounts.serializers.permission import PermissionSerializer
from accounts.permissions import HasPermissionCode


class PermissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all()
    filterset_fields = ['app_name', 'module_name']
    search_fields = ['code_name', 'module_name', 'app_name', 'name', 'description']
    ordering_fields = ['app_name', 'module_name', 'name', 'code_name', 'created_at']

    permission_prefix = 'permission'
    action_permissions = {
        'list': 'permission_read',
        'retrieve': 'permission_read',
        'create': 'permission_read',
        'update': 'permission_read',
        'partial_update': 'permission_read',
        'destroy': 'permission_read',
    }

    def get_queryset(self):
        return permission_list()
