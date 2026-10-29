from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Organization, Rank, Appointment
from .serializers import OrganizationSerializer, RankSerializer, AppointmentSerializer
from .selectors import organization_list, rank_list, appointment_list

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    filterset_fields = ['is_active', 'org_level', 'parent_organization']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'org_level', 'created_at']

    def get_queryset(self):
        return organization_list()


class RankViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RankSerializer
    queryset = Rank.objects.all()
    search_fields = ['title', 'abbreviation']
    ordering_fields = ['seniority_index', 'title', 'created_at']

    def get_queryset(self):
        return rank_list()


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    search_fields = ['title', 'appointment_code']
    ordering_fields = ['title', 'created_at']

    def get_queryset(self):
        return appointment_list()
