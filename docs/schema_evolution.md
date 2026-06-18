# Schema Evolution

Schema evolution covers what happens when incoming production data no longer matches the active baseline. This includes missing columns, extra columns, type changes, and newly important string fields.

OpsSight treats schema evolution as a controlled change-management workflow, not just a validation error.

---

## Why Schema Evolution Matters

Models depend on a stable input contract. If that contract changes unexpectedly, the model may:

- fail to load input features
- receive columns in the wrong shape
- silently ignore important new information
- produce unreliable predictions
- create false drift alerts
- require retraining with a new preprocessing pipeline

Schema changes are not always bad. They can be expected business changes. The key is that they must be reviewed and approved before becoming part of the production contract.

---

## Schema Change Types

| Change | Meaning | Typical Risk |
|---|---|---|
| Missing column | A baseline column is absent from the current batch | High if model requires it |
| Extra column | Current batch includes a column not in baseline | Medium until reviewed |
| Type mismatch | Column type changed, such as float to object | High for model features |
| Categorical expansion | New category values appeared | Medium or high depending on field |
| Feature candidate | New field may be useful for future retraining | Requires review and preprocessing |

---

## Current Detection Path

```text
Incoming CSV
    |
Load active baseline
    |
Compare current schema with baseline schema
    |
Create schema_change_events for differences
    |
Show pending schema changes in UI
    |
Admin approves or rejects changes
```

Schema changes are stored separately from normal data quality findings so the team can distinguish:

- data is bad right now
- the production contract may need to evolve

---

## What Happens When a New Column Appears

Example:

```text
New column: mood
Type: object/string
```

OpsSight should not automatically send this column to the model. Instead:

1. The column is detected as an extra schema field.
2. A schema change event is created.
3. The UI shows the change as pending review.
4. Admin decides whether the field is expected.
5. If approved, the baseline schema/profile can include it.
6. If the field is important for retraining, the model feature contract must be updated separately.

---

## Approving a New Column

Approval means:

- the new column is accepted as part of the monitored data contract
- future validations should not treat it as unexpected
- baseline metadata can be updated for that field
- the column may become eligible for future feature engineering review

Approval does not automatically mean:

- the model will use the column immediately
- the column is safe as a raw feature
- the column is deployed to production serving
- the current champion model changes

For string columns, approval should usually create a follow-up feature engineering task.

---

## Rejecting a New Column

Rejection means:

- the column is not accepted into the production schema
- future batches containing it can continue to raise schema-change evidence
- the column should not be used for retraining or model input
- upstream producers should be checked if the column is accidental

Rejecting a column does not delete the raw uploaded file. It only records the decision for monitoring and governance.

---

## String Columns as Features

Raw strings are usually not valid direct model inputs for scikit-learn models.

Example:

```text
mood = "happy"
mood = "sad"
mood = "energetic"
```

The model needs numeric representation:

- one-hot encoding
- ordinal encoding
- hashing
- embeddings
- target encoding
- custom business mapping

OpsSight should not invent this transformation automatically for production. The right production path is:

```text
New string column detected
    |
Admin approves schema field as expected
    |
Data scientist defines preprocessing
    |
Model training pipeline includes transformer
    |
New model candidate is trained and logged
    |
Candidate is staged and deployed through normal lifecycle
```

---

## Baseline vs Model Feature Contract

The baseline schema and model feature list are related but not identical.

### Baseline schema

Answers:

- what columns are expected in the data?
- what types and profiles are normal?
- which values are suspicious?

### Model feature list

Answers:

- what columns does the model actually consume?
- in what order?
- with what preprocessing?

A column can be in the baseline but not in the model. For example:

- `id`
- `name`
- `artist`
- raw text fields
- audit metadata

This is normal.

---

## Production Approval Criteria

Before approving a schema change, verify:

- the column came from an expected upstream release
- the type is stable across sample batches
- null rate is acceptable
- the column does not contain secrets or PII that should not be stored
- high-cardinality fields are not accidentally treated as enums
- the model does not require a preprocessing update before using it
- the baseline update will not hide a real upstream bug

---

## UI Expectations

The Schemas page should support:

- active baseline registry
- pending schema changes
- approve/reject actions
- field-level details
- old type vs new type
- impacted model/run
- reviewer notes
- active baseline activation

If you cannot see pending schema evolution in the UI, verify:

- a DAG run actually produced a schema change
- the schema change event belongs to the current tenant
- the selected model filter is correct
- frontend was hard-refreshed after UI changes
- API routes return schema-change events for the tenant

---

## How Schema Evolution Affects Remediation

If schema changes affect expected model features, remediation should be cautious:

- missing required features can block retraining
- new features should not automatically enter the model
- string features need explicit preprocessing
- baseline-approved columns may be available for future retraining only after feature contract review

For unsupervised clustering, a newly approved numeric feature may be considered for a future candidate. For supervised models, new features should be validated against target leakage and training stability.

---

## Related Code

- `backend/fastapi/app/api/routes/schema.py`
- `backend/fastapi/app/models/schema_change_event.py`
- `backend/fastapi/app/utils/schema_utils.py`
- `frontend/src/pages/schema/Schema.jsx`
- `frontend/src/store/baselineStore.js`
- `backend/fastapi/app/services/quality/validator.py`

---

## Related Docs

- [data_quality.md](./data_quality.md)
- [ml_integration.md](./ml_integration.md)
- [model_lifecycle.md](./model_lifecycle.md)
- [database_schema.md](./database_schema.md)
