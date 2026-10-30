from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APIClient
from organizations.models import Organization, Rank, Appointment
from organizations.services import organization_create, rank_create, appointment_create
from users.services import user_create, role_create

class OrganizationModelTests(TestCase):
    def test_single_root_organization_constraint(self):
        root1 = organization_create(name="Root HQ", code="HQ-001")
        self.assertEqual(root1.org_level, 1)
        self.assertIsNone(root1.parent_organization)
        self.assertTrue(root1.is_root)

        # Attempting to create second root via service/clean should raise ValidationError
        with self.assertRaises(ValidationError):
            organization_create(name="Second Root HQ", code="HQ-002")

    def test_db_level_unique_root_constraint(self):
        root1 = organization_create(name="Root HQ", code="HQ-001")
        # Attempting to bypass clean() directly into DB should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Organization.objects.bulk_create([
                Organization(name="Direct DB Root", code="HQ-DIR", is_root=True, org_level=1)
            ])

    def test_sub_organization_creation(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        sub1 = organization_create(parent_organization=root, name="Legal Directorate", code="LD-001")
        self.assertEqual(sub1.org_level, 2)
        self.assertEqual(sub1.parent_organization, root)
        self.assertFalse(sub1.is_root)

    def test_circular_organization_prevention(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        sub1 = organization_create(parent_organization=root, name="Legal Directorate", code="LD-001")
        # Attempt to make root its own child or sub1's child
        root.parent_organization = sub1
        with self.assertRaises(ValidationError):
            root.save()

    def test_self_parent_prevention(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        root.parent_organization = root
        with self.assertRaises(ValidationError):
            root.save()


class RankAppointmentTests(TestCase):
    def test_rank_and_appointment_creation(self):
        rank = rank_create(title="Major", abbreviation="Maj", seniority_index=10)
        self.assertEqual(str(rank), "Major (Maj)")

        appt = appointment_create(title="Legal Officer", appointment_code="LO-01")
        self.assertEqual(str(appt), "Legal Officer")


class OrganizationAPITests(TestCase):
    def setUp(self):
        self.root = organization_create(name="Root HQ", code="HQ-ROOT")
        self.sub = organization_create(parent_organization=self.root, name="Sub Branch", code="HQ-SUB")
        self.role = role_create(name="Admin")
        self.user = user_create(
            username="adminuser",
            name="Admin",
            svc_number="SVC-ADMIN",
            organization=self.root,
            role=self.role,
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_root_action(self):
        response = self.client.get('/api/v1/organizations/root/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 'HQ-ROOT')
        self.assertEqual(response.data['sub_organizations_count'], 1)

    def test_sub_organizations_action(self):
        response = self.client.get(f'/api/v1/organizations/{self.root.pk}/sub-organizations/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'HQ-SUB')
