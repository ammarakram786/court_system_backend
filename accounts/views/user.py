from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.selectors import user_list
from accounts.serializers.change_password import ChangePasswordSerializer
from accounts.serializers.user import UserSerializer
from accounts.permissions import HasPermissionCode


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filterset_fields = ['profile_status', 'organization', 'role', 'rank', 'is_active']
    search_fields = ['username', 'name', 'svc_number']
    ordering_fields = ['name', 'username', 'created_at']

    permission_prefix = 'user'
    action_permissions = {
        'list': 'user_read',
        'retrieve': 'user_read',
        'create': 'user_create',
        'update': 'user_update',
        'partial_update': 'user_update',
        'destroy': 'user_delete',
        'me': None,
        'change_password': None,
    }

    def get_queryset(self):
        return user_list()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'status': 'success', 'detail': 'Password updated successfully.'})
