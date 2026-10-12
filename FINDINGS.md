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

Seed-paired holdout deltas are now computed using the same seeds for each policy. Against fixed control, the selected configuration's paired PnL difference was +1.08 in balanced flow (approx. 95% CI [-11.04, 13.20]), -8.07 in one-sided flow ([-16.90, 0.76]), and -6.27 in informed flow ([-16.36, 3.81]). All three intervals include zero, so the holdout does not show a clear PnL advantage over fixed control. Paired drawdown differences were -20.99 ([-25.83, -16.14]), -19.06 ([-22.23, -15.89]), and -15.52 ([-18.77, -12.26]), respectively. These are approximate, descriptive intervals without multiple-comparison adjustment; pairing does not address model misspecification or the fact that the strategy was selected from a grid.

## Legacy versus stochastic execution sensitivity

The stochastic execution benchmark completed on the same 50 seeds (100–149), 1,200 steps, and three flow modes as the legacy benchmark. The stochastic model uses probabilistic quote allocation and synthetic partial fills. Paired PnL deltas below are stochastic minus legacy for the same seed; approximate 95% intervals use the per-seed PnL values rounded in the benchmark JSON.

| Flow | Strategy | PnL delta | Approx. paired 95% CI | Legacy / stochastic mean drawdown | Stochastic partial fills/session |
|---|---|---:|---:|---:|---:|
| Balanced | QuantEdge | +5.98 | [0.47, 11.50] | 8.27 / 10.95 | 36.58 |
| Balanced | Fixed control | -9.21 | [-19.26, 0.83] | 37.73 / 37.19 | 62.78 |
| Balanced | Adaptive loose | -10.37 | [-15.73, -5.01] | 18.16 / 20.42 | 78.48 |
| One-sided | QuantEdge | +2.34 | [-3.20, 7.87] | 13.20 / 21.60 | 27.64 |
| One-sided | Fixed control | -7.06 | [-16.46, 2.34] | 48.35 / 47.28 | 64.28 |
| One-sided | Adaptive loose | -6.33 | [-12.43, -0.22] | 37.14 / 40.84 | 59.42 |
| Informed | QuantEdge | +6.30 | [2.02, 10.57] | 8.98 / 11.61 | 36.56 |
| Informed | Fixed control | -0.55 | [-11.92, 10.82] | 36.01 / 37.25 | 63.46 |
| Informed | Adaptive loose | -7.53 | [-13.34, -1.71] | 20.60 / 21.93 | 76.20 |

### Markout diagnostics

Markout is the signed mid-price move after a fill, in basis points, where positive means the subsequent mid move favored the dealer's inventory change. It is **not** net trade profitability: it excludes the quoted spread, hedge fees, and other execution costs.

| Flow | Strategy | 1-step markout (bps) | 5-step markout (bps) |
|---|---|---:|---:|
| Balanced | QuantEdge | +0.0683 | +0.5356 |
| Balanced | Fixed control | -0.0237 | +0.1137 |
| Balanced | Adaptive loose | +0.0504 | +0.2800 |
| One-sided | QuantEdge | -0.3197 | +0.0435 |
| One-sided | Fixed control | +0.0596 | +0.8440 |
| One-sided | Adaptive loose | -0.1245 | +0.5052 |
| Informed | QuantEdge | -0.2029 | +0.6518 |
| Informed | Fixed control | -0.0467 | +0.4130 |
| Informed | Adaptive loose | -0.1553 | +0.3637 |

The main result is **model sensitivity, not a new winner**. Under this stochastic fill assumption, QuantEdge's mean PnL rises versus legacy in all three flow modes, with paired intervals excluding zero in balanced and informed flow, but its mean drawdown also rises. The adaptive-loose policy loses PnL versus legacy in all three modes, with paired intervals excluding zero; its drawdown also rises modestly. Fixed-control PnL changes are inconclusive under these intervals. Stochastic partial fills are frequent, so the execution assumption materially affects policy rankings.

These results remain synthetic. The allocation curve, competitor quote process, and fill-size randomization are not calibrated to venue data. The markouts are diagnostic only and should not be interpreted as evidence of live-market profitability.

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

1. Compare the legacy deterministic fill model against the optional stochastic partial-fill model and inspect markout diagnostics.
2. Calibrate fill and markout assumptions against a defensibly sourced dataset before interpreting the simulator as market evidence.
3. Add latency and richer queue/competition assumptions only where the execution venue makes those mechanics appropriate.
4. Only then evaluate a frozen policy on another untouched holdout.
