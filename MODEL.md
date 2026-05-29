# Data Model

## Goal

The model separates source ingestion from analyst-approved activity records. That is deliberate: raw client data is often messy, but auditors need to know exactly what arrived, how it was normalized, who touched it, and when it became locked.

## Core Entities

### Tenant

Represents one client company. All operational tables point back to a tenant so the same app can host multiple clients without mixing data.

Important fields:

- `name`
- `slug`
- `reporting_currency`

### Site

Maps client-specific facility or plant codes to a meaningful location. This matters because SAP often uses plant codes that are only useful with a lookup table.

Important fields:

- `tenant`
- `code`
- `name`
- `country`
- `facility_type`

### SourceSystem

Defines the data-producing system for a tenant. In this prototype the supported source types are:

- `sap`
- `utility`
- `travel`

This lets the ingestion layer use source-specific parsers while keeping normalized activity records in one table.

### IngestionBatch

One uploaded file or source pull. Batches are the operational unit analysts can inspect.

Important fields:

- `tenant`
- `source_system`
- `filename`
- `status`
- `uploaded_by`
- `uploaded_at`
- `notes`

### RawRecord

Stores the original row payload exactly as received from the client file. Failed rows stay here with an error message even if they never become normalized activity records.

Important fields:

- `batch`
- `row_number`
- `raw_payload`
- `parse_status`
- `error_message`

### ActivityRecord

The normalized reviewable ESG activity row. This is the row analysts approve and lock.

Important fields:

- `tenant`
- `batch`
- `raw_record`
- `site`
- `scope`
- `category`
- `activity_date`
- `period_start`
- `period_end`
- `quantity`
- `unit`
- `normalized_quantity`
- `normalized_unit`
- `emission_factor_key`
- `co2e_kg`
- `source_reference`
- `supplier_or_vendor`
- `cost_center`
- `status`
- `flags`
- `edited`
- `approved_by`
- `locked_at`

### AuditEvent

Append-only record of analyst actions. Edits, approvals, rejections, and locks are represented here.

Important fields:

- `tenant`
- `activity_record`
- `actor`
- `event_type`
- `before`
- `after`
- `note`
- `created_at`

## Review State

The workflow is:

1. `pending`
2. `flagged`
3. `approved`
4. `locked`

Rows can also be `rejected`.

Only approved rows can be locked. Locked rows cannot be edited. This models the audit boundary: before lock, analysts can correct data; after lock, changes should happen through a controlled adjustment flow.

## Scope Categorization

- SAP diesel/petrol rows are treated as Scope 1 because they represent owned fuel combustion.
- Utility electricity rows are Scope 2.
- Travel rows are Scope 3.
- SAP procurement rows are Scope 3, but this prototype flags them if there is no emission factor mapping.

## Unit Normalization

The system stores both original and normalized values:

- Original: `quantity`, `unit`
- Normalized: `normalized_quantity`, `normalized_unit`

Examples:

- gallons to liters
- MWh to kWh
- miles to kilometers

Keeping both values prevents loss of source fidelity while giving analysts one comparable quantity for review.

## Source Of Truth

Each normalized record points to:

- The exact `RawRecord`
- The `IngestionBatch`
- The `SourceSystem`
- A `source_reference`, such as SAP material document, utility bill ID, or travel booking ID

That chain answers: where did this row come from, when did it arrive, and what did the original row say?

## Tradeoff In The Model

I used one `ActivityRecord` table instead of separate tables for fuel, electricity, and travel. The shared table makes the review workflow simple and consistent. Source-specific detail remains in `RawRecord.raw_payload`. In a production system, I would add typed detail tables once the source contracts stabilize.

