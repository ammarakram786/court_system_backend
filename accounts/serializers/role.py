from rest_framework import serializers

from accounts.models import Permission, Role
from .permission import PermissionSerializer


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions'
    )

    class Meta:
        model = Role
        fields = ['role_id', 'id', 'name', 'description', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['role_id', 'id', 'created_at', 'updated_at']


class RoleMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'id', 'name']
        read_only_fields = ['role_id', 'id', 'name']
