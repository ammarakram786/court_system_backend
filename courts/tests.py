from datetime import date
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from courts.services import (
    court_create, police_station_create, case_category_create,
    case_create, case_proceeding_create, cause_list_create, cause_list_item_create
)
from courts.models import Case, CaseParty, CaseProceeding, CauseList
from courts.selectors import case_list
from organizations.services import organization_create
from users.services import user_create, role_create

class CourtCaseTests(TestCase):
    def setUp(self):
        self.org = organization_create(name="Legal Cell HQ", code="LCHQ")
        self.role = role_create(name="Case Officer")
        self.user = user_create(
            username="officer1",
            name="Lt Col Ahmed",
            svc_number="SVC-999",
            organization=self.org,
            role=self.role
        )
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

    def test_proceeding_sr_no_auto_increment(self):
        case = case_create(
            case_number="2026-CR-002",
            case_title="State VS Bilal",
            court=self.court,
            category=self.category,
            managing_organization=self.org,
            institution_date=date.today()
        )
        p1 = case_proceeding_create(case=case, court=self.court, proceeding_date=date.today(), stage="Summon")
        p2 = case_proceeding_create(case=case, court=self.court, proceeding_date=date.today(), stage="Charge")
        self.assertEqual(p1.sr_no, 1)
        self.assertEqual(p2.sr_no, 2)


class CourtAPITests(TestCase):
    def setUp(self):
        self.org = organization_create(name="Legal Cell HQ", code="LCHQ")
        self.role = role_create(name="Case Officer")
        self.user = user_create(
            username="courtclerk",
            name="Major Clerk",
            svc_number="SVC-444",
            organization=self.org,
            role=self.role
        )
        self.court = court_create(court_name="High Court", presiding_officer="Chief Justice", designation="CJ")
        self.category = case_category_create(nature="CIVIL", name="Writ Petition", short_code="WP")
        self.case = case_create(
            case_number="2026-WP-100",
            case_title="Citizen VS Federation",
            court=self.court,
            category=self.category,
            managing_organization=self.org,
            institution_date=date.today()
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_case_proceedings_action_get_and_post(self):
        # 1. Post new proceeding through case endpoint
        post_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Preliminary Hearing',
            'today_action': 'Notice Issued',
            'is_case_decided': False
        })
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post_res.data['sr_no'], 1)

        # 2. Get proceedings through case endpoint
        get_res = self.client.get(f'/api/v1/cases/{self.case.pk}/proceedings/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_res.data), 1)

    def test_case_parties_action_get_and_post(self):
        post_res = self.client.post(f'/api/v1/cases/{self.case.pk}/parties/', {
            'party_side': 'PETITIONER',
            'party_name': 'Citizen Khan',
            'is_primary_party': True,
            'counsel_name': 'Advocate Supreme Court'
        })
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post_res.data['party_name'], 'Citizen Khan')

        get_res = self.client.get(f'/api/v1/cases/{self.case.pk}/parties/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_res.data), 1)

    def test_close_case_action(self):
        res = self.client.post(f'/api/v1/cases/{self.case.pk}/close/', {
            'status': 'DECIDED',
            'decision_date': str(date.today())
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, Case.CaseStatus.DECIDED)
        self.assertEqual(self.case.decision_date, date.today())

    def test_cause_list_today_action(self):
        cl = cause_list_create(court=self.court, cause_list_date=date.today(), day_of_week="Monday")
        res = self.client.get('/api/v1/cause-lists/today/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['cause_list_id'], str(cl.cause_list_id))
