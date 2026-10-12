# Experiment results

All results below come from the synthetic simulator. PnL and drawdown are in price-times-quantity units, not currency. Runs use 50 sessions per scenario and 1,200 RFQ steps per session unless noted.

## Main benchmark

Mean results across seeds 100–149:

| Flow | Strategy | Mean PnL | Positive sessions | Mean fills | Mean ending position (absolute) | Mean drawdown |
|---|---|---:|---:|---:|---:|---:|
| Balanced | Unmanaged fixed | 73.74 | 74% | 584.56 | 43.58 | 306.26 |
| Balanced | Fixed control | 66.75 | 98% | 545.28 | 4.90 | 37.73 |
| Balanced | QuantEdge | 45.01 | 100% | 262.72 | 0.70 | 8.27 |
| Balanced | Adaptive loose | 63.18 | 98% | 702.42 | 2.50 | 18.16 |
| One-sided | Unmanaged fixed | -70.07 | 46% | 584.56 | 31.42 | 526.27 |
| One-sided | Fixed control | 77.24 | 82% | 545.26 | 7.04 | 48.35 |
| One-sided | QuantEdge | 35.98 | 98% | 194.24 | 1.38 | 13.20 |
| One-sided | Adaptive loose | 64.64 | 84% | 543.62 | 5.04 | 37.14 |
| Informed | Unmanaged fixed | 50.41 | 56% | 584.56 | 39.74 | 317.91 |
| Informed | Fixed control | 69.68 | 98% | 545.38 | 4.64 | 36.01 |
| Informed | QuantEdge | 44.61 | 100% | 259.34 | 0.90 | 8.98 |
| Informed | Adaptive loose | 65.60 | 100% | 695.90 | 2.76 | 20.60 |

QuantEdge trades less often and keeps inventory and drawdown lower than the other tested policies, but its mean PnL is also lower than the fixed control and adaptive-loose policy in these runs.

## Parameter search

The optimizer tested 54 configurations. It ranked them on 20 training seeds, compared the top five on 20 validation seeds, then evaluated the selected configuration on 50 separate holdout seeds. The objective was mean PnL minus 0.5 times mean drawdown, averaged equally across the three flow scenarios.

Selected settings: base edge 5 bps, volatility multiplier 0.05, inventory skew 0.8 bps/lot, excess skew 2 bps/lot, maximum edge 55 bps, soft/hard inventory limits 12/28, hedge threshold 8, hedge fraction 0.65, and hedge fee 1 bps.

| Flow | Strategy | Mean PnL | Approx. 95% interval | Positive sessions | Mean drawdown |
|---|---|---:|---:|---:|---:|
| Balanced | Selected configuration | 72.49 | [64.84, 80.14] | 98% | 16.11 |
| Balanced | Fixed control | 71.41 | [58.11, 84.71] | 94% | 37.09 |
| Balanced | Current QuantEdge | 44.47 | [40.53, 48.41] | 100% | 8.93 |
| One-sided | Selected configuration | 69.50 | [58.37, 80.64] | 96% | 27.37 |
| One-sided | Fixed control | 77.58 | [61.70, 93.45] | 90% | 46.43 |
| One-sided | Current QuantEdge | 35.05 | [28.98, 41.12] | 94% | 13.49 |
| Informed | Selected configuration | 66.64 | [59.21, 74.08] | 100% | 18.91 |
| Informed | Fixed control | 72.91 | [60.64, 85.19] | 94% | 34.42 |
| Informed | Current QuantEdge | 45.12 | [40.67, 49.58] | 100% | 9.43 |

Against the fixed control, the selected configuration's paired mean PnL differences were +1.08 for balanced flow (interval [-11.04, 13.20]), -8.07 for one-sided flow ([-16.90, 0.76]), and -6.27 for informed flow ([-16.36, 3.81]). Each interval includes zero, so these runs do not show a clear PnL advantage. Mean drawdown was lower than the fixed control in all three scenarios.

## Execution model comparison

The following values compare stochastic execution with the legacy fill model on the same seeds (100–149). PnL delta is stochastic minus legacy.

| Flow | Strategy | PnL delta | Approx. paired 95% interval | Drawdown: legacy / stochastic | Partial fills per session |
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

The stochastic model increased QuantEdge's mean PnL in all three scenarios, but drawdown also rose. The adaptive-loose policy's mean PnL fell in all three. The fill model is synthetic, so this is a sensitivity check rather than evidence that one strategy is better in a real market.

## Markout checks

Mean signed mid-price move after a fill, in basis points. Positive values mean the subsequent price move favored the dealer's inventory change. This excludes spread income, fees, and other costs.

| Flow | Strategy | 1-step | 5-step |
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

## Limitations

Customer flow, competitor quotes, and fill probabilities are stylized; prices are generated independently of the strategy. The simulator does not model market impact, venue latency, or real queue priority. Confidence intervals describe variation across seeds and do not account for errors in the model assumptions. These results are not evidence of live-market profitability.

## Reproduce

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced --execution-model stochastic
python optimize.py --steps 1200 --train-start 100 --train-sessions 20 --validation-start 500 --validation-sessions 20 --holdout-start 1000 --holdout-sessions 50
```

Full benchmark and optimization logs are available in [GitHub Actions](https://github.com/rupesh-mr/quantEdge/actions).
