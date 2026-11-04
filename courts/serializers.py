from rest_framework import serializers
from .models import (
    Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding,
    CauseList, CauseListItem, CaseMarkingHistory
)
from .permissions import can_user_work_on_case
from accounts.serializers import OrganizationSerializer, UserSerializer

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['court_id', 'district', 'court_name', 'presiding_officer', 'designation', 'court_room_no', 'is_active', 'created_at']
        read_only_fields = ['court_id', 'created_at']


class PoliceStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliceStation
        fields = ['police_station_id', 'district', 'name', 'code']
        read_only_fields = ['police_station_id']


class CaseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ['category_id', 'nature', 'name', 'short_code']
        read_only_fields = ['category_id']


class CasePartySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParty
        fields = ['party_id', 'case', 'party_side', 'party_name', 'is_primary_party', 'counsel_name', 'cnic', 'contact_number']
        read_only_fields = ['party_id']


class CaseProceedingSerializer(serializers.ModelSerializer):
    recorded_by_details = UserSerializer(source='recorded_by', read_only=True)
    court_details = CourtSerializer(source='court', read_only=True)
    sr_no = serializers.IntegerField(required=False)

    class Meta:
        model = CaseProceeding
        fields = [
            'proceeding_id',
            'case',
            'court',
            'court_details',
            'recorded_by',
            'recorded_by_details',
            'sr_no',
            'proceeding_date',
            'stage',
            'today_action',
            'short_order',
            'is_case_decided',
            'next_proceeding_date',
            'next_stage_purpose',
            'created_at'
        ]
        read_only_fields = ['proceeding_id', 'created_at']
        validators = []

    def validate(self, attrs):
        case = attrs.get('case') or (self.instance.case if self.instance else None)
        if 'sr_no' not in attrs or attrs.get('sr_no') is None:
            if case:
                from django.db.models import Max
                max_sr = CaseProceeding.objects.filter(case=case).aggregate(Max('sr_no'))['sr_no__max'] or 0
                attrs['sr_no'] = max_sr + 1

        sr_no = attrs.get('sr_no')
        if case and sr_no:
            qs = CaseProceeding.objects.filter(case=case, sr_no=sr_no)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'sr_no': f"Proceeding with serial number {sr_no} already exists for this case."
                })
        return super().validate(attrs)

    def create(self, validated_data):
        proceeding = super().create(validated_data)
        if proceeding.is_case_decided:
            case = proceeding.case
            case.status = Case.CaseStatus.DECIDED
            case.decision_date = proceeding.proceeding_date
            case.save(update_fields=['status', 'decision_date', 'updated_at'])
        return proceeding


class CaseSerializer(serializers.ModelSerializer):
    court_details = CourtSerializer(source='court', read_only=True)
    category_details = CaseCategorySerializer(source='category', read_only=True)
    managing_organization_details = OrganizationSerializer(source='managing_organization', read_only=True)
    assigned_case_officer_details = UserSerializer(source='assigned_case_officer', read_only=True)
    marked_by_details = UserSerializer(source='marked_by', read_only=True)
    police_station_details = PoliceStationSerializer(source='police_station', read_only=True)
    parties = CasePartySerializer(many=True, read_only=True)
    proceedings = CaseProceedingSerializer(many=True, read_only=True)

    can_work = serializers.SerializerMethodField()
    can_mark = serializers.SerializerMethodField()
    can_mark_back = serializers.SerializerMethodField()
    work_access_type = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            'case_id',
            'case_number',
            'case_title',
            'court',
            'court_details',
            'category',
            'category_details',
            'managing_organization',
            'managing_organization_details',
            'assigned_case_officer',
            'assigned_case_officer_details',
            'marked_by',
            'marked_by_details',
            'marked_at',
            'marking_remarks',
            'institution_number',
            'institution_date',
            'police_station',
            'police_station_details',
            'fir_number',
            'fir_year',
            'offence_sections',
            'status',
            'decision_date',
            'parties',
            'proceedings',
            'can_work',
            'can_mark',
            'can_mark_back',
            'work_access_type',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['case_id', 'marked_by', 'marked_at', 'marking_remarks', 'created_at', 'updated_at']

    def get_can_work(self, obj) -> bool:
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return can_user_work_on_case(request.user, obj)

    def get_can_mark(self, obj) -> bool:
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        is_open = obj.status not in [Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED, Case.CaseStatus.CONSIGNED]
        return is_open and can_user_work_on_case(request.user, obj)

    def get_can_mark_back(self, obj) -> bool:
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated or not obj.marked_by_id:
            return False
        return self.get_can_mark(obj) and obj.marked_by_id != request.user.user_id

    def get_work_access_type(self, obj) -> str:
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return "VIEW_ONLY"
        user = request.user
        if user.is_superuser or user.is_staff:
            return "ADMIN"
        if obj.assigned_case_officer_id == user.user_id:
            return "ASSIGNED"
        if (
            obj.assigned_case_officer
            and getattr(user, 'organization_id', None) is not None
            and getattr(obj.assigned_case_officer, 'organization_id', None) is not None
            and user.organization_id == obj.assigned_case_officer.organization_id
            and getattr(user, 'appointment_id', None) is not None
            and getattr(obj.assigned_case_officer, 'appointment_id', None) is not None
            and user.appointment_id == obj.assigned_case_officer.appointment_id
        ):
            return "PEER"
        return "VIEW_ONLY"


class CaseMarkingHistorySerializer(serializers.ModelSerializer):
    from_user_details = UserSerializer(source='from_user', read_only=True)
    to_user_details = UserSerializer(source='to_user', read_only=True)

    class Meta:
        model = CaseMarkingHistory
        fields = [
            'history_id',
            'case',
            'from_user',
            'from_user_details',
            'to_user',
            'to_user_details',
            'action',
            'remarks',
            'created_at'
        ]
        read_only_fields = ['history_id', 'created_at']


class CaseMarkSerializer(serializers.Serializer):
    to_user_id = serializers.UUIDField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class CaseMarkBackSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class CaseTimelineEventSerializer(serializers.Serializer):
    id = serializers.CharField()
    event_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, default='')
    date = serializers.CharField()
    timestamp = serializers.CharField()
    actor = UserSerializer(read_only=True, required=False, allow_null=True)
    target_user = UserSerializer(read_only=True, required=False, allow_null=True)
    metadata = serializers.DictField(required=False)




class CauseListItemSerializer(serializers.ModelSerializer):
    case_details = CaseSerializer(source='case', read_only=True)
    proceeding_details = CaseProceedingSerializer(source='proceeding', read_only=True)

    class Meta:
        model = CauseListItem
        fields = ['item_id', 'cause_list', 'case', 'case_details', 'proceeding', 'proceeding_details', 'roster_sr_no', 'category_heading']
        read_only_fields = ['item_id']


class CauseListSerializer(serializers.ModelSerializer):
    court_details = CourtSerializer(source='court', read_only=True)
    items = CauseListItemSerializer(many=True, read_only=True)

    class Meta:
        model = CauseList
        fields = ['cause_list_id', 'court', 'court_details', 'cause_list_date', 'day_of_week', 'items', 'created_at']
        read_only_fields = ['cause_list_id', 'created_at']
