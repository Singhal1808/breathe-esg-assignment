from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ingestion.models import Site, SourceSystem, Tenant
from ingestion.services import ingest_csv


class Command(BaseCommand):
    help = "Create demo tenant, user, sources, sites, and ingest sample CSV files."

    def handle(self, *args, **options):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="analyst@demo.com",
            defaults={"email": "analyst@demo.com", "is_staff": True, "is_superuser": True},
        )
        user.email = "analyst@demo.com"
        user.is_staff = True
        user.is_superuser = True
        user.set_password("BreatheDemo123!")
        user.save()

        tenant, _ = Tenant.objects.get_or_create(slug="acme-industries", defaults={"name": "Acme Industries"})
        Site.objects.get_or_create(tenant=tenant, code="BLR-PLANT", defaults={"name": "Bangalore Manufacturing Plant", "country": "IN", "facility_type": "manufacturing"})
        Site.objects.get_or_create(tenant=tenant, code="PUN-DC", defaults={"name": "Pune Distribution Center", "country": "IN", "facility_type": "warehouse"})
        Site.objects.get_or_create(tenant=tenant, code="MUM-HQ", defaults={"name": "Mumbai Corporate HQ", "country": "IN", "facility_type": "office"})

        sources = {
            "sap": SourceSystem.objects.get_or_create(
                tenant=tenant,
                source_type="sap",
                name="SAP MM flat export",
                defaults={"description": "Material document style CSV from SAP MM."},
            )[0],
            "utility": SourceSystem.objects.get_or_create(
                tenant=tenant,
                source_type="utility",
                name="Utility portal electricity CSV",
                defaults={"description": "Monthly meter/bill export from utility portal."},
            )[0],
            "travel": SourceSystem.objects.get_or_create(
                tenant=tenant,
                source_type="travel",
                name="Concur-style travel export",
                defaults={"description": "Expense/travel rows exported from corporate travel platform."},
            )[0],
        }

        sample_dir = Path(__file__).resolve().parents[4] / "sample_data"
        for source_type, filename in {
            "sap": "sample_sap_fuel_procurement.csv",
            "utility": "sample_utility_electricity.csv",
            "travel": "sample_travel_bookings.csv",
        }.items():
            if not sources[source_type].batches.filter(filename=filename).exists():
                ingest_csv(
                    tenant=tenant,
                    source_system=sources[source_type],
                    filename=filename,
                    file_text=(sample_dir / filename).read_text(encoding="utf-8"),
                    user=user,
                )

        self.stdout.write(self.style.SUCCESS("Demo data ready. Login: analyst@demo.com / BreatheDemo123!"))
