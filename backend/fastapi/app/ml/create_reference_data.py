import numpy as np
import pandas as pd
from pathlib import Path

feature_names = ["feature_1", "feature_2", "feature_3"]

reference_data = pd.DataFrame(
    np.random.normal(0.5, 0.1, (1000, 3)),
    columns=feature_names
)

output_path = Path("app/data/reference_data.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

reference_data.to_csv(output_path, index=False)

print("Reference data created:", output_path)