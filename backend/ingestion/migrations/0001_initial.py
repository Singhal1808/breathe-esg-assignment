# Generated for the Breathe ESG assignment prototype.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(unique=True)),
                ("reporting_currency", models.CharField(default="USD", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Site",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40)),
                ("name", models.CharField(max_length=160)),
                ("country", models.CharField(default="IN", max_length=2)),
                ("facility_type", models.CharField(blank=True, max_length=80)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sites", to="ingestion.tenant")),
            ],
            options={"unique_together": {("tenant", "code")}},
        ),
        migrations.CreateModel(
            name="SourceSystem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("sap", "SAP"), ("utility", "Utility"), ("travel", "Corporate travel")], max_length=20)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_systems", to="ingestion.tenant")),
            ],
            options={"unique_together": {("tenant", "source_type", "name")}},
        ),
        migrations.CreateModel(
            name="IngestionBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("uploaded", "Uploaded"), ("processed", "Processed"), ("needs_review", "Needs review")], default="uploaded", max_length=24)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
                ("source_system", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="ingestion.sourcesystem")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="ingestion.tenant")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="RawRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_number", models.PositiveIntegerField()),
                ("raw_payload", models.JSONField()),
                ("parse_status", models.CharField(default="parsed", max_length=20)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.ingestionbatch")),
            ],
            options={"unique_together": {("batch", "row_number")}},
        ),
        migrations.CreateModel(
            name="ActivityRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(choices=[("scope_1", "Scope 1"), ("scope_2", "Scope 2"), ("scope_3", "Scope 3")], max_length=20)),
                ("category", models.CharField(max_length=80)),
                ("activity_date", models.DateField(blank=True, null=True)),
                ("period_start", models.DateField(blank=True, null=True)),
                ("period_end", models.DateField(blank=True, null=True)),
                ("quantity", models.DecimalField(decimal_places=4, max_digits=14)),
                ("unit", models.CharField(max_length=24)),
                ("normalized_quantity", models.DecimalField(decimal_places=4, max_digits=14)),
                ("normalized_unit", models.CharField(max_length=24)),
                ("emission_factor_key", models.CharField(blank=True, max_length=120)),
                ("co2e_kg", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("source_reference", models.CharField(max_length=160)),
                ("supplier_or_vendor", models.CharField(blank=True, max_length=160)),
                ("cost_center", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("flagged", "Flagged"), ("approved", "Approved"), ("locked", "Locked"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("flags", models.JSONField(blank=True, default=list)),
                ("edited", models.BooleanField(default=False)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="activity_records", to="ingestion.ingestionbatch")),
                ("raw_record", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="activity_record", to="ingestion.rawrecord")),
                ("site", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.site")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_records", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=40)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activity_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.activityrecord")),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.tenant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

