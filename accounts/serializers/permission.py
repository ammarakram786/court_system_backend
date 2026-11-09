from rest_framework import serializers
from accounts.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='code_name', read_only=True)
    module = serializers.CharField(source='module_name', read_only=True)

    class Meta:
        model = Permission
        fields = [
            'permission_id',
            'id',
            'app_name',
            'module_name',
            'module',
            'name',
            'code_name',
            'code',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['permission_id', 'id', 'code', 'module', 'created_at', 'updated_at']
