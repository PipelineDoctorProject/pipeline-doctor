from backend.fastapi.app.api.routes import health
from fastapi import FastAPI
from backend.fastapi.app.api.routes import runs

app = FastAPI()

app.include_router(health.router)
app.include_router(runs.router)