from fastapi import FastAPI
from app.routes import health, runs

app = FastAPI()

app.include_router(health.router)
app.include_router(runs.router)