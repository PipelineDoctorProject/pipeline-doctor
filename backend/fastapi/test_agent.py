import time
import os
import sys

# Add the app directory to the path so we can import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.pipeline_run import PipelineRun
from app.models.tenant import Tenant
from app.tasks.ai_tasks import run_doctor_agent_task

def trigger_test():
    db = SessionLocal()
    try:
        # Get the most recent pipeline run
        latest_run = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).first()
        if not latest_run:
            print("❌ No pipeline runs found in the database. Please run a pipeline first.")
            return

        tenant = db.query(Tenant).first()
        tenant_id = tenant.id if tenant else "default"

        print(f"🎯 Found Pipeline Run ID: {latest_run.id}")
        
        # Reset the analyzed flag so it can be re-analyzed
        latest_run.is_analyzed = False
        db.commit()

        print("\n⏳ GET READY! Follow these steps:")
        print("1. Open http://localhost:5173/incidents in your browser.")
        print("2. You have 10 SECONDS to click 'View details' on the FIRST run in the list.")
        
        for i in range(10, 0, -1):
            print(f"... Triggering AI in {i} seconds (Click View Details now!)")
            time.sleep(1)

        print("\n🚀 TRIGGERING AI AGENT NOW!")
        run_doctor_agent_task.delay(latest_run.id, tenant_id, "doctor")
        
        print("✅ Task sent to Celery! Watch your browser!")

    finally:
        db.close()

if __name__ == "__main__":
    trigger_test()
