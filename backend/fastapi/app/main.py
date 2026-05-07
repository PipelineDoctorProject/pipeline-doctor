from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes import (
    health,
    runs,
    incidents,
    predictions,
    drift_findings,
    data_quality_findings,
    auth,
    onboarding,
    invite
)

from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI()

# Routers
app.include_router(health.router)
app.include_router(runs.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(data_quality_findings.router)
app.include_router(drift_findings.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(invite.router)

# Middleware
app.add_middleware(AuthMiddleware)


# ==========================================
# ADD AUTHORIZE BUTTON TO SWAGGER
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

    # JWT Bearer Config
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Apply globally
    openapi_schema["security"] = [
        {"BearerAuth": []}
    ]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi