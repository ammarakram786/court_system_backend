from django.test import TestCase
from django.core.exceptions import ValidationError
from organizations.models import Organization, Rank, Appointment
from organizations.services import organization_create, rank_create, appointment_create

class OrganizationModelTests(TestCase):
    def test_single_root_organization_constraint(self):
        root1 = organization_create(name="Root HQ", code="HQ-001")
        self.assertEqual(root1.org_level, 1)
        self.assertIsNone(root1.parent_organization)

        # Attempting to create second root should raise ValidationError
        with self.assertRaises(ValidationError):
            organization_create(name="Second Root HQ", code="HQ-002")

    def test_sub_organization_creation(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        sub1 = organization_create(parent_organization=root, name="Legal Directorate", code="LD-001")
        self.assertEqual(sub1.org_level, 2)
        self.assertEqual(sub1.parent_organization, root)


class RankAppointmentTests(TestCase):
    def test_rank_and_appointment_creation(self):
        rank = rank_create(title="Major", abbreviation="Maj", seniority_index=10)
        self.assertEqual(str(rank), "Major (Maj)")

        appt = appointment_create(title="Legal Officer", appointment_code="LO-01")
        self.assertEqual(str(appt), "Legal Officer")
