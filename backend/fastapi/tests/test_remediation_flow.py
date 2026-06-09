import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models import (  # noqa: E402
    Baseline,
    Incident,
    MLModel,
    PipelineRun,
    RemediationActionLog,
    RemediationRun,
    Tenant,
)
from app.models.base import Base  # noqa: E402
from app.api.routes.remediation import (  # noqa: E402
    approve_retraining_for_incident,
    promote_remediation_candidate,
    reject_remediation_run,
)
from app.services.remediation import decide_remediation  # noqa: E402
from app.services.remediation.retraining_service import run_retraining  # noqa: E402
from app.tasks.remediation_tasks import run_remediation_task  # noqa: E402


class RemediationFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.Session()
        self.tmpdir = tempfile.TemporaryDirectory()

        self.tenant = Tenant(id="tenant-test", name="Test Tenant", schema_name="tenant_test")
        self.db.add(self.tenant)
        self.db.commit()

        self.admin_user = SimpleNamespace(
            email="admin@example.com",
            role="admin",
            tenant_id=self.tenant.id,
        )

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.tmpdir.cleanup()

    def test_approve_queues_remediation_and_updates_report(self):
        incident, _, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])

        queued_calls: list[tuple[int, str, str]] = []

        with patch(
            "app.api.routes.remediation.run_remediation_task.delay",
            side_effect=lambda run_id, tenant_id, target: queued_calls.append(
                (run_id, tenant_id, target)
            ),
        ):
            response = approve_retraining_for_incident(
                incident_id=incident.id,
                target_column="label",
                db=self.db,
                current_user=self.admin_user,
            )

        remediation_run = self.db.query(RemediationRun).one()
        action_log = self.db.query(RemediationActionLog).one()
        refreshed_incident = self.db.query(Incident).filter(Incident.id == incident.id).one()
        payload = json.loads(refreshed_incident.description)

        self.assertEqual(response["status"], "queued")
        self.assertEqual(remediation_run.status, "queued")
        self.assertEqual(action_log.step_name, "approval")
        self.assertEqual(action_log.payload["target_column"], "label")
        self.assertEqual(payload["final_report"]["report_status"], "queued_for_execution")
        self.assertEqual(payload["remediation"]["last_status"], "queued")
        self.assertEqual(queued_calls, [(remediation_run.id, self.tenant.id, "label")])

    def test_approve_uses_baseline_feature_fallback_when_model_features_missing(self):
        incident, _, _ = self._seed_incident(expected_features=None)

        with patch("app.api.routes.remediation.run_remediation_task.delay", return_value=None):
            response = approve_retraining_for_incident(
                incident_id=incident.id,
                target_column="label",
                db=self.db,
                current_user=self.admin_user,
            )

        remediation_run = self.db.query(RemediationRun).one()
        self.assertEqual(response["status"], "queued")
        self.assertEqual(remediation_run.status, "queued")

    def test_approve_blocks_identifier_like_target(self):
        incident, _, _ = self._seed_incident(
            expected_features=["feature_a", "feature_b"],
            dataframe=self._build_training_frame(include_unique_identifier_target=True),
        )

        with self.assertRaisesRegex(Exception, "exceeds the remediation classification limit"):
            approve_retraining_for_incident(
                incident_id=incident.id,
                target_column="target_id",
                db=self.db,
                current_user=self.admin_user,
            )

    def test_source_data_failure_policy_requires_manual_correction_before_retraining(self):
        policy = decide_remediation(
            {
                "severity": "high",
                "failure_types": ["DATA_DRIFT", "SCHEMA_MISMATCH", "RANGE_VIOLATION"],
            }
        )

        self.assertEqual(policy["action_type"], "manual_data_correction")
        self.assertFalse(policy["requires_approval"])
        self.assertFalse(policy["allowed_to_execute"])
        self.assertTrue(policy["manual_only"])

    def test_approve_blocks_source_data_failure_incident(self):
        incident, _, _ = self._seed_incident(
            expected_features=["feature_a", "feature_b"],
            failure_types=["DATA_DRIFT", "SCHEMA_MISMATCH", "DATA_QUALITY"],
        )

        with self.assertRaisesRegex(Exception, "malformed data is blocked"):
            approve_retraining_for_incident(
                incident_id=incident.id,
                target_column="label",
                db=self.db,
                current_user=self.admin_user,
            )

    def test_reject_queued_run_marks_run_rejected(self):
        incident, _, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        remediation_run = self._create_remediation_run(incident.id, incident.run_id, status="queued")

        response = reject_remediation_run(
            remediation_run_id=remediation_run.id,
            db=self.db,
            current_user=self.admin_user,
        )

        refreshed_run = self.db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
        payload = json.loads(self.db.query(Incident).filter(Incident.id == incident.id).one().description)

        self.assertEqual(response["status"], "rejected")
        self.assertEqual(refreshed_run.status, "rejected")
        self.assertIsNotNone(refreshed_run.finished_at)
        self.assertEqual(payload["final_report"]["report_status"], "remediation_rejected")

    def test_reject_running_run_requests_cancellation(self):
        incident, _, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        remediation_run = self._create_remediation_run(incident.id, incident.run_id, status="running")

        response = reject_remediation_run(
            remediation_run_id=remediation_run.id,
            db=self.db,
            current_user=self.admin_user,
        )

        refreshed_run = self.db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
        payload = json.loads(self.db.query(Incident).filter(Incident.id == incident.id).one().description)

        self.assertEqual(response["status"], "cancel_requested")
        self.assertEqual(refreshed_run.status, "cancel_requested")
        self.assertIsNone(refreshed_run.finished_at)
        self.assertEqual(payload["final_report"]["report_status"], "remediation_cancel_requested")

    def test_task_completion_keeps_live_model_metadata_and_updates_candidate_report(self):
        incident, model, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        model.mlflow_run_id = "live-run-123"
        self.db.commit()
        remediation_run = self._create_remediation_run(incident.id, incident.run_id, status="queued")

        candidate_result = {
            "task_type": "classification",
            "feature_columns": ["feature_a", "feature_b"],
            "feature_source": "model",
            "target_column": "label",
            "row_count": 30,
            "target_null_ratio": 0.0,
            "class_distribution": {"yes": 15, "no": 15},
            "metrics": {"accuracy": 0.91},
            "artifact_path": "mlartifacts/remediation/candidate.pkl",
            "candidate_mlflow_run_id": "candidate-run-456",
            "candidate_model_uri": "runs:/candidate-run-456/candidate_model",
            "source_model_name": model.name,
            "source_model_version": model.version,
        }

        with patch("app.tasks.remediation_tasks.SessionLocal", side_effect=lambda: self.Session()), patch(
            "app.tasks.remediation_tasks.set_schema", return_value=None
        ), patch(
            "app.services.remediation.retraining_service.run_retraining",
            return_value=candidate_result,
        ):
            run_remediation_task.run(remediation_run.id, self.tenant.id, "label")

        verification_db = self.Session()
        try:
            refreshed_run = verification_db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
            refreshed_model = verification_db.query(MLModel).filter(MLModel.id == model.id).one()
            payload = json.loads(
                verification_db.query(Incident).filter(Incident.id == incident.id).one().description
            )

            self.assertEqual(refreshed_run.status, "pending_promotion")
            self.assertEqual(refreshed_model.mlflow_run_id, "live-run-123")
            self.assertEqual(payload["final_report"]["report_status"], "candidate_ready_for_review")
            self.assertEqual(
                payload["remediation"]["candidate_mlflow_run_id"],
                "candidate-run-456",
            )
            self.assertTrue(payload["remediation"]["candidate_pending_promotion"])
        finally:
            verification_db.close()

    def test_task_failure_marks_run_failed_and_updates_report(self):
        incident, _, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        remediation_run = self._create_remediation_run(incident.id, incident.run_id, status="queued")

        with patch("app.tasks.remediation_tasks.SessionLocal", side_effect=lambda: self.Session()), patch(
            "app.tasks.remediation_tasks.set_schema", return_value=None
        ), patch(
            "app.services.remediation.retraining_service.run_retraining",
            side_effect=ValueError("synthetic retraining failure"),
        ):
            with self.assertRaisesRegex(ValueError, "synthetic retraining failure"):
                run_remediation_task.run(remediation_run.id, self.tenant.id, "label")

        verification_db = self.Session()
        try:
            refreshed_run = verification_db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
            payload = json.loads(
                verification_db.query(Incident).filter(Incident.id == incident.id).one().description
            )

            self.assertEqual(refreshed_run.status, "failed")
            self.assertEqual(payload["final_report"]["report_status"], "remediation_failed")
        finally:
            verification_db.close()

    def test_reject_pending_candidate_marks_review_rejected(self):
        incident, _, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        remediation_run = self._create_remediation_run(
            incident.id,
            incident.run_id,
            status="pending_promotion",
        )
        self.db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="retraining",
                status="pending_promotion",
                message="Candidate ready.",
                payload={
                    "candidate_mlflow_run_id": "candidate-run-222",
                    "candidate_model_uri": "runs:/candidate-run-222/candidate_model",
                    "metrics": {"accuracy": 0.88},
                },
            )
        )
        self.db.commit()

        response = reject_remediation_run(
            remediation_run_id=remediation_run.id,
            review_notes="Metrics are not strong enough.",
            db=self.db,
            current_user=self.admin_user,
        )

        refreshed_run = self.db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
        payload = json.loads(self.db.query(Incident).filter(Incident.id == incident.id).one().description)

        self.assertEqual(response["status"], "promotion_rejected")
        self.assertEqual(refreshed_run.status, "promotion_rejected")
        self.assertEqual(payload["final_report"]["report_status"], "candidate_rejected")

    def test_stage_candidate_keeps_live_model_metadata_and_report(self):
        incident, model, _ = self._seed_incident(expected_features=["feature_a", "feature_b"])
        model.mlflow_alias = "champion"
        self.db.commit()
        remediation_run = self._create_remediation_run(
            incident.id,
            incident.run_id,
            status="pending_promotion",
        )
        self.db.add(
            RemediationActionLog(
                remediation_run_id=remediation_run.id,
                step_name="retraining",
                status="pending_promotion",
                message="Candidate ready.",
                payload={
                    "candidate_mlflow_run_id": "candidate-run-333",
                    "candidate_model_uri": "runs:/candidate-run-333/candidate_model",
                    "metrics": {"accuracy": 0.93},
                    "feature_columns": ["feature_a", "feature_b"],
                    "feature_source": "model",
                },
            )
        )
        self.db.commit()

        class DummyMlflowClient:
            def __init__(self, tracking_uri=None):
                self.tracking_uri = tracking_uri
                self.alias_calls = []
                self.version_calls = []

            def get_registered_model(self, name):
                return SimpleNamespace(name=name)

            def create_model_version(self, name, source, run_id):
                self.version_calls.append((name, source, run_id))
                return SimpleNamespace(version="7")

            def set_registered_model_alias(self, name, alias, version):
                self.alias_calls.append((name, alias, version))

        with patch(
            "app.services.remediation.promotion_service.MlflowClient",
            DummyMlflowClient,
        ), patch(
            "app.services.remediation.promotion_service.clear_mlflow_model_cache",
            return_value=None,
        ):
            response = promote_remediation_candidate(
                remediation_run_id=remediation_run.id,
                review_notes="Candidate looks good.",
                db=self.db,
                current_user=self.admin_user,
            )

        refreshed_run = self.db.query(RemediationRun).filter(RemediationRun.id == remediation_run.id).one()
        refreshed_model = self.db.query(MLModel).filter(MLModel.id == model.id).one()
        payload = json.loads(self.db.query(Incident).filter(Incident.id == incident.id).one().description)

        self.assertEqual(response["status"], "staged")
        self.assertEqual(refreshed_run.status, "staged")
        self.assertNotEqual(refreshed_model.mlflow_run_id, "candidate-run-333")
        self.assertEqual(refreshed_model.version, model.version)
        self.assertEqual(payload["final_report"]["report_status"], "candidate_staged_for_deployment")
        self.assertEqual(payload["remediation"]["staged_model_version"], "7")

    def test_run_retraining_reuses_original_sklearn_estimator_family(self):
        _, model, run = self._seed_incident(expected_features=["feature_a", "feature_b"])
        captured = {}

        class DummyRunContext:
            def __enter__(self):
                return SimpleNamespace(info=SimpleNamespace(run_id="candidate-run-789"))

            def __exit__(self, exc_type, exc, tb):
                return False

        def capture_logged_model(*, sk_model, **kwargs):
            captured["class_name"] = sk_model.__class__.__name__
            captured["max_depth"] = sk_model.get_params().get("max_depth")

        with patch(
            "app.services.remediation.retraining_service.mlflow.sklearn.load_model",
            return_value=DecisionTreeClassifier(max_depth=3, random_state=7),
        ), patch(
            "app.services.remediation.retraining_service.mlflow.start_run",
            return_value=DummyRunContext(),
        ), patch(
            "app.services.remediation.retraining_service.mlflow.sklearn.log_model",
            side_effect=capture_logged_model,
        ), patch(
            "app.services.remediation.retraining_service.mlflow.set_tags",
            return_value=None,
        ), patch(
            "app.services.remediation.retraining_service.mlflow.log_params",
            return_value=None,
        ), patch(
            "app.services.remediation.retraining_service.mlflow.log_metrics",
            return_value=None,
        ), patch(
            "app.services.remediation.retraining_service.infer_signature",
            return_value=None,
        ):
            result = run_retraining(
                db=self.db,
                run_id=run.id,
                model_id=model.id,
                target_column="label",
            )

        self.assertEqual(result["estimator_class"], "DecisionTreeClassifier")
        self.assertEqual(captured["class_name"], "DecisionTreeClassifier")
        self.assertEqual(captured["max_depth"], 3)

    def test_run_retraining_blocks_task_type_mismatch_against_original_model(self):
        _, model, run = self._seed_incident(expected_features=["feature_a", "feature_b"])

        with patch(
            "app.services.remediation.retraining_service.mlflow.sklearn.load_model",
            return_value=DecisionTreeRegressor(max_depth=3, random_state=7),
        ):
            with self.assertRaisesRegex(ValueError, "original model is not a classifier"):
                run_retraining(
                    db=self.db,
                    run_id=run.id,
                    model_id=model.id,
                    target_column="label",
                )

    def _seed_incident(self, expected_features, dataframe=None, failure_types=None):
        model = MLModel(
            tenant_id=self.tenant.id,
            name="Test Model",
            version="1",
            framework="sklearn",
            mlflow_model_name="test-model",
            mlflow_run_id="live-run-001",
            expected_features=expected_features,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        baseline = Baseline(
            model_id=model.id,
            version=1,
            schema={"feature_a": "float", "feature_b": "float", "label": "string"},
            profile={
                "feature_a": {"type": "numeric", "validation_mode": "range"},
                "feature_b": {"type": "numeric", "validation_mode": "range"},
                "label": {"type": "categorical", "validation_mode": "enum"},
            },
            is_active=True,
        )
        self.db.add(baseline)
        self.db.commit()

        csv_path = Path(self.tmpdir.name) / f"cleaned_{model.id}.csv"
        frame = dataframe if dataframe is not None else self._build_training_frame()
        frame.to_csv(csv_path, index=False)

        run = PipelineRun(
            model_id=model.id,
            baseline_version=baseline.version,
            file_path=str(csv_path),
            cleaned_data_path=str(csv_path),
            status="success",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        incident = Incident(
            run_id=run.id,
            title="AI Root Cause Analysis",
            description=json.dumps(
                {
                    "failure_types": failure_types or ["DATA_DRIFT"],
                    "severity": "high",
                    "remediation": {
                        "recommended_action": "Prepare a controlled retraining run and require admin approval before execution.",
                        "action_type": "retrain_model",
                        "action_mode": "approval_required",
                        "requires_approval": True,
                        "allowed_to_execute": True,
                        "manual_only": False,
                        "reason": "The failure pattern suggests population or concept change that may require model refresh.",
                    },
                    "final_report": {
                        "report_status": "awaiting_approval",
                        "action_taken": "Remediation was prepared but is waiting for human approval.",
                        "manual_action_required": True,
                    },
                }
            ),
            failure_type="ai_root_cause",
            finding_type="root_cause",
            finding_id=None,
            severity="high",
            status="open",
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        return incident, model, run

    def _create_remediation_run(self, incident_id, run_id, status):
        remediation_run = RemediationRun(
            incident_id=incident_id,
            run_id=run_id,
            tenant_id=self.tenant.id,
            action_type="retrain_model",
            status=status,
            trigger_mode="manual_approval",
            created_by=self.admin_user.email,
        )
        self.db.add(remediation_run)
        self.db.commit()
        self.db.refresh(remediation_run)
        return remediation_run

    @staticmethod
    def _build_training_frame(include_unique_identifier_target=False):
        rows = 30
        frame = pd.DataFrame(
            {
                "feature_a": [float(index) for index in range(rows)],
                "feature_b": [float(index % 5) for index in range(rows)],
                "label": ["yes" if index % 2 == 0 else "no" for index in range(rows)],
            }
        )
        if include_unique_identifier_target:
            frame["target_id"] = [f"ID-{index:03d}" for index in range(rows)]
        return frame


if __name__ == "__main__":
    unittest.main()
