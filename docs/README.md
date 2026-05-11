# PipelineDoctor — Project Documentation

> **An MLOps Observability Platform** for monitoring AI model health, detecting data drift, and escalating production incidents automatically.

---

## 👥 Team

| Member | Role | Responsibility |
|---|---|---|
| Member 1 | Backend Lead | Authentication, Multi-Tenancy, Database Design |
| Member 2 | ML Engineer | MLflow Integration, Drift Detection, Pipeline Orchestration |
| Member 3 | Backend Engineer | Data Quality Checks, Schema Validation, API Development |

---

## 📅 Week 1 — Completed Features

| Feature | Status |
|---|---|
| JWT Authentication (Signup / Login / OTP) | ✅ Done |
| Multi-Tenant Architecture (Schema Isolation) | ✅ Done |
| Team Invite System (Admin → Member) | ✅ Done |
| Baseline Upload & Profiling | ✅ Done |
| Schema Evolution Detection | ✅ Done |
| Data Quality Checks (Nulls, Ranges, Categorical) | ✅ Done |
| MLflow Dynamic Model Loading & Caching | ✅ Done |
| Data Drift Detection (PSI + KS) | ✅ Done |
| Concept Drift Detection | ✅ Done |
| Automated Incident Creation | ✅ Done |

---

## 📁 Documentation Index

| File | Description |
|---|---|
| [authentication.md](./authentication.md) | JWT auth, OTP flow, multi-tenant architecture |
| [data_quality.md](./data_quality.md) | Baseline profiling, schema validation, quality checks |
| [drift_detection.md](./drift_detection.md) | PSI, KS test, concept drift, incident escalation |
| [ml_integration.md](./ml_integration.md) | MLflow connection, dynamic model loading, feature filtering |
| [api_reference.md](./api_reference.md) | Full REST API reference for all endpoints |
| [database_schema.md](./database_schema.md) | All database tables and relationships |
| [setup.md](./setup.md) | Local development setup guide |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | PostgreSQL (Supabase) |
| ORM & Migrations | SQLAlchemy + Alembic |
| ML Registry | MLflow |
| Statistical Testing | SciPy, Evidently AI |
| Auth | JWT (PyJWT) + Bcrypt + OTP Email |
| Email | SMTP (Gmail) |
