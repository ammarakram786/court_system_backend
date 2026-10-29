from django.core.exceptions import ValidationError
from .models import Organization, Rank, Appointment

def organization_create(*, parent_organization=None, name: str, code: str, is_active: bool = True) -> Organization:
    org = Organization(
        parent_organization=parent_organization,
        name=name,
        code=code,
        is_active=is_active
    )
    org.full_clean()
    org.save()
    return org

def organization_update(*, organization: Organization, **kwargs) -> Organization:
    for field, value in kwargs.items():
        setattr(organization, field, value)
    organization.full_clean()
    organization.save()
    return organization

def rank_create(*, title: str, abbreviation: str = None, seniority_index: int = 0) -> Rank:
    rank = Rank.objects.create(
        title=title,
        abbreviation=abbreviation,
        seniority_index=seniority_index
    )
    return rank

def appointment_create(*, title: str, appointment_code: str = None) -> Appointment:
    appointment = Appointment.objects.create(
        title=title,
        appointment_code=appointment_code
    )
    return appointment
