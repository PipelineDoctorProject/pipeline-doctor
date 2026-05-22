from datetime import datetime

runs_db = []
run_id = 1

def create_run(data):
    global run_id

    run = {
        "id": run_id,
        "status": data.status,
        "drift_score": data.drift_score,
        "created_at": datetime.utcnow()
    }

    runs_db.append(run)
    run_id += 1

    return run

def get_runs():
    return runs_db