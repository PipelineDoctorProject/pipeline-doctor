# Current Sprint: Data Quality

This workstream covers the move from demo-style cleaning to a production-style quality gate.

---

## Delivered

- raw validation still records findings for observability and RCA
- cleaning now masks or repairs invalid values where safe
- heavily corrupted rows are quarantined
- post-clean validation runs on the accepted dataset
- prediction and drift only run when the cleaned dataset passes the gate
- failed batches still queue RCA so blocked runs remain explainable

---

## Runtime Behavior

### Accepted output

- accepted rows are written to `cleaned/{run_id}.csv`
- the run stores that file in `cleaned_data_path`

### Quarantine output

- removed rows are written to `cleaned/quarantine/{run_id}.csv`

### Gate behavior

The run is blocked when:

- required baseline columns are missing
- the accepted row count is too low
- the accepted row ratio is too low
- post-clean schema errors remain
- post-clean validation checks still fail

---

## Verified This Sprint

The corrupted tracks batch was checked against the real tracks baseline:

- `53` rows entered
- `49` rows were accepted
- `4` rows were quarantined
- raw validation failed as expected
- post-clean validation passed
- the quality gate returned `success`

The missing-column scenario was also checked:

- removing required column `tempo` still results in a blocked run
- the quality gate returns `failed`
- drift and predictions do not continue

---

## Production Value

This is the big behavior change:

- before: bad batches could still end up marked successful after only light normalization
- now: only the accepted cleaned dataset is allowed into prediction and drift

---

## Related Docs

- [data_quality.md](./data_quality.md)
- [drift_detection.md](./drift_detection.md)
