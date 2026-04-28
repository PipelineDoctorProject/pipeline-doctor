from fastapi import APIRouter
from app.schemas.run import RunCreate, RunResponse
from app.services.run_service import create_run, get_runs

router = APIRouter(prefix="/runs", tags=["Runs"])

@router.post("/", response_model=RunResponse)
def create_run_api(data: RunCreate):
    return create_run(data)

@router.get("/", response_model=list[RunResponse])
def list_runs_api():
    return get_runs()