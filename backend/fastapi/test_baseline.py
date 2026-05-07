import pandas as pd
from app.services.quality.baseline import create_baseline

# STEP 1: Create sample dataset
df = pd.DataFrame({
    "age": [20, 25, 30],
    "salary": [1000, 2000, 3000],
    "city": ["A", "B", "A"]
})

# STEP 2: Create baseline
baseline = create_baseline(df)

# STEP 3: Print result
print("=== BASELINE ===")
print(baseline)