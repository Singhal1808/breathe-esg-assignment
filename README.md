# Breathe ESG Assignment

A focused Django REST + React prototype for ingesting messy enterprise ESG activity data, normalizing it, and giving analysts a review workflow before records are locked for audit.

## Demo Scope

- SAP-style material document CSV for fuel and procurement rows.
- Utility portal CSV for electricity meter bills.
- Concur-style travel export CSV for flights, hotels, rail, and ground transport.
- Analyst dashboard showing ingestion batches, failed rows, suspicious rows, normalized activity records, and approval/lock actions.
- Data model designed for multi-tenancy, source tracking, unit normalization, edits, review state, and audit history.

## Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Default demo login:

- Email: `analyst@demo.com`
- Password: `BreatheDemo123!`

## Deployment

The repo includes `render.yaml` for a Render deployment:

- Django web service from `backend`
- PostgreSQL database
- React static site from `frontend`

Set these environment variables for production:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_URL`

## Required Assignment Docs

- [MODEL.md](MODEL.md)
- [DECISIONS.md](DECISIONS.md)
- [TRADEOFFS.md](TRADEOFFS.md)
- [SOURCES.md](SOURCES.md)

