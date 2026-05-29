from rest_framework import serializers

from .models import ActivityRecord, AuditEvent, IngestionBatch, RawRecord, Site, SourceSystem, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "reporting_currency"]


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "code", "name", "country", "facility_type"]


class SourceSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceSystem
        fields = ["id", "source_type", "name", "description"]


class IngestionBatchSerializer(serializers.ModelSerializer):
    source_system = SourceSystemSerializer(read_only=True)
    raw_count = serializers.IntegerField(read_only=True)
    activity_count = serializers.IntegerField(read_only=True)
    flagged_count = serializers.IntegerField(read_only=True)
    failed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = IngestionBatch
        fields = [
            "id",
            "source_system",
            "filename",
            "status",
            "uploaded_at",
            "notes",
            "raw_count",
            "activity_count",
            "flagged_count",
            "failed_count",
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ["id", "row_number", "raw_payload", "parse_status", "error_message"]


class ActivityRecordSerializer(serializers.ModelSerializer):
    site = SiteSerializer(read_only=True)
    source_type = serializers.CharField(source="batch.source_system.source_type", read_only=True)
    batch_filename = serializers.CharField(source="batch.filename", read_only=True)

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "source_type",
            "batch_filename",
            "site",
            "scope",
            "category",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "unit",
            "normalized_quantity",
            "normalized_unit",
            "emission_factor_key",
            "co2e_kg",
            "source_reference",
            "supplier_or_vendor",
            "cost_center",
            "status",
            "flags",
            "edited",
            "locked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "flags", "locked_at", "created_at", "updated_at", "edited"]


class ActivityEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityRecord
        fields = ["category", "normalized_quantity", "normalized_unit", "emission_factor_key", "co2e_kg", "cost_center"]


class AuditEventSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ["id", "actor", "event_type", "before", "after", "note", "created_at"]

