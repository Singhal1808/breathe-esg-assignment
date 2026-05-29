from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ActivityRecord, IngestionBatch, RawRecord, SourceSystem, Tenant
from .serializers import (
    ActivityEditSerializer,
    ActivityRecordSerializer,
    AuditEventSerializer,
    IngestionBatchSerializer,
    RawRecordSerializer,
    SourceSystemSerializer,
    TenantSerializer,
)
from .services import audit, ingest_csv


def current_tenant(request):
    tenant_id = request.query_params.get("tenant") or request.data.get("tenant")
    if tenant_id:
        return Tenant.objects.get(id=tenant_id)
    return Tenant.objects.first()


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSerializer


class SourceSystemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SourceSystemSerializer

    def get_queryset(self):
        tenant = current_tenant(self.request)
        return SourceSystem.objects.filter(tenant=tenant).order_by("source_type", "name")


class BatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngestionBatchSerializer

    def get_queryset(self):
        tenant = current_tenant(self.request)
        return (
            IngestionBatch.objects.filter(tenant=tenant)
            .select_related("source_system")
            .annotate(
                raw_count=Count("raw_records"),
                activity_count=Count("activity_records"),
                flagged_count=Count("activity_records", filter=Q(activity_records__status=ActivityRecord.FLAGGED)),
                failed_count=Count("raw_records", filter=Q(raw_records__parse_status="failed")),
            )
            .order_by("-uploaded_at")
        )

    @action(detail=True, methods=["get"])
    def raw_records(self, request, pk=None):
        records = RawRecord.objects.filter(batch_id=pk).order_by("row_number")
        return Response(RawRecordSerializer(records, many=True).data)


class ActivityRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ActivityRecordSerializer

    def get_queryset(self):
        tenant = current_tenant(self.request)
        qs = ActivityRecord.objects.filter(tenant=tenant).select_related("site", "batch", "batch__source_system")
        status_filter = self.request.query_params.get("status")
        source_type = self.request.query_params.get("source_type")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if source_type:
            qs = qs.filter(batch__source_system__source_type=source_type)
        return qs.order_by("-updated_at")

    def update(self, request, *args, **kwargs):
        activity = self.get_object()
        if activity.status == ActivityRecord.LOCKED:
            return Response({"detail": "Locked records cannot be edited."}, status=status.HTTP_400_BAD_REQUEST)
        before = ActivityRecordSerializer(activity).data
        serializer = ActivityEditSerializer(activity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(edited=True, status=ActivityRecord.FLAGGED)
        audit(activity, request.user, "edited", before=before, after=ActivityRecordSerializer(activity).data)
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        activity = self.get_object()
        if activity.status == ActivityRecord.LOCKED:
            return Response({"detail": "Record is already locked."}, status=status.HTTP_400_BAD_REQUEST)
        before = {"status": activity.status, "flags": activity.flags}
        activity.status = ActivityRecord.APPROVED
        activity.flags = []
        activity.approved_by = request.user
        activity.save(update_fields=["status", "flags", "approved_by", "updated_at"])
        audit(activity, request.user, "approved", before=before, after={"status": activity.status})
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        activity = self.get_object()
        before = {"status": activity.status}
        activity.status = ActivityRecord.REJECTED
        activity.save(update_fields=["status", "updated_at"])
        audit(activity, request.user, "rejected", before=before, after={"status": activity.status}, note=request.data.get("note", ""))
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        activity = self.get_object()
        if activity.status != ActivityRecord.APPROVED:
            return Response({"detail": "Only approved records can be locked."}, status=status.HTTP_400_BAD_REQUEST)
        before = {"status": activity.status}
        activity.status = ActivityRecord.LOCKED
        activity.locked_at = timezone.now()
        activity.save(update_fields=["status", "locked_at", "updated_at"])
        audit(activity, request.user, "locked", before=before, after={"status": activity.status})
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        return Response(AuditEventSerializer(self.get_object().audit_events.all(), many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    tenant = current_tenant(request)
    records = ActivityRecord.objects.filter(tenant=tenant)
    return Response(
        {
            "tenant": TenantSerializer(tenant).data,
            "total_records": records.count(),
            "pending": records.filter(status=ActivityRecord.PENDING).count(),
            "flagged": records.filter(status=ActivityRecord.FLAGGED).count(),
            "approved": records.filter(status=ActivityRecord.APPROVED).count(),
            "locked": records.filter(status=ActivityRecord.LOCKED).count(),
            "failed_rows": RawRecord.objects.filter(batch__tenant=tenant, parse_status="failed").count(),
            "co2e_kg": float(sum((r.co2e_kg or 0) for r in records)),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload(request):
    tenant = current_tenant(request)
    source_system = SourceSystem.objects.get(id=request.data["source_system"], tenant=tenant)
    upload_file = request.FILES["file"]
    file_text = upload_file.read().decode("utf-8-sig")
    batch = ingest_csv(
        tenant=tenant,
        source_system=source_system,
        filename=upload_file.name,
        file_text=file_text,
        user=request.user,
    )
    return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
