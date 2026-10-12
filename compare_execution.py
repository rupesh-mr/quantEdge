"""Compare legacy and stochastic execution benchmarks from simulator.py outputs."""
import argparse
import json
import math
import statistics
from pathlib import Path


def mean_ci(values):
    if not values:
        return None, None, None
    mean = statistics.mean(values)
    if len(values) < 2:
        return mean, None, None
    half = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def compare_file(legacy_path, stochastic_path):
    legacy = json.loads(Path(legacy_path).read_text())
    stochastic = json.loads(Path(stochastic_path).read_text())
    flow = legacy["experiment"]["flow_mode"]
    if stochastic["experiment"]["flow_mode"] != flow:
        raise ValueError(f"Flow mismatch: {flow} vs {stochastic['experiment']['flow_mode']}")
    results = {"flow_mode": flow, "strategies": {}}
    for strategy, old in legacy["strategies"].items():
        new = stochastic["strategies"][strategy]
        old_pnl = old.get("pnl_by_seed", {})
        new_pnl = new.get("pnl_by_seed", {})
        common = sorted(set(old_pnl) & set(new_pnl), key=int)
        paired = [new_pnl[s] - old_pnl[s] for s in common]
        delta, low, high = mean_ci(paired)
        results["strategies"][strategy] = {
            "legacy_mean_pnl": old["mean_pnl"],
            "stochastic_mean_pnl": new["mean_pnl"],
            "mean_pnl_delta_stochastic_minus_legacy": round(new["mean_pnl"] - old["mean_pnl"], 4),
            "paired_pnl_delta_mean": round(delta, 4) if delta is not None else None,
            "paired_pnl_delta_ci95_approx": [round(low, 4), round(high, 4)] if low is not None else None,
            "paired_sessions": len(common),
            "legacy_mean_fills": old.get("mean_fills"),
            "stochastic_mean_fills": new.get("mean_fills"),
            "stochastic_mean_partial_fills": new.get("mean_partial_fills"),
            "stochastic_mean_filled_quantity": new.get("mean_filled_quantity"),
            "legacy_mean_drawdown": old.get("mean_max_drawdown_from_peak"),
            "stochastic_mean_drawdown": new.get("mean_max_drawdown_from_peak"),
            "stochastic_mean_markout_1_step_bps": new.get("mean_markout_1_step_bps"),
            "stochastic_mean_markout_5_step_bps": new.get("mean_markout_5_step_bps"),
        }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="benchmark_output")
    args = parser.parse_args()
    root = Path(args.directory)
    report = {
        "note": (
            "Synthetic model sensitivity analysis, not live-market evidence. "
            "Paired intervals measure seed variation only and do not account for model misspecification."
        ),
        "flows": {},
    }
    for flow in ("balanced", "one_sided", "informed"):
        report["flows"][flow] = compare_file(
            root / f"{flow}.json", root / f"stochastic_{flow}.json"
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
