from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import FRONTEND_URL

from app.api.routes import (
    health,
    runs,
    incidents,
    predictions,
    drift_findings,
    data_quality,
    auth,
    onboarding,
    invite,
    upload_baseline,
    schema,
    dashboard,
    tenant,
    agent_trace,
    slack,
)

from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI()



# ==========================================
# MIDDLEWARE
# ==========================================

from app.api.routes import (health, 
                            runs,
                            incidents,
                            predictions,
                            drift_findings,
                            auth,upload_baseline,
                            schema,
                            ml_models
                            )



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL
    ],
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
app.include_router(upload_baseline.router)
app.include_router(schema.router)
app.include_router(tenant.router)
app.include_router(agent_trace.router)  # WS /ws/agent-trace/{run_id}
app.include_router(slack.router)


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
