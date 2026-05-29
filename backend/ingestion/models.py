from django.conf import settings
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    reporting_currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Site(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sites")
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=2, default="IN")
    facility_type = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceSystem(models.Model):
    SAP = "sap"
    UTILITY = "utility"
    TRAVEL = "travel"
    SOURCE_TYPES = [(SAP, "SAP"), (UTILITY, "Utility"), (TRAVEL, "Corporate travel")]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="source_systems")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("tenant", "source_type", "name")

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    STATUSES = [(UPLOADED, "Uploaded"), (PROCESSED, "Processed"), (NEEDS_REVIEW, "Needs review")]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source_system = models.ForeignKey(SourceSystem, on_delete=models.PROTECT, related_name="batches")
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=24, choices=STATUSES, default=UPLOADED)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source_system.name}: {self.filename}"


class RawRecord(models.Model):
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField()
    parse_status = models.CharField(max_length=20, default="parsed")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("batch", "row_number")


class ActivityRecord(models.Model):
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"
    SCOPES = [(SCOPE_1, "Scope 1"), (SCOPE_2, "Scope 2"), (SCOPE_3, "Scope 3")]

    PENDING = "pending"
    FLAGGED = "flagged"
    APPROVED = "approved"
    LOCKED = "locked"
    REJECTED = "rejected"
    STATUSES = [
        (PENDING, "Pending"),
        (FLAGGED, "Flagged"),
        (APPROVED, "Approved"),
        (LOCKED, "Locked"),
        (REJECTED, "Rejected"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="activity_records")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.PROTECT, related_name="activity_records")
    raw_record = models.OneToOneField(RawRecord, on_delete=models.PROTECT, related_name="activity_record")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True)
    scope = models.CharField(max_length=20, choices=SCOPES)
    category = models.CharField(max_length=80)
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=24)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    normalized_unit = models.CharField(max_length=24)
    emission_factor_key = models.CharField(max_length=120, blank=True)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    source_reference = models.CharField(max_length=160)
    supplier_or_vendor = models.CharField(max_length=160, blank=True)
    cost_center = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default=PENDING)
    flags = models.JSONField(default=list, blank=True)
    edited = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} {self.normalized_quantity} {self.normalized_unit}"


class AuditEvent(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_events")
    activity_record = models.ForeignKey(ActivityRecord, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=40)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

