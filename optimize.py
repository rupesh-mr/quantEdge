"""Grid-search strategy parameters with train/validation/holdout separation.

The selection objective is mean PnL minus risk_aversion * mean peak-to-trough
drawdown, averaged equally across the three synthetic customer-flow scenarios.
Holdout seeds are evaluated only after the configuration is selected.
"""
import argparse
import itertools
import json
import statistics
from dataclasses import asdict

from dealer_bot import StrategyConfig
from simulator import run_session

FLOW_MODES = ("balanced", "one_sided", "informed")


def candidate_configs():
    """A deliberately small, interpretable grid; expand only after inspecting results."""
    grid = itertools.product(
        (3.0, 5.0, 7.0),       # base edge bps
        (0.05, 0.15, 0.25),    # volatility multiplier
        (0.8, 1.5, 2.5),       # inventory skew bps per lot
        (8, 12),               # hedge threshold
    )
    for base, vol, skew, hedge in grid:
        yield StrategyConfig(
            base_edge_bps=base,
            volatility_multiplier=vol,
            inventory_skew_bps_per_lot=skew,
            excess_inventory_skew_bps_per_lot=2.0,
            max_quote_edge_bps=55.0,
            inventory_soft_limit=12,
            inventory_hard_limit=28,
            hedge_threshold=hedge,
            hedge_fraction=0.65,
            exchange_fee_bps=1.0,
        )


def evaluate_config(config, seeds, steps, risk_aversion):
    by_flow = {}
    objectives = []
    for flow in FLOW_MODES:
        runs = [
            run_session(seed=s, n_steps=steps, strategy="quantedge",
                        flow_mode=flow, config=config)
            for s in seeds
        ]
        mean_pnl = statistics.mean(r["final_pnl"] for r in runs)
        mean_dd = statistics.mean(r["max_drawdown_from_peak"] for r in runs)
        objective = mean_pnl - risk_aversion * mean_dd
        objectives.append(objective)
        by_flow[flow] = {
            "mean_pnl": round(mean_pnl, 4),
            "mean_drawdown": round(mean_dd, 4),
            "mean_abs_ending_position": round(
                statistics.mean(abs(r["ending_position"]) for r in runs), 4
            ),
            "mean_fills": round(statistics.mean(r["fills"] for r in runs), 4),
            "objective": round(objective, 4),
        }
    return {
        "config": asdict(config),
        "mean_objective": statistics.mean(objectives),
        "by_flow": by_flow,
    }


def summarize_holdout(strategy, config, seeds, steps):
    result = {}
    for flow in FLOW_MODES:
        runs = [
            run_session(seed=s, n_steps=steps, strategy=strategy,
                        flow_mode=flow, config=config)
            for s in seeds
        ]
        pnls = [r["final_pnl"] for r in runs]
        mean_pnl = statistics.mean(pnls)
        sem = statistics.stdev(pnls) / (len(pnls) ** 0.5) if len(pnls) > 1 else 0.0
        result[flow] = {
            "sessions": len(runs),
            "mean_pnl": round(mean_pnl, 4),
            "median_pnl": round(statistics.median(pnls), 4),
            "mean_pnl_ci95_approx": [
                round(mean_pnl - 1.96 * sem, 4),
                round(mean_pnl + 1.96 * sem, 4),
            ],
            "positive_sessions_pct": round(
                100 * sum(x > 0 for x in pnls) / len(pnls), 2
            ),
            "mean_drawdown": round(
                statistics.mean(r["max_drawdown_from_peak"] for r in runs), 4
            ),
            "mean_abs_ending_position": round(
                statistics.mean(abs(r["ending_position"]) for r in runs), 4
            ),
            "mean_fills": round(statistics.mean(r["fills"] for r in runs), 4),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--train-start", type=int, default=100)
    parser.add_argument("--train-sessions", type=int, default=20)
    parser.add_argument("--validation-start", type=int, default=500)
    parser.add_argument("--validation-sessions", type=int, default=20)
    parser.add_argument("--holdout-start", type=int, default=1000)
    parser.add_argument("--holdout-sessions", type=int, default=50)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--risk-aversion", type=float, default=0.5)
    args = parser.parse_args()
    if min(args.steps, args.train_sessions, args.validation_sessions,
           args.holdout_sessions, args.top_k) < 1:
        parser.error("steps, session counts, and top-k must be positive")
    seed_sets = {
        "train": list(range(args.train_start, args.train_start + args.train_sessions)),
        "validation": list(range(args.validation_start,
                                 args.validation_start + args.validation_sessions)),
        "holdout": list(range(args.holdout_start, args.holdout_start + args.holdout_sessions)),
    }
    all_seeds = [set(v) for v in seed_sets.values()]
    if any(all_seeds[i] & all_seeds[j] for i in range(3) for j in range(i + 1, 3)):
        parser.error("training, validation, and holdout seed ranges must not overlap")

    candidates = list(candidate_configs())
    train_ranked = sorted(
        (evaluate_config(c, seed_sets["train"], args.steps, args.risk_aversion)
         for c in candidates),
        key=lambda x: x["mean_objective"], reverse=True,
    )
    finalists = train_ranked[:min(args.top_k, len(train_ranked))]
    validation_ranked = sorted(
        (evaluate_config(StrategyConfig(**x["config"]), seed_sets["validation"],
                         args.steps, args.risk_aversion) for x in finalists),
        key=lambda x: x["mean_objective"], reverse=True,
    )
    selected = StrategyConfig(**validation_ranked[0]["config"])

    # Holdout is evaluated once after selection; never used for parameter choice.
    holdout = {
        "selected_adaptive": summarize_holdout(
            "quantedge", selected, seed_sets["holdout"], args.steps
        ),
        "fixed_control": summarize_holdout(
            "fixed_control", None, seed_sets["holdout"], args.steps
        ),
        "current_quantedge": summarize_holdout(
            "quantedge", None, seed_sets["holdout"], args.steps
        ),
    }
    print(json.dumps({
        "method": {
            "objective": "mean PnL - risk_aversion * mean peak-to-trough drawdown",
            "risk_aversion": args.risk_aversion,
            "flow_modes_equal_weight": list(FLOW_MODES),
            "candidate_count": len(candidates),
            "train_top_k": len(finalists),
            "seeds": seed_sets,
            "holdout_used_for_selection": False,
            "caveat": "Stylized synthetic model; scores are not live-trading evidence.",
        },
        "training_top_5": train_ranked[:5],
        "validation_ranked_finalists": validation_ranked,
        "selected_config": asdict(selected),
        "holdout_results": holdout,
    }, indent=2))


if __name__ == "__main__":
    main()
