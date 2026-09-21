import json
import tempfile
import unittest
from pathlib import Path

from self_evolving_business import (
    EvolutionError,
    MarketSignal,
    evaluate_experiment,
    propose_experiments,
)


class SelfEvolvingBusinessTests(unittest.TestCase):
    def test_high_value_signal_creates_reviewable_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            signal = MarketSignal("AI workflow interface", "rss", 90, 85, 80, 10)
            paths = propose_experiments([signal], output_dir=root / "artifacts", audit_path=root / "audit.jsonl")
            artifact = json.loads(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(artifact["plan"]["status"], "draft")
            self.assertTrue(artifact["plan"]["human_approval_required"])
            self.assertFalse(artifact["plan"]["direct_publishing"])

    def test_observations_cannot_exceed_mvp_sample_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            signal = MarketSignal("Decentralized app", "rss", 90, 85, 80, 10)
            experiment = propose_experiments([signal], output_dir=root, audit_path=root / "audit.jsonl")[0]
            observations = [{"variant": "control", "success": True}] * 101
            with self.assertRaises(EvolutionError):
                evaluate_experiment(experiment, observations, audit_path=root / "audit.jsonl")

    def test_personal_data_like_signal_is_rejected(self):
        with self.assertRaises(EvolutionError):
            MarketSignal.from_dict(
                {
                    "name": "unsafe",
                    "source": "input",
                    "demand_score": 80,
                    "fit_score": 80,
                    "evidence_score": 80,
                    "risk_score": 10,
                    "description": "collect email addresses",
                }
            )


if __name__ == "__main__":
    unittest.main()
