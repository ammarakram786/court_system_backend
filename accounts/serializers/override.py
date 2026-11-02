from rest_framework import serializers
from accounts.models import PermissionOverride


class PermissionOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionOverride
        fields = [
            'override_id',
            'id',
            'user',
            'permission_code',
            'effect',
            'reason',
            'granted_by',
            'expires_at',
            'created_at',
        ]
        read_only_fields = ['override_id', 'id', 'created_at']
