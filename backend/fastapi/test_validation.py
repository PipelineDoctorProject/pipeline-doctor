import pandas as pd
from app.services.quality.baseline import create_baseline
from app.services.quality.validator import run_validation

# STEP 1 — baseline data
df1 = pd.DataFrame({
    "age": [20, 25, 30],
    "salary": [1000, 2000, 3000],
    "city": ["A", "B", "A"]
})

baseline = create_baseline(df1)

# STEP 2 — new data (with issues)
df2 = pd.DataFrame({
    "age": [22, 500, 28],     # anomaly
    "salary": [1500, 2500, 3500],
    "city": ["A", "X", "A"]   # anomaly
})

results = run_validation(df2, baseline)

print(results)