# QuantEdge experiment findings

## Research-v2 full benchmark

GitHub Actions successfully ran unit tests, smoke tests, and the full benchmark matrix on 12 October 2026. Each scenario uses 50 seeded sessions (seeds 100–149), 1,200 RFQ opportunities per session, and independent price/RFQ/competitor random streams. [Benchmark and optimization artifacts](https://github.com/rupesh-mr/quantEdge/actions/runs/38265056048).

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

All values are averages across 50 sessions. PnL and drawdown are in synthetic price-times-quantity units, not currency-calibrated results.

## Train/validation/holdout optimization

The optimizer searched 54 configurations using training seeds 100–119, retained the top five, selected among those using validation seeds 500–519, and then evaluated the selected configuration once on holdout seeds 1000–1049. The selection objective was equally weighted across balanced, one-sided, and informed flow: mean PnL minus 0.5 times mean peak-to-trough drawdown. Holdout data was not used for selection.

Selected configuration:

| Parameter | Value |
|---|---:|
| Base quote edge | 5 bps |
| Volatility multiplier | 0.05 |
| Inventory skew | 0.8 bps/lot |
| Excess inventory skew | 2 bps/lot |
| Maximum quote edge | 55 bps |
| Soft / hard inventory limits | 12 / 28 |
| Hedge threshold / fraction | 8 / 0.65 |
| Exchange hedge fee | 1 bps |

### Holdout results (50 sessions per flow mode)

| Flow | Strategy | Mean PnL | Approx. 95% CI | Positive sessions | Mean drawdown |
|---|---|---:|---:|---:|---:|
| Balanced | Selected adaptive | 72.49 | [64.84, 80.14] | 98% | 16.11 |
| Balanced | Fixed control | 71.41 | [58.11, 84.71] | 94% | 37.09 |
| Balanced | Current QuantEdge | 44.47 | [40.53, 48.41] | 100% | 8.93 |
| One-sided | Selected adaptive | 69.50 | [58.37, 80.64] | 96% | 27.37 |
| One-sided | Fixed control | 77.58 | [61.70, 93.45] | 90% | 46.43 |
| One-sided | Current QuantEdge | 35.05 | [28.98, 41.12] | 94% | 13.49 |
| Informed | Selected adaptive | 66.64 | [59.21, 74.08] | 100% | 18.91 |
| Informed | Fixed control | 72.91 | [60.64, 85.19] | 94% | 34.42 |
| Informed | Current QuantEdge | 45.12 | [40.67, 49.58] | 100% | 9.43 |

The selected configuration produces much more PnL than the conservative current QuantEdge policy, with higher drawdown and inventory exposure. Against the fixed control, it is close to even in balanced flow (+1.08 mean PnL), and lower in one-sided (-8.07) and informed flow (-6.27). Mean drawdown is lower than fixed control by 56.6%, 41.1%, and 45.1%, respectively. The individual approximate PnL confidence intervals overlap. These are descriptive simulation results, not evidence of live-market profitability.

The next CI revision adds seed-paired holdout deltas and approximate confidence intervals. Pairing by seed can reduce noise from differences in simulated paths; it still does not account for model misspecification or repeated strategy selection.

## Methodology and caveats

The price, RFQ-flow, and competitor-quote random streams are independent, so strategy branches do not alter later random draws. Customer flow is not calibrated from real order flow; prices are exogenous; market impact, queue priority, realistic partial fills, latency, and empirically calibrated post-fill markouts are absent. The confidence intervals describe variation across simulation seeds only, not uncertainty about the model itself.

These results are not evidence of live-market profitability. Before making performance claims, add explicit microstructure assumptions, evaluate adverse-selection markouts, and calibrate with sourced market data if available.

## Reproduction

\`\`\`bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
python optimize.py --steps 1200 --train-start 100 --train-sessions 20 --validation-start 500 --validation-sessions 20 --holdout-start 1000 --holdout-sessions 50
\`\`\`

## Next experiments

1. Add seed-paired holdout comparisons and confidence intervals (now implemented in optimize.py).
2. Add configurable latency, queue competition, partial fills, and post-fill markout diagnostics.
3. Calibrate fill and markout assumptions against a defensibly sourced dataset before interpreting the simulator as market evidence.
4. Only then evaluate a frozen policy on another untouched holdout.
