from fastapi import APIRouter, UploadFile, File
import pandas as pd
from app.data_quality.baseline import create_baseline
from app.data_quality.service import save_baseline

router = APIRouter()


@router.post("/baseline/upload")
async def upload_baseline(model_id: str, file: UploadFile = File(...)):

    
    df = pd.read_csv(file.file)

    # 2. Create baseline
    baseline = create_baseline(df)

    # 3. Store baseline
    save_baseline(model_id, baseline)

    return {
        "message": "Baseline uploaded successfully",
        "columns": list(df.columns)
    }