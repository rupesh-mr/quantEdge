# QuantEdge experiment findings

## Research-v2 full benchmark

GitHub Actions successfully ran the unit tests, smoke tests, and full benchmark matrix on 12 October 2026. Each scenario uses 50 seeded sessions (seeds 100–149), 1,200 RFQ opportunities per session, and the same independent price/RFQ/competitor random streams across strategies. Full JSON outputs are available as the [workflow artifact](https://github.com/rupesh-mr/quantEdge/actions/runs/38264423562).

### Balanced customer flow

| Strategy | Mean PnL | Positive sessions | Mean fills | Mean abs. ending position | Mean max drawdown |
|---|---:|---:|---:|---:|---:|
| Unmanaged fixed | 73.74 | 74% | 584.56 | 43.58 | 306.26 |
| Fixed control | 66.75 | 98% | 545.28 | 4.90 | 37.73 |
| QuantEdge | 45.01 | 100% | 262.72 | 0.70 | 8.27 |
| Adaptive loose | 63.18 | 98% | 702.42 | 2.50 | 18.16 |

### One-sided customer-flow stress

| Strategy | Mean PnL | Positive sessions | Mean fills | Mean abs. ending position | Mean max drawdown |
|---|---:|---:|---:|---:|---:|
| Unmanaged fixed | -70.07 | 46% | 584.56 | 31.42 | 526.27 |
| Fixed control | 77.24 | 82% | 545.26 | 7.04 | 48.35 |
| QuantEdge | 35.98 | 98% | 194.24 | 1.38 | 13.20 |
| Adaptive loose | 64.64 | 84% | 543.62 | 5.04 | 37.14 |

### Momentum-associated customer flow

| Strategy | Mean PnL | Positive sessions | Mean fills | Mean abs. ending position | Mean max drawdown |
|---|---:|---:|---:|---:|---:|
| Unmanaged fixed | 50.41 | 56% | 584.56 | 39.74 | 317.91 |
| Fixed control | 69.68 | 98% | 545.38 | 4.64 | 36.01 |
| QuantEdge | 44.61 | 100% | 259.34 | 0.90 | 8.98 |
| Adaptive loose | 65.60 | 100% | 695.90 | 2.76 | 20.60 |

All values are averages across 50 sessions. PnL and drawdown are in the simulator's price-times-quantity units; they are not currency-calibrated.

## Interpretation

The new adaptive configuration is a promising risk/activity compromise, not a proven winner:

- Against the very conservative QuantEdge configuration, adaptive quoting raises mean PnL by about 40% in balanced flow, 80% in one-sided flow, and 47% in momentum-associated flow. It also increases fills and inventory exposure.
- Against the managed fixed control, adaptive quoting has lower mean PnL in all three modes, but materially lower average max drawdown: about 52% lower in balanced flow, 23% lower in one-sided flow, and 43% lower in momentum-associated flow.
- The one-sided scenario is the key weakness: adaptive quoting is profitable in 84% of sessions versus 82% for the fixed control, but has a noticeably lower mean PnL. This is not enough evidence to call it superior.
- QuantEdge remains the lowest-drawdown and lowest-inventory configuration, but its conservative quoting leaves substantial trading activity and PnL on the table.
- The approximate 95% confidence intervals for mean PnL overlap between adaptive quoting and the fixed control in all three modes. We therefore should not claim a statistically established PnL improvement.

## Methodology and caveats

The price, RFQ-flow, and competitor-quote random streams are independent, so strategy branches do not alter later random draws. The scenarios are still stylized: customer flow is not calibrated from market data; prices are exogenous; market impact, queue priority, realistic partial fills, and empirically calibrated post-fill markouts are absent. The approximate confidence interval describes seed-to-seed simulation variation only, not uncertainty about the model itself.

These results are not evidence of live-market profitability. Before performance claims, add empirical fill/markout calibration and test a frozen configuration on untouched holdout seeds.

## Reproduction

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
```

## Next experiments

1. Add a training/validation/holdout seed split and tune only on training seeds.
2. Run a parameter sensitivity grid for base spread, volatility multiplier, inventory skew, and hedge threshold.
3. Add fill probability and post-fill markout models calibrated from sourced data.
4. Compare policies on risk-adjusted metrics, not mean PnL alone.
