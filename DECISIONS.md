# Decisions

## Chosen Source Mechanisms

### SAP

I chose a SAP Material Management style flat CSV export, based on SAP material document concepts such as posting date, plant, material, movement type, entry unit, quantity, supplier, and purchase order.

Why:

- It is realistic for an analyst or implementation team to receive SAP report exports during onboarding.
- It avoids pretending we have customer SAP credentials for OData/BAPI access.
- It still captures SAP messiness: plant codes, movement types, mixed units, localized headers, and date formats.

Ignored:

- Direct SAP OData authentication.
- IDoc parsing.
- Full procurement spend-based emissions.

### Utility Electricity

I chose a utility portal CSV export inspired by Green Button/utility meter concepts: meter ID, billing period, interval or billing quantity, unit, tariff, and estimated-read flag.

Why:

- Facilities teams commonly download portal CSVs or spreadsheets.
- PDF bill parsing would be fragile for a 4-day prototype.
- Billing periods often do not align with calendar months, which is important for ESG review.

Ignored:

- PDF bill OCR.
- Interval-level Green Button XML parsing.
- Demand charges and time-of-use tariff calculations.

### Corporate Travel

I chose a Concur-style travel/expense export with booking ID, expense report ID, travel category, origin, destination, date, distance, nights, amount, vendor, and cost center.

Why:

- Travel platforms expose both itinerary-style and expense-style records.
- ESG treatment depends heavily on category: flights, hotels, rail, and ground transport need different factors.
- Distances are not always present, especially in expense exports, so the app flags missing flight distance.

Ignored:

- Live Concur/Navan OAuth integration.
- Airport-to-airport distance lookup.
- Cabin class multipliers.

## Product Decisions

### One Review Queue

I used a single normalized review queue across all sources. Analysts should not need to learn three workflows for three source systems.

### Flags Instead Of Hard Failures Where Possible

Rows with unknown sites or suspicious billing periods become reviewable flagged rows. Rows that cannot be parsed at all become failed raw rows.

### Simple Emission Factors

The prototype uses simple fixed emission factors. This is enough to show normalization and review behavior, but production would need factor libraries by geography, date, fuel type, supplier, and methodology.

### Multi-Tenancy From Day One

Even though the demo has one tenant, every important object belongs to a tenant. Retrofitting multi-tenancy later is risky in audit-heavy systems.

## Questions I Would Ask The PM

- Which carbon accounting methodology should this client follow?
- Does Breathe already maintain emission factor libraries?
- Should procurement use spend-based factors, supplier-specific factors, or product-level quantities?
- Who is allowed to approve and lock records?
- Does the audit lock happen per row, per batch, or per reporting period?
- Are client plant/site lookup tables available before ingestion?
- Should billing periods be split across reporting months?
- What source should win if SAP and a manual spreadsheet disagree?

