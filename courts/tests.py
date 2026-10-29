from django.test import TestCase
from datetime import date
from courts.services import court_create, police_station_create, case_category_create, case_create, case_proceeding_create
from courts.models import Case
from organizations.services import organization_create
from users.services import user_create, role_create

class CourtCaseTests(TestCase):
    def setUp(self):
        self.org = organization_create(name="Legal Cell HQ", code="LCHQ")
        self.role = role_create(name="Case Officer")
        self.user = user_create(username="officer1", name="Lt Col Ahmed", svc_number="SVC-999", organization=self.org, role=self.role)
        self.court = court_create(court_name="Sessions Court", presiding_officer="Justice Asghar", designation="Sessions Judge")
        self.ps = police_station_create(name="Waris Khan", code="PS-WK")
        self.category = case_category_create(nature="CRIMINAL", name="Criminal Appeal", short_code="CA")

    def test_case_and_proceeding_workflow(self):
        case = case_create(
            case_number="2026-CR-001",
            case_title="State VS Ali",
            court=self.court,
            category=self.category,
            managing_organization=self.org,
            assigned_case_officer=self.user,
            institution_date=date.today(),
            police_station=self.ps,
            fir_number="123",
            fir_year=2026,
            offence_sections="302 PPC"
        )
        self.assertEqual(case.status, Case.CaseStatus.PENDING)

        proceeding = case_proceeding_create(
            case=case,
            court=self.court,
            recorded_by=self.user,
            sr_no=1,
            proceeding_date=date.today(),
            stage="Arguments",
            today_action="Arguments heard",
            is_case_decided=True
        )
        case.refresh_from_db()
        self.assertEqual(case.status, Case.CaseStatus.DECIDED)
        self.assertEqual(case.decision_date, date.today())
