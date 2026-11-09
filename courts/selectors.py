from django.db.models import QuerySet, Prefetch
from django.utils import timezone
from .models import (
    Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding,
    CauseList, CauseListItem, CaseMarkingHistory
)

def court_list() -> QuerySet[Court]:
    return Court.objects.all()

def police_station_list() -> QuerySet[PoliceStation]:
    return PoliceStation.objects.all()

def case_category_list() -> QuerySet[CaseCategory]:
    return CaseCategory.objects.all()

def case_list() -> QuerySet[Case]:
    proceedings_qs = CaseProceeding.objects.select_related(
        'court',
        'recorded_by__rank',
        'recorded_by__appointment',
        'recorded_by__organization',
        'recorded_by__role'
    )
    return Case.objects.select_related(
        'court',
        'category',
        'managing_organization',
        'assigned_case_officer__rank',
        'assigned_case_officer__appointment',
        'assigned_case_officer__organization',
        'assigned_case_officer__role',
        'marked_by__rank',
        'marked_by__appointment',
        'marked_by__organization',
        'marked_by__role',
        'police_station'
    ).prefetch_related(
        'parties',
        Prefetch('proceedings', queryset=proceedings_qs)
    ).all()

def case_get(*, case_id) -> Case:
    proceedings_qs = CaseProceeding.objects.select_related(
        'court',
        'recorded_by__rank',
        'recorded_by__appointment',
        'recorded_by__organization',
        'recorded_by__role'
    )
    return Case.objects.select_related(
        'court',
        'category',
        'managing_organization',
        'assigned_case_officer__rank',
        'assigned_case_officer__appointment',
        'assigned_case_officer__organization',
        'assigned_case_officer__role',
        'marked_by__rank',
        'marked_by__appointment',
        'marked_by__organization',
        'marked_by__role',
        'police_station'
    ).prefetch_related(
        'parties',
        Prefetch('proceedings', queryset=proceedings_qs)
    ).get(pk=case_id)

def case_marking_history_list(*, case_id) -> QuerySet[CaseMarkingHistory]:
    return CaseMarkingHistory.objects.filter(case_id=case_id).select_related(
        'from_user__rank',
        'from_user__appointment',
        'from_user__organization',
        'to_user__rank',
        'to_user__appointment',
        'to_user__organization'
    ).order_by('-created_at')

def case_timeline(*, case: Case, order: str = 'desc') -> list[dict]:
    events = []

    # 1. Institution event
    events.append({
        'id': f"institution_{case.case_id}",
        'event_type': 'INSTITUTION',
        'title': f"Case Instituted: {case.case_number}",
        'description': case.case_title,
        'date': str(case.institution_date),
        'timestamp': case.created_at.isoformat(),
        'actor': case.assigned_case_officer,
        'metadata': {
            'court': case.court.court_name if case.court else None,
            'court_id': str(case.court_id) if case.court_id else None,
            'category': case.category.name if case.category else None,
            'category_nature': case.category.nature if case.category else None,
            'institution_number': case.institution_number,
            'managing_organization': case.managing_organization.name if case.managing_organization else None,
            'police_station': case.police_station.name if case.police_station else None,
            'fir_number': case.fir_number,
            'fir_year': case.fir_year,
            'offence_sections': case.offence_sections,
        }
    })

    # 2. Movement / Marking history
    history_qs = CaseMarkingHistory.objects.filter(case=case).select_related(
        'from_user__rank', 'from_user__appointment', 'from_user__organization',
        'to_user__rank', 'to_user__appointment', 'to_user__organization'
    )
    for h in history_qs:
        is_back = (h.action == CaseMarkingHistory.Action.MARK_BACK)
        events.append({
            'id': f"marking_{h.history_id}",
            'event_type': 'MARK_BACK' if is_back else 'MARK',
            'title': f"Marked back to {h.to_user.name}" if is_back else f"Marked to {h.to_user.name}",
            'description': h.remarks or '',
            'date': str(timezone.localdate(h.created_at)),
            'timestamp': h.created_at.isoformat(),
            'actor': h.from_user,
            'target_user': h.to_user,
            'metadata': {
                'history_id': str(h.history_id),
                'action': h.action,
                'from_user_name': h.from_user.name,
                'to_user_name': h.to_user.name,
                'remarks': h.remarks
            }
        })

    # 3. Proceedings / Hearing orders
    proceedings_qs = CaseProceeding.objects.filter(case=case).select_related(
        'court', 'recorded_by__rank', 'recorded_by__appointment', 'recorded_by__organization'
    )
    for p in proceedings_qs:
        events.append({
            'id': f"proceeding_{p.proceeding_id}",
            'event_type': 'PROCEEDING',
            'title': f"Hearing #{p.sr_no}: {p.stage}",
            'description': p.short_order or p.today_action or '',
            'date': str(p.proceeding_date),
            'timestamp': p.created_at.isoformat(),
            'actor': p.recorded_by,
            'metadata': {
                'proceeding_id': str(p.proceeding_id),
                'sr_no': p.sr_no,
                'stage': p.stage,
                'today_action': p.today_action,
                'short_order': p.short_order,
                'next_proceeding_date': str(p.next_proceeding_date) if p.next_proceeding_date else None,
                'next_stage_purpose': p.next_stage_purpose,
                'is_case_decided': p.is_case_decided,
                'court_name': p.court.court_name if p.court else None,
                'presiding_officer': p.court.presiding_officer if p.court else None,
            }
        })

    # 4. Decision / Closure event
    if case.status in [Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED, Case.CaseStatus.CONSIGNED] and case.decision_date:
        events.append({
            'id': f"decision_{case.case_id}",
            'event_type': 'DECISION',
            'title': f"Case {case.get_status_display()}",
            'description': f"Case marked as {case.get_status_display()}",
            'date': str(case.decision_date),
            'timestamp': case.updated_at.isoformat(),
            'actor': case.assigned_case_officer,
            'metadata': {
                'status': case.status,
                'decision_date': str(case.decision_date)
            }
        })

    event_order_rank = {
        'INSTITUTION': 0,
        'PROCEEDING': 1,
        'MARK': 2,
        'MARK_BACK': 2,
        'DECISION': 3,
    }
    reverse = (order.lower() == 'desc')
    events.sort(
        key=lambda x: (
            x['date'],
            (event_order_rank.get(x['event_type'], 1) if not reverse else -event_order_rank.get(x['event_type'], 1)),
            x['timestamp']
        ),
        reverse=reverse
    )
    return events

def cause_list_queryset() -> QuerySet[CauseList]:
    items_qs = CauseListItem.objects.select_related(
        'case__court',
        'case__category',
        'case__managing_organization',
        'proceeding__court',
        'proceeding__recorded_by'
    )
    return CauseList.objects.select_related('court').prefetch_related(
        Prefetch('items', queryset=items_qs)
    ).all()
