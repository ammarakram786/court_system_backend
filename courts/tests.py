from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from courts.services import (
    court_create, police_station_create, case_category_create,
    case_create, case_proceeding_create, cause_list_create, cause_list_item_create,
    case_mark, case_mark_back
)
from courts.models import Case, CaseParty, CaseProceeding, CauseList, CaseMarkingHistory
from courts.selectors import case_list
from accounts.models import Permission
from accounts.services import (
    organization_create, user_create, role_create, appointment_create,
    permissions_sync
)

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
            role=self.role,
            is_staff=True
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


class CaseMarkingServiceTests(TestCase):
    def setUp(self):
        self.org = organization_create(name="Directorate of Law", code="DOL")
        self.role = role_create(name="Law Officer")
        self.officer1 = user_create(
            username="law_officer_1",
            name="Major Bilal",
            svc_number="SVC-101",
            organization=self.org,
            role=self.role
        )
        self.officer2 = user_create(
            username="law_officer_2",
            name="Captain Tariq",
            svc_number="SVC-102",
            organization=self.org,
            role=self.role
        )
        self.court = court_create(court_name="High Court", presiding_officer="Judge", designation="Judge")
        self.category = case_category_create(nature="CIVIL", name="Civil Revision", short_code="CR")
        self.case = case_create(
            case_number="2026-CR-555",
            case_title="Govt VS Contractor",
            court=self.court,
            category=self.category,
            managing_organization=self.org,
            assigned_case_officer=self.officer1,
            institution_date=date.today()
        )

    def test_case_mark_and_mark_back_lifecycle(self):
        # 1. Mark to Officer 2
        updated_case = case_mark(
            case=self.case,
            from_user=self.officer1,
            to_user=self.officer2,
            remarks="Please attend the upcoming hearing and prepare written reply."
        )
        self.assertEqual(updated_case.assigned_case_officer, self.officer2)
        self.assertEqual(updated_case.marked_by, self.officer1)
        self.assertEqual(updated_case.marking_remarks, "Please attend the upcoming hearing and prepare written reply.")

        history = CaseMarkingHistory.objects.filter(case=self.case)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().action, CaseMarkingHistory.Action.MARK)
        self.assertEqual(history.first().from_user, self.officer1)
        self.assertEqual(history.first().to_user, self.officer2)

        # 2. Mark Back to Officer 1
        marked_back_case = case_mark_back(
            case=updated_case,
            from_user=self.officer2,
            remarks="Written reply filed. Hearing concluded."
        )
        self.assertEqual(marked_back_case.assigned_case_officer, self.officer1)
        self.assertEqual(marked_back_case.marked_by, self.officer2)
        self.assertEqual(marked_back_case.marking_remarks, "Written reply filed. Hearing concluded.")

        history_items = list(CaseMarkingHistory.objects.filter(case=self.case).order_by('created_at'))
        self.assertEqual(len(history_items), 2)
        self.assertEqual(history_items[1].action, CaseMarkingHistory.Action.MARK_BACK)
        self.assertEqual(history_items[1].from_user, self.officer2)
        self.assertEqual(history_items[1].to_user, self.officer1)

    def test_cannot_mark_to_same_officer(self):
        with self.assertRaises(ValidationError):
            case_mark(
                case=self.case,
                from_user=self.officer1,
                to_user=self.officer1,
                remarks="Self assignment"
            )

    def test_cannot_mark_back_when_no_marked_by(self):
        # Fresh case has no marked_by
        self.assertIsNone(self.case.marked_by)
        with self.assertRaises(ValidationError):
            case_mark_back(
                case=self.case,
                from_user=self.officer1,
                remarks="Should fail"
            )

    def test_cannot_mark_decided_case(self):
        self.case.status = Case.CaseStatus.DECIDED
        self.case.save()
        with self.assertRaises(ValidationError):
            case_mark(
                case=self.case,
                from_user=self.officer1,
                to_user=self.officer2,
                remarks="Case is already decided"
            )


class CaseMarkingAndObjectPermissionAPITests(TestCase):
    def setUp(self):
        # Organizations
        self.org_root = organization_create(name="Law Directorate HQ", code="LDHQ")
        self.org_north = organization_create(name="North Division HQ", code="NDHQ", parent_organization=self.org_root)
        self.org_south = organization_create(name="South Division HQ", code="SDHQ", parent_organization=self.org_root)

        # Appointments
        self.appt_legal_officer = appointment_create(title="Legal Officer", appointment_code="LO")
        self.appt_record_officer = appointment_create(title="Record Officer", appointment_code="RO")

        # Sync permissions and assign all court permissions to role
        permissions_sync()
        self.role = role_create(name="Full Case Access")
        perms = Permission.objects.filter(app_name='courts')
        self.role.permissions.set(perms)

        # Users:
        # 1. Primary assigned officer (North Org, Legal Officer)
        self.officer_assigned = user_create(
            username="assigned_user",
            name="Major Assigned",
            svc_number="SVC-001",
            organization=self.org_north,
            appointment=self.appt_legal_officer,
            role=self.role
        )

        # 2. Peer officer (North Org, Legal Officer) -> SAME ORG & SAME APPOINTMENT
        self.officer_peer = user_create(
            username="peer_user",
            name="Major Peer",
            svc_number="SVC-002",
            organization=self.org_north,
            appointment=self.appt_legal_officer,
            role=self.role
        )

        # 3. Different Appointment officer (North Org, Record Officer) -> SAME ORG, DIFF APPOINTMENT
        self.officer_diff_appt = user_create(
            username="diff_appt_user",
            name="Captain Record",
            svc_number="SVC-003",
            organization=self.org_north,
            appointment=self.appt_record_officer,
            role=self.role
        )

        # 4. Different Organization officer (South Org, Legal Officer) -> DIFF ORG, SAME APPOINTMENT
        self.officer_diff_org = user_create(
            username="diff_org_user",
            name="Major South",
            svc_number="SVC-004",
            organization=self.org_south,
            appointment=self.appt_legal_officer,
            role=self.role
        )

        self.court = court_create(court_name="District Court", presiding_officer="Senior Judge", designation="SJ")
        self.category = case_category_create(nature="CIVIL", name="Civil Suit", short_code="CS")
        self.case = case_create(
            case_number="2026-CS-777",
            case_title="North HQ VS Landowner",
            court=self.court,
            category=self.category,
            managing_organization=self.org_north,
            assigned_case_officer=self.officer_assigned,
            institution_date=date.today()
        )
        self.client = APIClient()

    def test_assigned_officer_can_work_and_metadata_is_correct(self):
        self.client.force_authenticate(user=self.officer_assigned)

        res = self.client.get(f'/api/v1/cases/{self.case.pk}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['can_work'])
        self.assertTrue(res.data['can_mark'])
        self.assertFalse(res.data['can_mark_back'])  # no marked_by yet
        self.assertEqual(res.data['work_access_type'], 'ASSIGNED')

        # Update case
        patch_res = self.client.patch(f'/api/v1/cases/{self.case.pk}/', {'case_title': 'Updated Title by Assigned'})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        # Add proceeding
        proc_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Arguments',
            'today_action': 'Arguments Completed'
        })
        self.assertEqual(proc_res.status_code, status.HTTP_201_CREATED)

    def test_peer_officer_with_same_appointment_and_org_can_work(self):
        # Peer has same appointment (Legal Officer) and same org (North Division)
        self.client.force_authenticate(user=self.officer_peer)

        res = self.client.get(f'/api/v1/cases/{self.case.pk}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['can_work'])
        self.assertEqual(res.data['work_access_type'], 'PEER')

        # Peer can update
        patch_res = self.client.patch(f'/api/v1/cases/{self.case.pk}/', {'case_title': 'Updated by Peer'})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        # Peer can record proceedings
        proc_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Evidence',
            'today_action': 'Witness Examined'
        })
        self.assertEqual(proc_res.status_code, status.HTTP_201_CREATED)

    def test_non_peer_user_has_view_only_access(self):
        # User in same org but different appointment (Record Officer)
        self.client.force_authenticate(user=self.officer_diff_appt)

        res = self.client.get(f'/api/v1/cases/{self.case.pk}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['can_work'])
        self.assertFalse(res.data['can_mark'])
        self.assertFalse(res.data['can_mark_back'])
        self.assertEqual(res.data['work_access_type'], 'VIEW_ONLY')

        # Attempt to patch case -> 403 Forbidden
        patch_res = self.client.patch(f'/api/v1/cases/{self.case.pk}/', {'case_title': 'Unauthorized Update'})
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to record proceeding on case -> 403 Forbidden
        proc_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Notice',
            'today_action': 'Notice'
        })
        self.assertEqual(proc_res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to close case -> 403 Forbidden
        close_res = self.client.post(f'/api/v1/cases/{self.case.pk}/close/', {
            'status': 'DECIDED'
        })
        self.assertEqual(close_res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to mark case -> 403 Forbidden
        mark_res = self.client.post(f'/api/v1/cases/{self.case.pk}/mark/', {
            'to_user_id': str(self.officer_peer.pk)
        })
        self.assertEqual(mark_res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt direct proceeding creation via standalone endpoint -> 403 Forbidden
        direct_proc_res = self.client.post('/api/v1/case-proceedings/', {
            'case': str(self.case.pk),
            'court': str(self.court.pk),
            'proceeding_date': str(date.today()),
            'stage': 'Unauthorized',
        })
        self.assertEqual(direct_proc_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_marking_and_mark_back_complete_workflow(self):
        # 1. Assigned officer marks the case to officer_diff_appt
        self.client.force_authenticate(user=self.officer_assigned)
        mark_res = self.client.post(f'/api/v1/cases/{self.case.pk}/mark/', {
            'to_user_id': str(self.officer_diff_appt.pk),
            'remarks': 'Assigned to Record Officer for document audit.'
        })
        self.assertEqual(mark_res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(mark_res.data['assigned_case_officer']), str(self.officer_diff_appt.pk))
        self.assertEqual(str(mark_res.data['marked_by']), str(self.officer_assigned.pk))

        # 2. Former assignee (officer_assigned) now has VIEW-ONLY access
        check_old_officer = self.client.get(f'/api/v1/cases/{self.case.pk}/')
        self.assertFalse(check_old_officer.data['can_work'])
        self.assertEqual(check_old_officer.data['work_access_type'], 'VIEW_ONLY')

        # 3. Newly assigned officer (officer_diff_appt) now has WORK and MARK_BACK access
        self.client.force_authenticate(user=self.officer_diff_appt)
        check_new_officer = self.client.get(f'/api/v1/cases/{self.case.pk}/')
        self.assertTrue(check_new_officer.data['can_work'])
        self.assertTrue(check_new_officer.data['can_mark_back'])
        self.assertEqual(check_new_officer.data['work_access_type'], 'ASSIGNED')

        # 4. Newly assigned officer records proceeding
        proc_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Record Checked',
            'today_action': 'Documents Verified'
        })
        self.assertEqual(proc_res.status_code, status.HTTP_201_CREATED)

        # 5. Newly assigned officer marks case back to original sender
        mark_back_res = self.client.post(f'/api/v1/cases/{self.case.pk}/mark-back/', {
            'remarks': 'Document audit completed. Returning case file.'
        })
        self.assertEqual(mark_back_res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(mark_back_res.data['assigned_case_officer']), str(self.officer_assigned.pk))
        self.assertEqual(str(mark_back_res.data['marked_by']), str(self.officer_diff_appt.pk))

        # 6. Verify movement audit trail via marking-history endpoint
        history_res = self.client.get(f'/api/v1/cases/{self.case.pk}/marking-history/')
        self.assertEqual(history_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history_res.data), 2)
        # Most recent first
        self.assertEqual(history_res.data[0]['action'], 'MARK_BACK')
        self.assertEqual(history_res.data[0]['remarks'], 'Document audit completed. Returning case file.')
        self.assertEqual(history_res.data[1]['action'], 'MARK')
        self.assertEqual(history_res.data[1]['remarks'], 'Assigned to Record Officer for document audit.')

    def test_case_timeline_endpoint(self):
        self.client.force_authenticate(user=self.officer_assigned)

        # 1. Add a proceeding
        proc_res = self.client.post(f'/api/v1/cases/{self.case.pk}/proceedings/', {
            'proceeding_date': str(date.today()),
            'stage': 'Preliminary Hearing',
            'today_action': 'Notice to parties',
            'short_order': 'Notice issued for next week',
            'next_proceeding_date': str(date.today()),
            'next_stage_purpose': 'Written Statements'
        })
        self.assertEqual(proc_res.status_code, status.HTTP_201_CREATED)

        # 2. Mark case to peer
        mark_res = self.client.post(f'/api/v1/cases/{self.case.pk}/mark/', {
            'to_user_id': str(self.officer_peer.pk),
            'remarks': 'Assigned to peer officer'
        })
        self.assertEqual(mark_res.status_code, status.HTTP_200_OK)

        # 3. Peer closes case
        self.client.force_authenticate(user=self.officer_peer)
        close_res = self.client.post(f'/api/v1/cases/{self.case.pk}/close/', {
            'status': 'DECIDED',
            'decision_date': str(date.today())
        })
        self.assertEqual(close_res.status_code, status.HTTP_200_OK)

        # 4. Fetch timeline in default (descending) order
        timeline_res = self.client.get(f'/api/v1/cases/{self.case.pk}/timeline/')
        self.assertEqual(timeline_res.status_code, status.HTTP_200_OK)
        events = timeline_res.data
        self.assertGreaterEqual(len(events), 4)

        event_types = [e['event_type'] for e in events]
        self.assertIn('INSTITUTION', event_types)
        self.assertIn('PROCEEDING', event_types)
        self.assertIn('MARK', event_types)
        self.assertIn('DECISION', event_types)

        # 5. Fetch timeline in ascending order
        timeline_asc_res = self.client.get(f'/api/v1/cases/{self.case.pk}/timeline/?order=asc')
        self.assertEqual(timeline_asc_res.status_code, status.HTTP_200_OK)
        asc_events = timeline_asc_res.data
        self.assertEqual(len(asc_events), len(events))
        # First event in asc order should be INSTITUTION
        self.assertEqual(asc_events[0]['event_type'], 'INSTITUTION')
        self.assertIsNotNone(asc_events[0]['metadata']['court'])

