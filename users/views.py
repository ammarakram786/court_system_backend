from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Role, Permission, PermissionOverride
from .serializers import UserSerializer, RoleSerializer, PermissionSerializer, PermissionOverrideSerializer
from .selectors import user_list, role_list, permission_list

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filterset_fields = ['profile_status', 'organization', 'role', 'rank', 'is_active']
    search_fields = ['username', 'name', 'svc_number']
    ordering_fields = ['name', 'username', 'created_at']

    def get_queryset(self):
        return user_list()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        return role_list()


class PermissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all()
    filterset_fields = ['module']
    search_fields = ['code', 'module', 'description']
    ordering_fields = ['module', 'code', 'created_at']

    def get_queryset(self):
        return permission_list()


class PermissionOverrideViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionOverrideSerializer
    queryset = PermissionOverride.objects.all()
    filterset_fields = ['user', 'effect', 'permission_code']
    search_fields = ['permission_code', 'reason', 'granted_by']
    ordering_fields = ['created_at', 'expires_at']
