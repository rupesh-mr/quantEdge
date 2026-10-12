# QuantEdge: inventory-aware market-making research

A small, dependency-free Python research project for comparing RFQ quoting policies under stylized synthetic market and customer-flow assumptions. This is a simulator, not a claim of live-market profitability.

## Run

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced --execution-model stochastic
python optimize.py --steps 1200 --train-start 100 --train-sessions 20 --validation-start 500 --validation-sessions 20 --holdout-start 1000 --holdout-sessions 50
```

To compare the two execution models, first save legacy and stochastic simulator JSON outputs using the same seeds, then run:

```bash
python compare_execution.py --directory benchmark_output
```

The directory should contain `balanced.json`, `one_sided.json`, `informed.json` and their `stochastic_*.json` counterparts. The report gives seed-paired PnL changes, approximate confidence intervals, drawdown, partial-fill, and markout diagnostics.

## Model

- Volatility-sensitive quote edge and inventory-skewed reservation price.
- Tick-aligned quoting, hard position limits, and threshold hedging with fees.
- Independent seeded streams for price, RFQ flow, competitor quotes, and execution randomness.
- Balanced, one-sided stress, and momentum-associated customer-flow scenarios.
- Risk outputs include PnL dispersion, approximate confidence intervals, maximum absolute position, peak-to-trough drawdown, and maximum loss from session start.
- Legacy deterministic execution plus an optional stochastic allocation/partial-fill model with 1-step and 5-step post-fill markout diagnostics.
- Train/validation/holdout optimization with paired seed-wise PnL and drawdown comparisons.

The stochastic fill model is an explicit synthetic assumption, not a calibrated exchange execution model.

## Research results

The seeded benchmark and optimization runs are recorded in [FINDINGS.md](FINDINGS.md). In brief, the stochastic execution assumption changes the measured outcomes: QuantEdge's simulated mean PnL rises in all three flow scenarios relative to its legacy-model results, but its drawdown also increases. The adaptive-loose policy loses mean PnL in all three scenarios. These comparisons establish sensitivity to model assumptions, not live-market profitability or a definitive winning strategy.

[View benchmark and optimization artifacts in GitHub Actions](https://github.com/rupesh-mr/quantEdge/actions/runs/38266219837).

## Caveats

Customer-flow modes and competitor quotes are stylized, not calibrated empirical order flow. Prices are exogenous and the model does not represent market impact, true queue priority, venue latency, or calibrated fill probabilities. Markouts are diagnostic mid-price changes, not net trade profitability. Confidence intervals describe variation across simulation seeds only; they do not quantify model uncertainty. Results are not evidence of live-market profitability.

## Files

- `dealer_bot.py`: strategy configuration, quoting, and hedging rules.
- `simulator.py`: synthetic market and customer-flow experiments.
- `optimize.py`: configuration search with separate train, validation, and holdout seeds.
- `compare_execution.py`: paired comparison of legacy and stochastic benchmark outputs.
- `tests/`: strategy, simulator, and execution-comparison unit tests.
- `FINDINGS.md`: benchmark tables, holdout results, execution sensitivity, markouts, and limitations.
