from django.db.models import QuerySet, Count
from .models import Organization, Rank, Appointment

def organization_list() -> QuerySet[Organization]:
    return Organization.objects.select_related('parent_organization').annotate(
        _sub_organizations_count=Count('sub_organizations')
    ).all()

def organization_get(*, organization_id) -> Organization:
    return Organization.objects.select_related('parent_organization').annotate(
        _sub_organizations_count=Count('sub_organizations')
    ).get(pk=organization_id)

def rank_list() -> QuerySet[Rank]:
    return Rank.objects.all()

def appointment_list() -> QuerySet[Appointment]:
    return Appointment.objects.all()
