from rest_framework import serializers
from .models import User, Role, Permission, PermissionOverride
from organizations.serializers import OrganizationSerializer, RankSerializer, AppointmentSerializer

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['permission_id', 'code', 'module', 'description', 'created_at']
        read_only_fields = ['permission_id', 'created_at']


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
        fields = ['role_id', 'name', 'description', 'permissions', 'permission_ids', 'created_at']
        read_only_fields = ['role_id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    rank_details = RankSerializer(source='rank', read_only=True)
    appointment_details = AppointmentSerializer(source='appointment', read_only=True)
    organization_details = OrganizationSerializer(source='organization', read_only=True)
    role_details = RoleSerializer(source='role', read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'user_id',
            'username',
            'name',
            'profile_status',
            'svc_number',
            'rank',
            'rank_details',
            'appointment',
            'appointment_details',
            'organization',
            'organization_details',
            'role',
            'role_details',
            'profile_image',
            'is_staff',
            'is_active',
            'password',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class PermissionOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionOverride
        fields = ['override_id', 'user', 'permission_code', 'effect', 'reason', 'granted_by', 'expires_at', 'created_at']
        read_only_fields = ['override_id', 'created_at']
