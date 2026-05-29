import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.db import transaction

from .models import ActivityRecord, AuditEvent, IngestionBatch, RawRecord, Site


UNIT_FACTORS = {
    "l": ("liter", Decimal("1")),
    "liter": ("liter", Decimal("1")),
    "litre": ("liter", Decimal("1")),
    "gal": ("liter", Decimal("3.78541")),
    "gallon": ("liter", Decimal("3.78541")),
    "kwh": ("kWh", Decimal("1")),
    "mwh": ("kWh", Decimal("1000")),
    "km": ("km", Decimal("1")),
    "mi": ("km", Decimal("1.60934")),
    "night": ("night", Decimal("1")),
    "nights": ("night", Decimal("1")),
    "usd": ("USD", Decimal("1")),
    "inr": ("INR", Decimal("1")),
}

EMISSION_FACTORS = {
    "fuel:diesel:liter": Decimal("2.68"),
    "fuel:petrol:liter": Decimal("2.31"),
    "electricity:india:kWh": Decimal("0.716"),
    "travel:flight:km": Decimal("0.158"),
    "travel:rail:km": Decimal("0.035"),
    "travel:ground:km": Decimal("0.121"),
    "travel:hotel:night": Decimal("28.00"),
}

SAP_HEADER_ALIASES = {
    "Buchungsdatum": "posting_date",
    "Posting Date": "posting_date",
    "Werkscode": "plant_code",
    "Plant": "plant_code",
    "Material": "material",
    "Materialkurztext": "material_description",
    "Quantity": "quantity",
    "Menge": "quantity",
    "UoM": "unit",
    "MEINS": "unit",
    "Movement Type": "movement_type",
    "GoodsMovementType": "movement_type",
    "CostCenter": "cost_center",
    "Supplier": "supplier",
    "PurchaseOrder": "purchase_order",
    "Document": "document",
}


@dataclass
class NormalizedRow:
    raw: dict
    data: dict | None
    flags: list[str]
    error: str = ""


def parse_date(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def parse_decimal(value):
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Invalid number: {value}")


def normalize_unit(quantity, unit):
    key = str(unit or "").strip().lower()
    if key not in UNIT_FACTORS:
        raise ValueError(f"Unsupported unit: {unit}")
    normalized_unit, factor = UNIT_FACTORS[key]
    return quantity * factor, normalized_unit


def find_site(tenant, code, flags):
    if not code:
        flags.append("missing_site_code")
        return None
    site = Site.objects.filter(tenant=tenant, code=str(code).strip()).first()
    if not site:
        flags.append(f"unknown_site:{code}")
    return site


def co2e_for(key, quantity):
    factor = EMISSION_FACTORS.get(key)
    if factor is None:
        return None
    return quantity * factor


def normalize_sap(row, tenant):
    mapped = {SAP_HEADER_ALIASES.get(k, k): v for k, v in row.items()}
    flags = []
    quantity = parse_decimal(mapped.get("quantity"))
    normalized_quantity, normalized_unit = normalize_unit(quantity, mapped.get("unit"))
    material = str(mapped.get("material") or mapped.get("material_description") or "").lower()
    scope = ActivityRecord.SCOPE_1 if "diesel" in material or "petrol" in material else ActivityRecord.SCOPE_3
    category = "diesel" if "diesel" in material else "petrol" if "petrol" in material else "procurement"
    factor_key = f"fuel:{category}:liter" if category in {"diesel", "petrol"} else ""
    if not factor_key:
        flags.append("missing_procurement_emission_factor")
    data = {
        "site": find_site(tenant, mapped.get("plant_code"), flags),
        "scope": scope,
        "category": category,
        "activity_date": parse_date(mapped.get("posting_date")),
        "quantity": quantity,
        "unit": mapped.get("unit"),
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "emission_factor_key": factor_key,
        "co2e_kg": co2e_for(factor_key, normalized_quantity),
        "source_reference": mapped.get("document") or mapped.get("purchase_order") or "sap-row",
        "supplier_or_vendor": mapped.get("supplier", ""),
        "cost_center": mapped.get("cost_center", ""),
    }
    return NormalizedRow(row, data, flags)


def normalize_utility(row, tenant):
    flags = []
    quantity = parse_decimal(row.get("usage"))
    normalized_quantity, normalized_unit = normalize_unit(quantity, row.get("unit"))
    start = parse_date(row.get("billing_start"))
    end = parse_date(row.get("billing_end"))
    if start and end and start.day != 1:
        flags.append("billing_period_not_calendar_month")
    if str(row.get("estimated", "")).lower() in {"true", "yes", "1"}:
        flags.append("estimated_meter_reading")
    factor_key = "electricity:india:kWh"
    data = {
        "site": find_site(tenant, row.get("site_code"), flags),
        "scope": ActivityRecord.SCOPE_2,
        "category": "electricity",
        "period_start": start,
        "period_end": end,
        "quantity": quantity,
        "unit": row.get("unit"),
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "emission_factor_key": factor_key,
        "co2e_kg": co2e_for(factor_key, normalized_quantity),
        "source_reference": row.get("bill_id") or row.get("meter_id") or "utility-row",
        "supplier_or_vendor": row.get("utility", ""),
        "cost_center": row.get("cost_center", ""),
    }
    return NormalizedRow(row, data, flags)


def normalize_travel(row, tenant):
    flags = []
    travel_type = str(row.get("travel_type", "")).lower()
    quantity_value = row.get("distance") or row.get("nights") or row.get("amount")
    quantity = parse_decimal(quantity_value)
    unit = row.get("unit") or ("night" if travel_type == "hotel" else "km")
    normalized_quantity, normalized_unit = normalize_unit(quantity, unit)
    if travel_type == "flight" and not row.get("distance"):
        flags.append("flight_distance_missing_using_review_required")
    if travel_type == "flight" and (not row.get("origin") or not row.get("destination")):
        flags.append("missing_airport_code")
    factor_type = "ground" if travel_type in {"taxi", "car", "rideshare"} else travel_type
    factor_key = f"travel:{factor_type}:{normalized_unit}"
    if factor_key not in EMISSION_FACTORS:
        flags.append("missing_travel_emission_factor")
    data = {
        "site": find_site(tenant, row.get("site_code"), flags),
        "scope": ActivityRecord.SCOPE_3,
        "category": travel_type or "travel",
        "activity_date": parse_date(row.get("trip_start")),
        "quantity": quantity,
        "unit": unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "emission_factor_key": factor_key,
        "co2e_kg": co2e_for(factor_key, normalized_quantity),
        "source_reference": row.get("booking_id") or row.get("expense_report_id") or "travel-row",
        "supplier_or_vendor": row.get("vendor", ""),
        "cost_center": row.get("cost_center", ""),
    }
    return NormalizedRow(row, data, flags)


NORMALIZERS = {
    "sap": normalize_sap,
    "utility": normalize_utility,
    "travel": normalize_travel,
}


@transaction.atomic
def ingest_csv(*, tenant, source_system, filename, file_text, user=None):
    batch = IngestionBatch.objects.create(
        tenant=tenant,
        source_system=source_system,
        filename=filename,
        uploaded_by=user if getattr(user, "is_authenticated", False) else None,
    )
    reader = csv.DictReader(StringIO(file_text))
    normalizer = NORMALIZERS[source_system.source_type]
    flagged = 0
    failed = 0
    created = 0

    for row_number, row in enumerate(reader, start=2):
        raw = RawRecord.objects.create(batch=batch, row_number=row_number, raw_payload=row)
        try:
            normalized = normalizer(row, tenant)
            status = ActivityRecord.FLAGGED if normalized.flags else ActivityRecord.PENDING
            if normalized.flags:
                flagged += 1
            ActivityRecord.objects.create(
                tenant=tenant,
                batch=batch,
                raw_record=raw,
                status=status,
                flags=normalized.flags,
                **normalized.data,
            )
            created += 1
        except Exception as exc:
            raw.parse_status = "failed"
            raw.error_message = str(exc)
            raw.save(update_fields=["parse_status", "error_message"])
            failed += 1

    batch.status = IngestionBatch.NEEDS_REVIEW if flagged or failed else IngestionBatch.PROCESSED
    batch.notes = f"{created} normalized, {flagged} flagged, {failed} failed"
    batch.save(update_fields=["status", "notes"])
    return batch


def audit(activity, actor, event_type, before=None, after=None, note=""):
    return AuditEvent.objects.create(
        tenant=activity.tenant,
        activity_record=activity,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        event_type=event_type,
        before=before,
        after=after,
        note=note,
    )

