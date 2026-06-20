from fastapi import Depends, FastAPI, Query
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.config.settings import get_allowed_origins

from app.api.routes import (
    auth,
    agent_trace,
    dashboard,
    data_quality,
    drift_findings,
    health,
    incidents,
    invite,
    ml_models,
    onboarding,
    predictions,
    remediation,
    reports,
    runs,
    schema,
    slack,
    tenant,
    upload_baseline,
)

from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI(title="PipelineDoctor API", version="1.0.0")

# ==========================================
# MIDDLEWARE
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)


# ==========================================
# ROUTERS
# ==========================================

app.include_router(health.router)
app.include_router(runs.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(data_quality.router)
app.include_router(drift_findings.router)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(invite.router)
app.include_router(upload_baseline.router)
app.include_router(ml_models.router)
app.include_router(dashboard.router)
app.include_router(schema.router)
app.include_router(tenant.router)
app.include_router(agent_trace.router)  # WS /ws/agent-trace/{run_id}
app.include_router(remediation.router)
app.include_router(slack.router)
app.include_router(reports.router)


@app.get("/")
def root(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if code or state or error:
        return slack.slack_callback(code=code, state=state, error=error, db=db)

    return {"status": "ok"}



# ==========================================
# SWAGGER JWT AUTH
# ==========================================

def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="PipelineDoctor API",
        version="1.0.0",
        description="PipelineDoctor Backend APIs",
        routes=app.routes,
    )

    # JWT Bearer configuration
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Apply globally to all routes
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi
