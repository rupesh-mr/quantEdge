"""Synthetic RFQ simulator for comparing market-making policies.

Market and customer-flow mechanics are stylized assumptions for research, not evidence
of live-market profitability.
"""
import argparse
import json
import math
import random
import statistics
from dealer_bot import QuantEdgeDealer, StrategyConfig


def make_dealer(strategy, config=None):
    if strategy == "quantedge":
        return QuantEdgeDealer(config or StrategyConfig())
    if strategy == "fixed_control":
        return QuantEdgeDealer(config or StrategyConfig(
            base_edge_bps=8.0, volatility_multiplier=0.0,
            inventory_skew_bps_per_lot=0.0,
            excess_inventory_skew_bps_per_lot=0.0,
            inventory_soft_limit=20, inventory_hard_limit=35,
        ))
    if strategy == "adaptive_loose":
        return QuantEdgeDealer(config or StrategyConfig(
            base_edge_bps=4.0, volatility_multiplier=0.12,
            inventory_skew_bps_per_lot=0.8,
            excess_inventory_skew_bps_per_lot=1.5,
            max_quote_edge_bps=45.0,
            inventory_soft_limit=12, inventory_hard_limit=25,
            hedge_threshold=10, hedge_fraction=0.65,
        ))
    raise ValueError(f"Unknown dealer strategy: {strategy}")


def run_session(seed=7, n_steps=1200, strategy="quantedge",
                flow_mode="balanced", config=None, execution_model="legacy"):
    """Run one deterministic synthetic session."""
    # Independent streams prevent strategy-dependent code paths from changing
    # the market tape or RFQ stream consumed by later events.
    price_rng = random.Random(seed)
    flow_rng = random.Random(seed + 1_000_003)
    quote_rng = random.Random(seed + 2_000_033)
    execution_rng = random.Random(seed + 3_000_037)
    if execution_model not in ("legacy", "stochastic"):
        raise ValueError(f"Unknown execution model: {execution_model}")
    dealer = None if strategy == "unmanaged_fixed" else make_dealer(strategy, config)
    cash = position = fills = hedges = partial_fills = filled_quantity = 0
    notional = fees = 0.0
    pending_markouts = []
    markout_1s = []
    markout_5s = []
    equity_peak = 0.0
    max_drawdown = max_loss_from_start = 0.0
    max_abs_position = 0
    price = previous = 100.0
    recent_abs_returns = []
    recent_returns = []

    for t in range(n_steps):
        sigma = 0.0015 if (t // 180) % 3 else 0.0035
        log_return = price_rng.gauss(0.00002, sigma)
        price *= math.exp(log_return)
        # Mark-to-mid outcomes after fills. Positive markout means the dealer's
        # inventory change benefited from the subsequent mid-price move.
        for event in pending_markouts:
            if event["target_1"] == t:
                markout_1s.append(event["signed_side"] * (price / event["fill_price"] - 1) * 10000)
            if event["target_5"] == t:
                markout_5s.append(event["signed_side"] * (price / event["fill_price"] - 1) * 10000)
        pending_markouts = [e for e in pending_markouts if e["target_5"] > t]
        abs_ret_bps = abs(log_return * 10000)
        recent_abs_returns.append(abs_ret_bps)
        recent_returns.append(log_return)
        vol_bps = statistics.mean(recent_abs_returns[-20:])
        momentum = sum(recent_returns[-5:])
        previous = price

        if flow_mode == "balanced":
            buy_probability = 0.5
        elif flow_mode == "one_sided":
            buy_probability = 0.8 if (t // 120) % 2 == 0 else 0.2
        elif flow_mode == "informed":
            # Stylized directional flow correlated with the latest short-term move.
            buy_probability = 0.65 if momentum >= 0 else 0.35
        else:
            raise ValueError(f"Unknown flow mode: {flow_mode}")

        side = "BUY" if flow_rng.random() < buy_probability else "SELL"
        qty = flow_rng.choice([1, 1, 1, 2, 3])
        customer_limit_bps = flow_rng.uniform(2, 38)

        if strategy == "unmanaged_fixed":
            edge = 8.0
            quote = price * (1 + edge / 10000) if side == "BUY" else price * (1 - edge / 10000)
        else:
            quote = dealer.quote_one(
                {"side": side, "quantity": qty}, price, vol_bps, 0.01, position
            )

        opponent_edge = quote_rng.uniform(1, 18)
        opponent_quote = (price * (1 + opponent_edge / 10000) if side == "BUY"
                          else price * (1 - opponent_edge / 10000))
        eligible = quote is not None and abs(quote / price - 1) * 10000 <= customer_limit_bps
        wins = eligible and (quote <= opponent_quote if side == "BUY" else quote >= opponent_quote)
        fill_qty = 0
        if execution_model == "legacy":
            if wins:
                fill_qty = qty
        elif eligible:
            # Smooth stochastic allocation based on relative quote competitiveness.
            # This is an explicit synthetic assumption, not a calibrated venue model.
            dealer_edge = abs(quote / price - 1) * 10000
            competitor_edge = abs(opponent_quote / price - 1) * 10000
            advantage = competitor_edge - dealer_edge
            fill_probability = 1 / (1 + math.exp(-max(-30, min(30, advantage / 4))))
            if execution_rng.random() < fill_probability:
                fill_qty = qty if execution_rng.random() < 0.5 else execution_rng.randint(1, qty)

        if fill_qty > 0:
            fills += 1
            filled_quantity += fill_qty
            if fill_qty < qty:
                partial_fills += 1
            notional += fill_qty * quote
            if side == "BUY":
                cash += fill_qty * quote
                position -= fill_qty
                signed_side = -1
            else:
                cash -= fill_qty * quote
                position += fill_qty
                signed_side = 1
            if execution_model == "stochastic":
                pending_markouts.append({
                    "target_1": t + 1, "target_5": t + 5,
                    "fill_price": price, "signed_side": signed_side,
                })

        if dealer is not None:
            action = dealer.hedge_one("ASSET", position)
            if action:
                hedge_side, hedge_qty = action
                fee = abs(hedge_qty * price) * dealer.config.exchange_fee_bps / 10000
                fees += fee
                hedges += 1
                if hedge_side == "SELL":
                    cash += hedge_qty * price
                    position -= hedge_qty
                else:
                    cash -= hedge_qty * price
                    position += hedge_qty

        max_abs_position = max(max_abs_position, abs(position))
        pnl = cash + position * price - fees
        equity_peak = max(equity_peak, pnl)
        max_drawdown = max(max_drawdown, equity_peak - pnl)
        max_loss_from_start = max(max_loss_from_start, -pnl)

    final_pnl = cash + position * price - fees
    return {
        "seed": seed, "strategy": strategy, "flow_mode": flow_mode,
        "steps": n_steps, "execution_model": execution_model,
        "fills": fills, "fill_rate": fills / n_steps,
        "filled_quantity": filled_quantity, "partial_fills": partial_fills,
        "mean_markout_1_step_bps": statistics.mean(markout_1s) if markout_1s else None,
        "mean_markout_5_step_bps": statistics.mean(markout_5s) if markout_5s else None,
        "markout_1_step_observations": len(markout_1s),
        "markout_5_step_observations": len(markout_5s),
        "customer_notional": notional, "ending_position": position,
        "max_abs_position": max_abs_position, "hedges": hedges, "fees": fees,
        "final_pnl": final_pnl, "max_drawdown_from_peak": max_drawdown,
        "max_loss_from_start": max_loss_from_start,
    }


def summarize(strategy, seeds, n_steps, flow_mode="balanced", config=None,
             execution_model="legacy"):
    runs = [run_session(seed=s, n_steps=n_steps, strategy=strategy,
                        flow_mode=flow_mode, config=config,
                        execution_model=execution_model) for s in seeds]
    pnls = [r["final_pnl"] for r in runs]
    mean_pnl = statistics.mean(pnls)
    std_pnl = statistics.stdev(pnls) if len(pnls) > 1 else 0.0
    sem = std_pnl / math.sqrt(len(pnls)) if runs else 0.0
    return {
        "strategy": strategy, "flow_mode": flow_mode, "sessions": len(runs),
        "execution_model": execution_model,
        "mean_pnl": round(mean_pnl, 4), "median_pnl": round(statistics.median(pnls), 4),
        "pnl_std": round(std_pnl, 4), "mean_pnl_ci95_approx": [
            round(mean_pnl - 1.96 * sem, 4), round(mean_pnl + 1.96 * sem, 4)
        ],
        "positive_sessions_pct": round(100 * sum(x > 0 for x in pnls) / len(pnls), 2),
        "mean_fills": round(statistics.mean(r["fills"] for r in runs), 2),
        "mean_fill_rate": round(statistics.mean(r["fill_rate"] for r in runs), 4),
        "mean_filled_quantity": round(statistics.mean(r["filled_quantity"] for r in runs), 2),
        "mean_partial_fills": round(statistics.mean(r["partial_fills"] for r in runs), 2),
        "mean_markout_1_step_bps": (
            round(statistics.mean(r["mean_markout_1_step_bps"] for r in runs
                                  if r["mean_markout_1_step_bps"] is not None), 4)
            if any(r["mean_markout_1_step_bps"] is not None for r in runs) else None
        ),
        "mean_markout_5_step_bps": (
            round(statistics.mean(r["mean_markout_5_step_bps"] for r in runs
                                  if r["mean_markout_5_step_bps"] is not None), 4)
            if any(r["mean_markout_5_step_bps"] is not None for r in runs) else None
        ),
        "mean_abs_ending_position": round(statistics.mean(abs(r["ending_position"]) for r in runs), 2),
        "mean_max_abs_position": round(statistics.mean(r["max_abs_position"] for r in runs), 2),
        "mean_hedges": round(statistics.mean(r["hedges"] for r in runs), 2),
        "mean_fees": round(statistics.mean(r["fees"] for r in runs), 4),
        "mean_max_drawdown_from_peak": round(statistics.mean(r["max_drawdown_from_peak"] for r in runs), 4),
        "mean_max_loss_from_start": round(statistics.mean(r["max_loss_from_start"] for r in runs), 4),
        "pnl_by_seed": {str(r["seed"]): round(r["final_pnl"], 2) for r in runs},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=50)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--flow", choices=("balanced", "one_sided", "informed"),
                        default="balanced")
    parser.add_argument("--execution-model", choices=("legacy", "stochastic"),
                        default="legacy")
    args = parser.parse_args()
    if args.sessions < 1 or args.steps < 1:
        parser.error("--sessions and --steps must be positive")
    seeds = list(range(args.seed, args.seed + args.sessions))
    strategies = ("unmanaged_fixed", "fixed_control", "quantedge", "adaptive_loose")
    results = {
        "experiment": {
            "sessions": args.sessions, "steps_per_session": args.steps,
            "seeds": [seeds[0], seeds[-1]], "flow_mode": args.flow,
            "note": "Stylized synthetic simulator only; not evidence of live-market performance.",
        },
        "strategies": {
            name: summarize(name, seeds, args.steps, args.flow,
                            execution_model=args.execution_model) for name in strategies
        },
        "execution_model": args.execution_model,
    }
    print(json.dumps(results, indent=2))
