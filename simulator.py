"""Synthetic RFQ simulator; intentionally not the official competition simulator."""
import argparse
import json
import math
import random
import statistics
from dealer_bot import QuantEdgeDealer, StrategyConfig


def make_dealer(strategy):
    if strategy == "quantedge":
        return QuantEdgeDealer()
    if strategy == "fixed_control":
        return QuantEdgeDealer(StrategyConfig(
            base_edge_bps=8.0, volatility_multiplier=0.0,
            inventory_skew_bps_per_lot=0.0,
            excess_inventory_skew_bps_per_lot=0.0
        ))
    return None


def run_session(seed=7, n_steps=1200, strategy="quantedge"):
    rng = random.Random(seed)
    dealer = make_dealer(strategy) if strategy != "unmanaged_fixed" else None
    cash = position = fills = hedges = 0
    notional = fees = 0.0
    peak = max_drawdown = 0.0
    max_abs_position = 0
    price = previous = 100.0
    recent_abs_returns = []

    for t in range(n_steps):
        sigma = 0.0015 if (t // 180) % 3 else 0.0035
        price *= math.exp(rng.gauss(0.00002, sigma))
        abs_ret_bps = abs((price / previous - 1) * 10000)
        recent_abs_returns.append(abs_ret_bps)
        vol_bps = statistics.mean(recent_abs_returns[-20:])
        previous = price

        side = "BUY" if rng.random() < 0.5 else "SELL"
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
        peak = max(peak, pnl)
        max_drawdown = max(max_drawdown, peak - pnl)

    return {
        "seed": seed, "strategy": strategy, "steps": n_steps, "fills": fills,
        "fill_rate": fills / n_steps, "customer_notional": notional,
        "ending_position": position, "max_abs_position": max_abs_position,
        "hedges": hedges, "fees": fees,
        "final_pnl": cash + position * price - fees,
        "max_drawdown": max_drawdown,
    }


def summarize(strategy, seeds, n_steps):
    runs = [run_session(seed=s, n_steps=n_steps, strategy=strategy) for s in seeds]
    pnls = [r["final_pnl"] for r in runs]
    return {
        "strategy": strategy,
        "sessions": len(runs),
        "mean_pnl": round(statistics.mean(pnls), 4),
        "median_pnl": round(statistics.median(pnls), 4),
        "positive_sessions_pct": round(100 * sum(x > 0 for x in pnls) / len(pnls), 2),
        "mean_fills": round(statistics.mean(r["fills"] for r in runs), 2),
        "mean_fill_rate": round(statistics.mean(r["fill_rate"] for r in runs), 4),
        "mean_abs_ending_position": round(statistics.mean(abs(r["ending_position"]) for r in runs), 2),
        "mean_max_abs_position": round(statistics.mean(r["max_abs_position"] for r in runs), 2),
        "mean_hedges": round(statistics.mean(r["hedges"] for r in runs), 2),
        "mean_fees": round(statistics.mean(r["fees"] for r in runs), 4),
        "mean_max_drawdown": round(statistics.mean(r["max_drawdown"] for r in runs), 4),
        "pnl_by_seed": {str(r["seed"]): round(r["final_pnl"], 2) for r in runs},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=50)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=100)
    args = parser.parse_args()
    if args.sessions < 1 or args.steps < 1:
        parser.error("--sessions and --steps must be positive")
    seeds = list(range(args.seed, args.seed + args.sessions))
    results = {
        "experiment": {
            "sessions": args.sessions, "steps_per_session": args.steps,
            "seeds": [seeds[0], seeds[-1]],
            "note": "Synthetic simulator only; not official competition or live-market evidence."
        },
        "unmanaged_fixed": summarize("unmanaged_fixed", seeds, args.steps),
        "fixed_control": summarize("fixed_control", seeds, args.steps),
        "quantedge": summarize("quantedge", seeds, args.steps),
    }
    print(json.dumps(results, indent=2))
