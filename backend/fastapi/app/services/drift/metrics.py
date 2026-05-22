import numpy as np
from scipy.stats import ks_2samp


def calculate_psi(reference_values, current_values, bins=10):
    reference_values = np.asarray(reference_values)
    current_values = np.asarray(current_values)

    reference_values = reference_values[~np.isnan(reference_values)]
    current_values = current_values[~np.isnan(current_values)]

    breakpoints = np.percentile(reference_values, np.linspace(0, 100, bins + 1))
    breakpoints = np.unique(breakpoints)

    if len(breakpoints) < 2:
        return 0.0

    ref_counts, _ = np.histogram(reference_values, bins=breakpoints)
    cur_counts, _ = np.histogram(current_values, bins=breakpoints)

    ref_pct = ref_counts / max(len(reference_values), 1)
    cur_pct = cur_counts / max(len(current_values), 1)

    ref_pct = np.where(ref_pct == 0, 0.0001, ref_pct)
    cur_pct = np.where(cur_pct == 0, 0.0001, cur_pct)

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def calculate_ks(reference_values, current_values):
    reference_values = np.asarray(reference_values)
    current_values = np.asarray(current_values)

    reference_values = reference_values[~np.isnan(reference_values)]
    current_values = current_values[~np.isnan(current_values)]

    if len(reference_values) == 0 or len(current_values) == 0:
        return 0.0, 1.0

    result = ks_2samp(reference_values, current_values)
    return float(result.statistic), float(result.pvalue)