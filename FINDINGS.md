# QuantEdge experiment findings

## Original benchmark snapshot

The original main-branch benchmark ran 50 sessions (seeds 100–149), with 1,200 RFQ opportunities per session and balanced random customer direction.

| Strategy | Mean PnL | Positive sessions | Mean fills | Mean absolute ending position | Mean max drawdown |
|---|---:|---:|---:|---:|---:|
| Unmanaged fixed spread | 85.87 | 64% | 590.9 | 35.76 | 270.18 |
| Managed fixed-spread control | 75.89 | 94% | 552.3 | 5.02 | 36.53 |
| QuantEdge | 45.36 | 100% | 265.6 | 0.96 | 8.39 |

QuantEdge is more conservative in this snapshot but has lower mean PnL and fewer fills than the managed fixed-spread control. This is a risk/activity trade-off, not a superiority claim. QuantEdge did not hedge in these sessions.

## Research-v2 changes

- Adds independent random streams for the price path, RFQ flow, and competitor quote. The market/RFQ tape therefore does not change just because a strategy declines an order or follows a different branch.
- Adds balanced, one-sided stress, and momentum-associated customer-flow modes.
- Adds an alternate, less conservative adaptive quoting configuration for investigation.
- Reports PnL dispersion, an approximate 95% confidence interval for mean PnL, drawdown from running peak, maximum loss from session start, inventory, fills, hedges, and fees.
- Expands unit tests for reproducibility and simulator scenarios.

## What this still does not establish

The new flow modes are stylized test scenarios, not empirically calibrated customer flow. Prices remain exogenous; market impact, true queue position, informed customer limits, and partial fills are not modeled. The approximate interval only reflects variation across simulated seeds, not model uncertainty. Do not interpret output as evidence of live trading profitability.

## Reproduction

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
```

## Next experiment

Tune parameters only on training seeds, select one configuration, then report results on untouched holdout seeds. Inspect both PnL and risk metrics across all flow modes. Before making performance claims, calibrate fill behavior and post-fill markouts against actual or defensibly sourced market data.
