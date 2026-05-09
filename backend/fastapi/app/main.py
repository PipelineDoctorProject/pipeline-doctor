from app.api.routes import data_quality
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes import (
    health,
    runs,
    incidents,
    predictions,
    drift_findings,
    auth,
    onboarding,
    invite,
    upload_baseline
)




from app.api.routes import (health, 
                            runs,
                            incidents,
                              predictions,
                                drift_findings,
                                  auth,upload_baseline,
                                  schema,
                                  )


from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI()


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

app.include_router(schema.router)


app.include_router(onboarding.router)
app.include_router(invite.router)
app.include_router(upload_baseline.router)


# ==========================================
# MIDDLEWARE
# ==========================================
app.add_middleware(AuthMiddleware)


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

    # JWT Auth config
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Apply auth globally
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi