"""Synthetic RFQ simulator for comparing inventory-aware market-making policies.

All market mechanics are stylized assumptions. Results are for research and debugging,
not evidence of live-market profitability.
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
                flow_mode="balanced", config=None):
    """Run one synthetic session with common random numbers across strategies."""
    rng = random.Random(seed)
    dealer = None if strategy == "unmanaged_fixed" else make_dealer(strategy, config)
    cash = position = fills = hedges = 0
    notional = fees = 0.0
    equity_peak = 0.0
    max_drawdown = max_loss_from_start = 0.0
    max_abs_position = 0
    price = previous = 100.0
    recent_abs_returns = []
    flow_direction = 0

    for t in range(n_steps):
        # Three alternating volatility regimes.
        sigma = 0.0015 if (t // 180) % 3 else 0.0035
        price *= math.exp(rng.gauss(0.00002, sigma))
        abs_ret_bps = abs((price / previous - 1) * 10000)
        recent_abs_returns.append(abs_ret_bps)
        vol_bps = statistics.mean(recent_abs_returns[-20:])
        previous = price

        # Customer-flow regimes allow explicit stress testing. In informed mode,
        # customers disproportionately trade in the direction of recent momentum.
        if t % 90 == 0:
            flow_direction = rng.choice([-1, 1])
        if flow_mode == "balanced":
            buy_probability = 0.5
        elif flow_mode == "one_sided":
            buy_probability = 0.8 if (t // 120) % 2 == 0 else 0.2
        elif flow_mode == "informed":
            recent_move = price / max(1e-12, price / math.exp(rng.gauss(0.0, sigma))) - 1
            buy_probability = 0.65 if recent_move >= 0 else 0.35
        else:
            raise ValueError(f"Unknown flow mode: {flow_mode}")
        side = "BUY" if rng.random() < buy_probability else "SELL"
        qty = rng.choice([1, 1, 1, 2, 3])
        customer_limit_bps = rng.uniform(2, 38)

        if strategy == "unmanaged_fixed":
            edge = 8.0
            quote = price * (1 + edge / 10000) if side == "BUY" else price * (1 - edge / 10000)
        else:
            quote = dealer.quote_one(
                {"side": side, "quantity": qty}, price, vol_bps, 0.01, position
            )

        opponent_edge = rng.uniform(1, 18)
        opponent_quote = (price * (1 + opponent_edge / 10000) if side == "BUY"
                          else price * (1 - opponent_edge / 10000))
        eligible = quote is not None and abs(quote / price - 1) * 10000 <= customer_limit_bps
        wins = eligible and (quote <= opponent_quote if side == "BUY" else quote >= opponent_quote)

        if wins:
            fills += 1
            notional += qty * quote
            if side == "BUY":
                cash += qty * quote
                position -= qty
            else:
                cash -= qty * quote
                position += qty

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
        "steps": n_steps, "fills": fills, "fill_rate": fills / n_steps,
        "customer_notional": notional, "ending_position": position,
        "max_abs_position": max_abs_position, "hedges": hedges, "fees": fees,
        "final_pnl": final_pnl, "max_drawdown_from_peak": max_drawdown,
        "max_loss_from_start": max_loss_from_start,
    }


def summarize(strategy, seeds, n_steps, flow_mode="balanced", config=None):
    runs = [run_session(seed=s, n_steps=n_steps, strategy=strategy,
                        flow_mode=flow_mode, config=config) for s in seeds]
    pnls = [r["final_pnl"] for r in runs]
    mean_pnl = statistics.mean(pnls)
    std_pnl = statistics.stdev(pnls) if len(pnls) > 1 else 0.0
    sem = std_pnl / math.sqrt(len(pnls)) if runs else 0.0
    return {
        "strategy": strategy, "flow_mode": flow_mode, "sessions": len(runs),
        "mean_pnl": round(mean_pnl, 4), "median_pnl": round(statistics.median(pnls), 4),
        "pnl_std": round(std_pnl, 4), "mean_pnl_ci95_approx": [
            round(mean_pnl - 1.96 * sem, 4), round(mean_pnl + 1.96 * sem, 4)
        ],
        "positive_sessions_pct": round(100 * sum(x > 0 for x in pnls) / len(pnls), 2),
        "mean_fills": round(statistics.mean(r["fills"] for r in runs), 2),
        "mean_fill_rate": round(statistics.mean(r["fill_rate"] for r in runs), 4),
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
            name: summarize(name, seeds, args.steps, args.flow) for name in strategies
        },
    }
    print(json.dumps(results, indent=2))
