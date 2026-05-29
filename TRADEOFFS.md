# Tradeoffs

## 1. I Did Not Build PDF Utility Bill Parsing

PDF parsing would be impressive but brittle. Utility bills vary heavily by provider, layout, and scanned quality. A portal CSV is a more reliable onboarding path for a 4-day prototype and still lets the app model meters, tariffs, units, and billing periods.

## 2. I Did Not Build Live SAP Or Concur Integrations

Real SAP and Concur integrations require credentials, tenant configuration, OAuth/security review, and client-specific field mappings. I modeled realistic exports instead. This keeps the prototype honest while still demonstrating the ingestion and normalization pipeline.

## 3. I Did Not Build A Full Emission Factor Engine

The app uses small fixed factors to calculate indicative CO2e. A real factor engine would need geography, year, methodology, supplier-specific factors, unit families, versioning, and auditor-approved factor sets. I kept the assignment focused on data ingestion, traceability, review, and audit lock.

