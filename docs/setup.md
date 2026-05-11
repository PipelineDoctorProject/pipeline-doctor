# Local Development Setup

This guide walks you through setting up PipelineDoctor on your local machine from scratch.

---

## 📋 Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| PostgreSQL | 14+ | Database (or use Supabase) |
| MLflow | Any | Model registry |
| Git | Any | Version control |

---

## 1️⃣ Clone & Enter the Project

```bash
git clone <your-repo-url>
cd pipeline-doctor/backend/fastapi
```

---

## 2️⃣ Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment Variables

Create a `.env` file in `backend/fastapi/`:

```env
# Database (Supabase or local PostgreSQL)
DB_NAME=postgres
DB_USER=postgres.your_project_ref
DB_PASSWORD=your_password
DB_HOST=aws-0-ap-south-1.pooler.supabase.com
DB_PORT=5432

# JWT
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256

# Email (for OTP and invites)
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=PipelineDoctor
```

> **Note:** For Gmail, use an [App Password](https://myaccount.google.com/apppasswords), not your regular password.

---

## 5️⃣ Run Database Migrations

```bash
alembic upgrade head
```

This creates all required tables in your PostgreSQL database.

---

## 6️⃣ Start the MLflow Server

In a **separate terminal**:

```bash
mlflow server --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000` to verify it's running.

---

## 7️⃣ Train & Register the Demo Model

```bash
python app/ml/train_register_model.py
```

Then go to `http://127.0.0.1:5000`, open the **Models** tab, and assign the `champion` alias to Version 1 of `PipelineDoctorDemoModel`.

---

## 8️⃣ Start the FastAPI Backend

```bash
uvicorn app.main:app --reload
```

- API runs at: `http://127.0.0.1:8000`
- Swagger UI at: `http://127.0.0.1:8000/docs`

---

## 9️⃣ Register Your Model via Swagger

Open Swagger at `/docs` and call `POST /ml-models/`:

```json
{
  "name": "Demo Model",
  "version": "1.0",
  "mlflow_model_name": "PipelineDoctorDemoModel",
  "mlflow_alias": "champion",
  "mlflow_tracking_uri": "http://127.0.0.1:5000",
  "expected_features": ["age", "salary", "bonus"]
}
```

---

## 🔟 Upload a Baseline CSV

Use `POST /baseline/upload?model_id=1` and upload your reference CSV.

---

## 1️⃣1️⃣ Run the Pipeline

Drop a production CSV into `uploads/incoming/` and run:

```bash
python run_auto_runner.py
```

Check your database for:
- `prediction_logs` — AI predictions
- `drift_findings` — Statistical drift scores
- `incidents` — Auto-created alerts

---

## 🗂️ Project Structure

```
pipeline-doctor/
├── backend/
│   └── fastapi/
│       ├── app/
│       │   ├── api/routes/       ← FastAPI route handlers
│       │   ├── core/             ← JWT, security utils
│       │   ├── middleware/       ← Auth middleware
│       │   ├── models/           ← SQLAlchemy DB models
│       │   ├── schemas/          ← Pydantic request/response schemas
│       │   ├── services/
│       │   │   ├── auth/         ← Signup, login, OTP, invite
│       │   │   ├── quality/      ← Baseline, validator, pipeline
│       │   │   └── drift/        ← Data drift, concept drift
│       │   ├── utils/            ← Email, OTP, schema utils
│       │   └── main.py           ← FastAPI app entry point
│       ├── alembic/              ← Database migrations
│       ├── uploads/              ← Incoming / processed / baseline CSVs
│       └── run_auto_runner.py    ← Pipeline execution entry point
├── docs/                         ← Project documentation (you are here)
├── agents/                       ← AI reasoning agents (Stage 8)
└── frontend/                     ← Frontend application
```