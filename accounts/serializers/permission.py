from rest_framework import serializers
from accounts.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            'permission_id',
            'id',
            'app_name',
            'module_name',
            'name',
            'code_name',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['permission_id', 'id', 'created_at', 'updated_at']
