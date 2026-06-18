import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai_orchestration.parser import parse_root_cause_response, classify_failure_types


class ParserTests(unittest.TestCase):
    def test_classify_failure_types_ignores_json_keys(self):
        text = """
        No issues detected in pipeline run 21.
        ```json
        {
          "failure_types": [],
          "severity": "low",
          "summary": "No issues detected in pipeline run 21",
          "recommendation": "Continue monitoring pipeline runs for potential issues"
        }
        ```
        """
        res = parse_root_cause_response(text)
        self.assertEqual(res["failure_types"], [])
        self.assertEqual(res["severity"], "low")

    def test_classify_failure_types_matches_actual_keywords(self):
        text = "This batch has range violations and data drift issues."
        res = parse_root_cause_response(text)
        self.assertIn("DATA_DRIFT", res["failure_types"])
        self.assertIn("RANGE_VIOLATION", res["failure_types"])


if __name__ == "__main__":
    unittest.main()
