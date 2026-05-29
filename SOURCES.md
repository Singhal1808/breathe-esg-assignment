# Sources

## SAP Fuel And Procurement

Researched format:

- SAP S/4HANA Material Document API and material document field concepts.
- Relevant fields include material document, posting date, plant, material, movement type, quantity, entry unit, supplier, and purchase order.

Useful references:

- SAP Help, Material Document API operations: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/eb2a39dd0c124fed8252f684002d55e1/1aef4e402acd4c8b8ec2ea2bfda7715b.html
- SAP Help, Read Material Documents: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/eb2a39dd0c124fed8252f684002d55e1/78f5a8461d554cc38b3af2d07d6f9c8e.html
- SAP Help, material document fields including posting date and SAP unit code: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/1891d652a8d54a46a587bc11a0a713c7.html

What I learned:

- SAP material documents are commonly queried by posting date/year and can be filtered by plant or storage location.
- Plant codes and material numbers are not self-explanatory without lookup tables.
- SAP exports may contain SAP-specific units and localized headers.

Sample data:

- `sample_data/sample_sap_fuel_procurement.csv`
- Includes German header names, plant codes, material descriptions, mixed date formats, liters/gallons, and one procurement row with unsupported unit `EA`.

What would break in production:

- Client-specific SAP custom fields.
- Unknown material-to-emissions mappings.
- IDoc/OData authentication and authorization.
- Unit codes not in the prototype conversion table.

## Utility Electricity

Researched format:

- Utility portal CSVs and Green Button-inspired electricity usage structures.
- Green Button data uses concepts such as UsagePoint, MeterReading, ReadingType, IntervalBlock, and IntervalReading.

Useful references:

- Green Button Alliance, Usage Data: https://www.greenbuttonalliance.org/usage-data
- Green Button Alliance, Usage Data Interval Metering: https://www.greenbuttonalliance.org/fb04

What I learned:

- Meter data has a usage point/meter identity, readings, intervals, units, and time periods.
- Billing periods do not always align to calendar months.
- Estimated readings are important review signals.

Sample data:

- `sample_data/sample_utility_electricity.csv`
- Includes meter IDs, bill IDs, site codes, billing start/end dates, kWh/MWh usage, tariff names, utilities, and estimated-read flags.

What would break in production:

- PDF-only bills.
- Interval data too large for row-by-row upload.
- Tariff-specific demand charges.
- Splitting bills across reporting periods.

## Corporate Travel

Researched format:

- SAP Concur expense/travel records and itinerary-style segment data.
- Relevant fields include expense report, expense entry, payment/currency, vendor, city/location, travel segments, booking IDs, airport/city codes, and dates.

Useful references:

- SAP Concur Developer Center, Financial Integration service showing expense entry fields: https://preview.developer.concur.com/api-reference/financial-integration/v4.financial-integration.html
- SAP Concur Developer Center, Expense configuration/payment types: https://preview.developer.concur.com/api-reference/expense/expense-config/v4.expense.config.html
- SAP Help, Concur Travel hotel segment format: https://help.sap.com/docs/CONCUR_TRAVEL/ab1138d052604b6d98d43485e50525f8/a086878170631014910ed88b30cbd5f5.html

What I learned:

- Travel systems can expose both itinerary details and expense/reporting records.
- Flights, hotels, rail, and ground transport need different emissions treatment.
- Distance is often not directly present in expense-style exports.

Sample data:

- `sample_data/sample_travel_bookings.csv`
- Includes booking ID, expense report ID, employee ID, travel type, origin, destination, distance, nights, amount, vendor, site, and cost center.

What would break in production:

- Missing or ambiguous airport codes.
- Multi-leg itineraries.
- Cabin class effects.
- Hotel country/city-specific emission factors.
- Reconciliation between booked travel and expensed travel.

