from fastapi import FastAPI
from app.api.routes import health, runs,incidents

app = FastAPI()

app.include_router(health.router)
app.include_router(runs.router)
app.include_router(incidents.router)