# QuantEdge experiment findings

## Question

Does adding volatility-aware spreads and inventory-aware pricing change the balance between trading activity, PnL, and inventory risk compared with a fixed-spread rule?

## Setup

- 50 random seeds: 100–149
- 1,200 RFQ opportunities per session
- Same seeds and synthetic market process for all three strategies
- PnL = customer-trade cash flows + final marked inventory value − exchange hedge fees
- The synthetic price process has alternating volatility regimes and a small positive drift.
- RFQ sides, sizes, customer limits, and competitor edges are random.

## Results

| Strategy | Mean PnL | Median PnL | Positive sessions | Mean fills | Mean absolute ending position | Mean max absolute position | Mean hedges | Mean hedge fees | Mean max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Unmanaged fixed spread | 85.87 | 56.78 | 64.0% | 590.9 | 35.76 | 55.16 | 0.00 | 0.0000 | 270.18 |
| Managed fixed-spread control | 75.89 | 81.64 | 94.0% | 552.3 | 5.02 | 11.00 | 12.58 | 1.1706 | 36.53 |
| QuantEdge | 45.36 | 45.37 | 100.0% | 265.6 | 0.96 | 5.56 | 0.00 | 0.0000 | 8.39 |

## What the numbers suggest

1. **Risk controls materially change behaviour.** The unmanaged fixed-spread reference trades much more and ends with much larger positions. Its higher mean PnL in this run comes with much larger drawdown and is not a fair comparison to the managed strategies.
2. **QuantEdge is more conservative than the fixed control.** Its inventory skew and volatility adjustment led to fewer fills, lower mean PnL, smaller ending positions, and lower drawdown in this sample.
3. **There is a tuning problem, not a victory claim.** The current settings appear to trade too little relative to the fixed control under these simulator assumptions. The next step should be a controlled parameter study, not claiming QuantEdge is superior.
4. **Hedging was not exercised by QuantEdge in this run.** Inventory stayed below the threshold. Unit tests confirm the hedge function's basic direction and quantity behaviour, but scenario tests with persistent one-sided order flow are still needed.
5. **Market impact and adverse selection are missing.** Because the synthetic price process does not react to our trades and customer direction is random, this experiment cannot evaluate how trading affects prices or how the strategy responds to informed customer flow.

## Important caveats

- This is one parameter configuration on one synthetic simulator, not a market model calibrated to data.
- The same seeds improve comparability but do not make the simulator realistic.
- Parameters were not selected using a separate training/holdout process.
- The unmanaged strategy intentionally lacks the same risk controls, so it is only a cautionary reference.
- Outcomes may differ substantially in real markets, where fees, customer behaviour, settlement, and market impact vary accordingly.

## Reproduction

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1300 --seed 100
```

Compare the output to `benchmark_results.json`. Minor differences may occur if the code or Python random/statistics implementation changes.
