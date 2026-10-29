from rest_framework import serializers
from .models import Organization, Rank, Appointment

class OrganizationSerializer(serializers.ModelSerializer):
    sub_organizations_count = serializers.IntegerField(source='sub_organizations.count', read_only=True)

    class Meta:
        model = Organization
        fields = [
            'organization_id',
            'parent_organization',
            'name',
            'code',
            'org_level',
            'is_active',
            'created_at',
            'sub_organizations_count'
        ]
        read_only_fields = ['organization_id', 'org_level', 'created_at']

    def validate(self, attrs):
        # Additional custom validation if needed
        return super().validate(attrs)


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = ['rank_id', 'title', 'abbreviation', 'seniority_index', 'created_at']
        read_only_fields = ['rank_id', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['appointment_id', 'title', 'appointment_code', 'created_at']
        read_only_fields = ['appointment_id', 'created_at']
