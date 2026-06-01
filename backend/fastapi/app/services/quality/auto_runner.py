import os
import shutil

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


INCOMING_DIR = "uploads/incoming"
PROCESSED_DIR = "uploads/processed"
FAILED_DIR = "uploads/failed"


def process_incoming_files(model_id: int):
    from app.services.quality.pipeline import run_data_quality_pipeline

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(FAILED_DIR, exist_ok=True)

    files = [
        f for f in os.listdir(INCOMING_DIR)
        if f.endswith(".csv")
    ]

    if not files:
        print("No incoming files found")
        return

    db: Session = SessionLocal()

    try:

        for filename in files:

            file_path = os.path.join(INCOMING_DIR, filename)

            print(f"\nProcessing: {filename}")

            try:

                result = run_data_quality_pipeline(
                    db=db,
                    model_id=model_id,
                    file_path=file_path
                )

                print("SUCCESS")
                print(result)

                # move to processed
                shutil.move(
                    file_path,
                    os.path.join(PROCESSED_DIR, filename)
                )

            except Exception as e:

                print(f"FAILED: {str(e)}")

                # move to failed
                shutil.move(
                    file_path,
                    os.path.join(FAILED_DIR, filename)
                )

    finally:
        db.close()
