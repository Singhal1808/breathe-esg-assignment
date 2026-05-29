from django.test import TestCase

from .models import Site, SourceSystem, Tenant
from .services import ingest_csv


class IngestionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="TestCo", slug="testco")
        self.site = Site.objects.create(tenant=self.tenant, code="BLR-PLANT", name="Bangalore Plant")
        self.source = SourceSystem.objects.create(tenant=self.tenant, source_type="utility", name="Utility CSV")

    def test_utility_csv_flags_non_calendar_billing_period(self):
        csv_text = "\n".join(
            [
                "bill_id,meter_id,site_code,billing_start,billing_end,usage,unit,tariff,estimated,utility,cost_center",
                "B-1,M-1,BLR-PLANT,2026-01-08,2026-02-07,10,MWh,HT,true,BESCOM,FAC",
            ]
        )
        batch = ingest_csv(tenant=self.tenant, source_system=self.source, filename="utility.csv", file_text=csv_text)
        activity = batch.activity_records.first()
        self.assertEqual(activity.normalized_quantity, 10000)
        self.assertIn("billing_period_not_calendar_month", activity.flags)
        self.assertIn("estimated_meter_reading", activity.flags)

