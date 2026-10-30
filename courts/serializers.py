from rest_framework import serializers
from .models import Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding, CauseList, CauseListItem
from organizations.serializers import OrganizationSerializer
from users.serializers import UserSerializer

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
    police_station_details = PoliceStationSerializer(source='police_station', read_only=True)
    parties = CasePartySerializer(many=True, read_only=True)
    proceedings = CaseProceedingSerializer(many=True, read_only=True)

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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['case_id', 'created_at', 'updated_at']


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
