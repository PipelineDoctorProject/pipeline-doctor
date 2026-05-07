from fastapi import FastAPI
from app.api.routes import health, runs,incidents, predictions, drift_findings, data_quality_findings,auth
from app.middleware.auth_middleware import AuthMiddleware

app = FastAPI()

app.include_router(health.router)
app.include_router(runs.router)
app.include_router(incidents.router)
app.include_router(predictions.router)
app.include_router(drift_findings.router)
app.include_router(data_quality_findings.router)
app.include_router(auth.router)
app.add_middleware(AuthMiddleware)