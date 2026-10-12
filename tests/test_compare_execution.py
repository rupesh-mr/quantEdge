import json
import tempfile
import unittest
from pathlib import Path

from compare_execution import compare_file


class ExecutionComparisonTests(unittest.TestCase):
    def _write_result(self, path, flow, execution_model, pnl_by_seed):
        payload = {
            "experiment": {"flow_mode": flow},
            "strategies": {
                "quantedge": {
                    "mean_pnl": sum(pnl_by_seed.values()) / len(pnl_by_seed),
                    "pnl_by_seed": {str(k): v for k, v in pnl_by_seed.items()},
                    "mean_fills": 10.0,
                    "mean_partial_fills": 2.0 if execution_model == "stochastic" else 0.0,
                    "mean_filled_quantity": 12.0,
                    "mean_max_drawdown_from_peak": 3.0,
                    "mean_markout_1_step_bps": 0.1 if execution_model == "stochastic" else None,
                    "mean_markout_5_step_bps": 0.2 if execution_model == "stochastic" else None,
                }
            },
            "execution_model": execution_model,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_paired_delta_uses_common_seed_values(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "legacy.json"
            stochastic = Path(directory) / "stochastic.json"
            self._write_result(legacy, "balanced", "legacy", {1: 10.0, 2: 20.0})
            self._write_result(stochastic, "balanced", "stochastic", {1: 12.0, 2: 19.0, 3: 100.0})
            result = compare_file(legacy, stochastic)
            strategy = result["strategies"]["quantedge"]
            self.assertEqual(strategy["paired_sessions"], 2)
            self.assertAlmostEqual(strategy["paired_pnl_delta_mean"], 0.5)
            self.assertEqual(strategy["stochastic_mean_partial_fills"], 2.0)

    def test_flow_mismatch_fails_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "legacy.json"
            stochastic = Path(directory) / "stochastic.json"
            self._write_result(legacy, "balanced", "legacy", {1: 10.0})
            self._write_result(stochastic, "informed", "stochastic", {1: 12.0})
            with self.assertRaisesRegex(ValueError, "Flow mismatch"):
                compare_file(legacy, stochastic)


if __name__ == "__main__":
    unittest.main()
