"""
Populate the database with realistic demo data for the dashboard, users and cases.

Usage:
    python manage.py seed_demo                  # idempotent: safe to run repeatedly
    python manage.py seed_demo --reset          # wipe previously seeded demo data first
    python manage.py seed_demo --cases 80       # change the number of demo cases
    python manage.py seed_demo --password 'X'   # change the shared demo-user password

Everything this command creates is tagged so --reset removes only demo records:
    * users       -> usernames listed in DEMO_USERS
    * cases       -> case_number starting with "DEMO-"
    * org/ranks/… -> left in place (they are reference data and are re-used)
"""
import random
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Appointment, Organization, Permission, Rank, Role, RolePermission, User
from courts.models import (
    Case, CaseCategory, CaseMarkingHistory, CaseParty, CaseProceeding,
    CauseList, CauseListItem, Court, PoliceStation,
)

CASE_PREFIX = 'DEMO-'
DEFAULT_PASSWORD = 'Demo@12345'

RANKS = [
    ('Brigadier', 'Brig', 1),
    ('Colonel', 'Col', 2),
    ('Lieutenant Colonel', 'Lt Col', 3),
    ('Major', 'Maj', 4),
    ('Captain', 'Capt', 5),
    ('Lieutenant', 'Lt', 6),
]

APPOINTMENTS = [
    ('Director Legal', 'DIR-LEGAL'),
    ('Deputy Director Legal', 'DD-LEGAL'),
    ('Case Officer Litigation', 'CO-LIT'),
    ('Legal Assistant', 'LEGAL-ASST'),
]

# (name, code, parent_code)
ORGANIZATIONS = [
    ('Directorate of Legal Affairs', 'DLA', None),
    ('Litigation Wing', 'LIT', 'DLA'),
    ('Criminal Cell', 'CRIM', 'LIT'),
    ('Civil Cell', 'CIVIL', 'LIT'),
    ('Advisory Wing', 'ADV', 'DLA'),
]

# username, name, svc_number, rank, appointment, org code, role, is_staff
DEMO_USERS = [
    ('admin.demo', 'Tariq Mehmood', 'DEMO-001', 'Brigadier', 'Director Legal', 'DLA', 'Administrator', True),
    ('dd.legal', 'Imran Qureshi', 'DEMO-002', 'Colonel', 'Deputy Director Legal', 'LIT', 'Supervisor', False),
    ('officer.crim1', 'Asad Rauf', 'DEMO-003', 'Major', 'Case Officer Litigation', 'CRIM', 'Case Officer', False),
    ('officer.crim2', 'Faisal Nadeem', 'DEMO-004', 'Major', 'Case Officer Litigation', 'CRIM', 'Case Officer', False),
    ('officer.civil1', 'Salman Javed', 'DEMO-005', 'Captain', 'Case Officer Litigation', 'CIVIL', 'Case Officer', False),
    ('officer.civil2', 'Bilal Ahmed', 'DEMO-006', 'Captain', 'Case Officer Litigation', 'CIVIL', 'Case Officer', False),
    ('asst.legal', 'Hamza Siddiqui', 'DEMO-007', 'Lieutenant', 'Legal Assistant', 'ADV', 'Viewer', False),
]

COURTS = [
    ('District & Sessions Court', 'Syed Asghar Ali', 'District & Sessions Judge', '1'),
    ('Additional Sessions Court', 'Mian Shahid Hussain', 'Additional Sessions Judge', '2'),
    ('Civil Court', 'Rana Zafar Iqbal', 'Senior Civil Judge', '3'),
    ('Judicial Magistrate Court', 'Ms. Ayesha Malik', 'Judicial Magistrate 1st Class', '4'),
]

POLICE_STATIONS = [
    ('Waris Khan', 'PS-WK'), ('Civil Lines', 'PS-CL'), ('Saddar Bairooni', 'PS-SB'),
    ('Race Course', 'PS-RC'), ('Gulzar-e-Quaid', 'PS-GQ'), ('Westridge', 'PS-WR'),
]

CATEGORIES = [
    ('CRIMINAL', 'Criminal Misc', 'CRM'),
    ('CRIMINAL', 'Bail Application', 'BAIL'),
    ('CRIMINAL', 'Criminal Appeal', 'CRA'),
    ('CIVIL', 'Civil Suit', 'CS'),
    ('CIVIL', 'Civil Appeal', 'CA'),
    ('CIVIL', 'Writ Petition', 'WP'),
]

OFFENCES = ['PPC 302', 'PPC 324', 'PPC 380', 'PPC 420', 'PPC 489-F', 'CNSA 9(C)', 'PPC 365-A', 'PPC 406']

SURNAMES = ['Khan', 'Ahmed', 'Malik', 'Butt', 'Raja', 'Chaudhry', 'Mirza', 'Sheikh', 'Awan', 'Abbasi']
FIRST_NAMES = ['Muhammad', 'Ali', 'Usman', 'Hassan', 'Zubair', 'Kamran', 'Nadia', 'Saima', 'Rashid', 'Shahid']
RESPONDENTS = [
    'Punjab Health Care Commission', 'Federation of Pakistan', 'Capital Development Authority',
    'Rawalpindi Development Authority', 'Cantonment Board Rawalpindi', 'WAPDA / IESCO',
    'Sui Northern Gas Pipelines', 'National Bank of Pakistan', 'Land Acquisition Collector',
]
COUNSEL = ['Adv. Khalid Mehmood', 'Adv. Sana Rehman', 'Adv. Waqar Younas', 'Adv. Tahir Cheema', 'Adv. Rubina Kausar']

CIVIL_STAGES = [
    ('Notice', 'Notice Issued', 'Written statement'),
    ('Written Statement', 'Reply Filed', 'Framing of issues'),
    ('Evidence', 'Evidence Recorded', 'Cross examination'),
    ('Arguments', 'Arguments Heard', 'Judgment'),
]
CRIMINAL_STAGES = [
    ('Notice', 'Notice to Prosecution', 'Police record'),
    ('Summon for Record', 'Record Summoned', 'Arguments'),
    ('Arguments', 'Arguments Heard', 'Order'),
    ('Order', 'Order Reserved', 'Announcement of order'),
]

# Weighted status mix so the dashboard looks lively
STATUS_WEIGHTS = [
    (Case.CaseStatus.PENDING, 60), (Case.CaseStatus.DECIDED, 18), (Case.CaseStatus.DISPOSED, 10),
    (Case.CaseStatus.TRANSFERRED, 5), (Case.CaseStatus.CONSIGNED, 7),
]


class Command(BaseCommand):
    help = 'Seed demo users, reference data, cases, proceedings and cause lists for the dashboard.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete previously seeded demo data first.')
        parser.add_argument('--cases', type=int, default=40, help='Number of demo cases (default 40).')
        parser.add_argument('--password', default=DEFAULT_PASSWORD, help='Password for all demo users.')
        parser.add_argument('--seed', type=int, default=2026, help='Random seed (deterministic output).')

    @transaction.atomic
    def handle(self, *args, **opts):
        self.rng = random.Random(opts['seed'])
        self.today = timezone.localdate()

        if opts['reset']:
            self._reset()

        self.stdout.write(self.style.NOTICE('Syncing permissions...'))
        call_command('sync_permissions', verbosity=0)

        orgs = self._seed_organizations()
        ranks = self._seed_ranks()
        appts = self._seed_appointments()
        roles = self._seed_roles()
        users = self._seed_users(opts['password'], orgs, ranks, appts, roles)
        courts = self._seed_courts()
        stations = self._seed_police_stations()
        categories = self._seed_categories()
        n_cases = self._seed_cases(opts['cases'], orgs, users, courts, stations, categories)
        n_lists = self._seed_cause_lists(courts)

        self.stdout.write(self.style.SUCCESS(
            f'\nDemo data ready: {len(users)} users, {len(courts)} courts, '
            f'{n_cases} new cases, {n_lists} new cause lists.'
        ))
        self.stdout.write('\nLogin credentials (password for all: ' + self.style.WARNING(opts['password']) + ')')
        for u in DEMO_USERS:
            self.stdout.write(f'  {u[0]:<15} {u[6]:<14} {u[1]}')

    # ------------------------------------------------------------------ reset
    def _reset(self):
        self.stdout.write(self.style.WARNING('Removing previous demo data...'))
        demo_cases = Case.objects.filter(case_number__startswith=CASE_PREFIX)
        CauseListItem.objects.filter(case__in=demo_cases).delete()
        CauseList.objects.filter(items__isnull=True, court__court_name__in=[c[0] for c in COURTS]).delete()
        demo_cases.delete()  # cascades parties, proceedings, marking history
        User.objects.filter(username__in=[u[0] for u in DEMO_USERS]).delete()

    # -------------------------------------------------------- reference data
    def _seed_organizations(self):
        orgs = {}
        root = Organization.objects.filter(is_root=True).first()
        for name, code, parent_code in ORGANIZATIONS:
            existing = Organization.objects.filter(code=code).first()
            if existing:
                orgs[code] = existing
                continue
            if parent_code is None:
                if root:  # a root already exists (e.g. pre-existing data) -> reuse it
                    orgs[code] = root
                    continue
                orgs[code] = root = Organization.objects.create(name=name, code=code)
            else:
                orgs[code] = Organization.objects.create(name=name, code=code, parent_organization=orgs[parent_code])
        return orgs

    def _seed_ranks(self):
        return {
            title: Rank.objects.get_or_create(
                title=title, defaults={'abbreviation': abbr, 'seniority_index': idx})[0]
            for title, abbr, idx in RANKS
        }

    def _seed_appointments(self):
        return {
            title: Appointment.objects.get_or_create(title=title, defaults={'appointment_code': code})[0]
            for title, code in APPOINTMENTS
        }

    def _seed_roles(self):
        all_codes = list(Permission.objects.values_list('code_name', flat=True))
        read_codes = [c for c in all_codes if c.endswith('_read')]
        officer_codes = read_codes + [
            c for c in all_codes
            if c.startswith(('case_create', 'case_update', 'case_close', 'case_mark', 'case_party_',
                             'case_proceeding_', 'cause_list_item_create', 'cause_list_item_update'))
            and not c.endswith('_delete')
        ]
        supervisor_codes = officer_codes + [c for c in all_codes if c.startswith(('cause_list_', 'court_', 'user_'))]

        definitions = {
            'Administrator': ('Full system access', all_codes),
            'Supervisor': ('Supervises case officers and cause lists', supervisor_codes),
            'Case Officer': ('Works on assigned cases and proceedings', officer_codes),
            'Viewer': ('Read-only access', read_codes),
        }
        roles = {}
        for name, (desc, codes) in definitions.items():
            role, _ = Role.objects.get_or_create(name=name, defaults={'description': desc})
            wanted = set(codes)
            have = set(RolePermission.objects.filter(role=role).values_list('permission__code_name', flat=True))
            for perm in Permission.objects.filter(code_name__in=wanted - have):
                RolePermission.objects.create(role=role, permission=perm)
            roles[name] = role
        return roles

    def _seed_users(self, password, orgs, ranks, appts, roles):
        users = {}
        for username, name, svc, rank, appt, org, role, is_staff in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    name=name, svc_number=svc, rank=ranks[rank], appointment=appts[appt],
                    organization=orgs[org], role=roles[role], is_staff=is_staff,
                    is_superuser=is_staff, profile_status='ACTIVE', is_active=True,
                ),
            )
            if created:
                user.set_password(password)
                user.save(update_fields=['password'])
            users[username] = user
        return users

    def _seed_courts(self):
        courts = []
        for name, officer, designation, room in COURTS:
            court, _ = Court.objects.get_or_create(
                court_name=name, presiding_officer=officer,
                defaults={'designation': designation, 'court_room_no': room, 'district': 'Rawalpindi'})
            courts.append(court)
        return courts

    def _seed_police_stations(self):
        return [
            PoliceStation.objects.get_or_create(code=code, defaults={'name': name, 'district': 'Rawalpindi'})[0]
            for name, code in POLICE_STATIONS
        ]

    def _seed_categories(self):
        cats = []
        for nature, name, code in CATEGORIES:
            cat = CaseCategory.objects.filter(nature=nature, name=name).first() or \
                CaseCategory.objects.create(nature=nature, name=name, short_code=code)
            cats.append(cat)
        return cats

    # ------------------------------------------------------------------ cases
    def _person(self):
        return f'{self.rng.choice(FIRST_NAMES)} {self.rng.choice(SURNAMES)}'

    def _pick_status(self):
        statuses, weights = zip(*STATUS_WEIGHTS)
        return self.rng.choices(statuses, weights=weights)[0]

    def _seed_cases(self, total, orgs, users, courts, stations, categories):
        criminal_officers = [users['officer.crim1'], users['officer.crim2']]
        civil_officers = [users['officer.civil1'], users['officer.civil2']]
        supervisor = users['dd.legal']
        created = 0

        for i in range(1, total + 1):
            case_number = f'{CASE_PREFIX}{self.today.year}-{i:04d}'
            if Case.objects.filter(case_number=case_number).exists():
                continue

            category = self.rng.choice(categories)
            is_criminal = category.nature == CaseCategory.CaseNature.CRIMINAL
            court = self.rng.choice(courts)
            officer = self.rng.choice(criminal_officers if is_criminal else civil_officers)
            org = orgs['CRIM'] if is_criminal else orgs['CIVIL']
            status = self._pick_status()
            institution = self.today - timedelta(days=self.rng.randint(20, 700))

            petitioner = self._person()
            if is_criminal:
                title = f'The State VS {petitioner}'
                extra = dict(
                    police_station=self.rng.choice(stations),
                    fir_number=str(self.rng.randint(100, 2500)),
                    fir_year=institution.year - self.rng.randint(0, 1),
                    offence_sections=self.rng.choice(OFFENCES),
                )
            else:
                title = f'{petitioner} VS {self.rng.choice(RESPONDENTS)}'
                extra = {}

            case = Case.objects.create(
                case_number=case_number, case_title=title, court=court, category=category,
                managing_organization=org, assigned_case_officer=officer,
                institution_number=str(self.rng.randint(1000, 9999)), institution_date=institution,
                status=Case.CaseStatus.PENDING, **extra,
            )

            self._seed_parties(case, petitioner, is_criminal)
            decided_on = self._seed_proceedings(case, court, officer, institution, status, is_criminal)
            if decided_on:
                case.status = status
                case.decision_date = decided_on
                case.save(update_fields=['status', 'decision_date', 'updated_at'])
            elif status != Case.CaseStatus.PENDING:
                # non-judgment closures (transferred / consigned) still need a closing date
                case.status = status
                case.decision_date = min(self.today, institution + timedelta(days=self.rng.randint(30, 200)))
                case.save(update_fields=['status', 'decision_date', 'updated_at'])

            # A third of open cases have been marked between officers
            if case.status == Case.CaseStatus.PENDING and self.rng.random() < 0.33:
                self._seed_marking(case, supervisor, officer)

            created += 1
        return created

    def _seed_parties(self, case, petitioner, is_criminal):
        CaseParty.objects.create(
            case=case, party_side=CaseParty.PartySide.PETITIONER, party_name=petitioner, is_primary_party=True,
            counsel_name=self.rng.choice(COUNSEL),
            cnic=f'37405-{self.rng.randint(1000000, 9999999)}-{self.rng.randint(1, 9)}',
            contact_number=f'03{self.rng.randint(0, 4)}{self.rng.randint(10000000, 99999999)}',
        )
        if is_criminal:
            CaseParty.objects.create(
                case=case, party_side=CaseParty.PartySide.STATE, party_name='The State',
                counsel_name='Deputy District Public Prosecutor')
        else:
            CaseParty.objects.create(
                case=case, party_side=CaseParty.PartySide.RESPONDENT,
                party_name=case.case_title.split(' VS ')[-1], counsel_name=self.rng.choice(COUNSEL))

    def _seed_proceedings(self, case, court, officer, institution, status, is_criminal):
        """Create 1-4 hearings. Returns the decision date when the case was decided/disposed."""
        stages = CRIMINAL_STAGES if is_criminal else CIVIL_STAGES
        closes = status in (Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED)
        count = self.rng.randint(2, 4) if closes else self.rng.randint(1, 3)
        date = institution + timedelta(days=self.rng.randint(5, 20))
        decided_on = None

        for sr in range(1, count + 1):
            if date > self.today:
                break
            stage, action, next_purpose = stages[min(sr - 1, len(stages) - 1)]
            last = sr == count
            is_decided = closes and last
            next_date = None if is_decided else date + timedelta(days=self.rng.randint(7, 30))
            CaseProceeding.objects.create(
                case=case, court=court, recorded_by=officer, sr_no=sr, proceeding_date=date, stage=stage,
                today_action='Decided' if is_decided else action,
                short_order=('Case decided on merits; file consigned.' if is_decided
                             else f'{action}. Adjourned for {next_purpose.lower()}.'),
                is_case_decided=is_decided, next_proceeding_date=next_date,
                next_stage_purpose=None if is_decided else next_purpose,
            )
            if is_decided:
                decided_on = date
            date = next_date or date
        # If we ran out of calendar before deciding, the case simply stays open
        return decided_on

    def _seed_marking(self, case, supervisor, officer):
        new_officer = User.objects.filter(
            organization=case.managing_organization, role__name='Case Officer', is_active=True,
        ).exclude(pk=officer.pk).first()
        if not new_officer:
            return
        remarks = 'Marked for urgent attention before next hearing.'
        CaseMarkingHistory.objects.create(
            case=case, from_user=supervisor, to_user=new_officer,
            action=CaseMarkingHistory.Action.MARK, remarks=remarks)
        case.marked_by = supervisor
        case.assigned_case_officer = new_officer
        case.marked_at = timezone.now() - timedelta(days=self.rng.randint(1, 14))
        case.marking_remarks = remarks
        case.save(update_fields=['marked_by', 'assigned_case_officer', 'marked_at', 'marking_remarks', 'updated_at'])

    # ------------------------------------------------------------- cause lists
    def _seed_cause_lists(self, courts):
        """Today (every court) + yesterday + the next two days for the first court."""
        created = 0
        plan = [(court, self.today) for court in courts]
        plan += [(courts[0], self.today + timedelta(days=d)) for d in (-1, 1, 2)]

        for court, day in plan:
            cause_list, was_created = CauseList.objects.get_or_create(
                court=court, cause_list_date=day, defaults={'day_of_week': day.strftime('%A')})
            if cause_list.items.exists():
                continue

            cases = list(
                Case.objects.filter(court=court, status=Case.CaseStatus.PENDING, case_number__startswith=CASE_PREFIX)
                .select_related('category').order_by('case_number')[:8]
            )
            for roster_no, case in enumerate(cases, start=1):
                proceeding = CaseProceeding.objects.filter(case=case, proceeding_date=day).first()
                if not proceeding:
                    last_sr = case.proceedings.order_by('-sr_no').values_list('sr_no', flat=True).first() or 0
                    proceeding = CaseProceeding.objects.create(
                        case=case, court=court, recorded_by=case.assigned_case_officer, sr_no=last_sr + 1,
                        proceeding_date=day, stage='Hearing', today_action='Listed for hearing',
                        next_stage_purpose='Arguments')
                CauseListItem.objects.create(
                    cause_list=cause_list, case=case, proceeding=proceeding,
                    roster_sr_no=roster_no, category_heading=case.category.name)
            created += int(was_created)
        return created
