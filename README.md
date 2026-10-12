# QuantEdge: inventory-aware market-making research

A small, dependency-free Python research project for comparing RFQ quoting policies under stylized synthetic market and customer-flow assumptions. This is a simulator, not a claim of live-market profitability.

## Run

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
```

## Current model

- Volatility-sensitive quote edge and inventory-skewed reservation price.
- Tick-aligned quoting, hard position limits, and threshold hedging with fees.
- Reproducible random seeds, matched-seed strategy comparisons, and PnL uncertainty summaries.
- Flow scenarios: balanced, one-sided stress, and momentum-associated customer flow.
- Risk outputs include maximum absolute position, peak-to-trough drawdown, and maximum loss from session start.

## Interpretation of the first benchmark

In the original 50-session balanced-flow snapshot, QuantEdge had mean PnL 45.36 versus 75.89 for the managed fixed-spread control, but lower mean absolute ending inventory (0.96 versus 5.02) and lower mean maximum drawdown (8.39 versus 36.53). The result is a risk/activity trade-off, not a strategy win. The original benchmark also had zero QuantEdge hedge events.

## Caveats and research next steps

The model remains deliberately stylized. Customer-flow modes are stress scenarios rather than calibrated empirical order flow. The price process is exogenous, competitor quotes are randomized, and there is no market impact, queue position, partial fill model, or calibration to historical data. The reported 95% interval is a normal approximation for the mean across independent seeded sessions; it does not represent model uncertainty.

Suggested next experiments:
1. Compare policies across all three flow modes using the same seed set.
2. Tune quote and inventory parameters on a designated training seed range only.
3. Freeze the selected policy and report untouched holdout seeds.
4. Add calibrated fill/markout models before making claims about trading performance.

## Files

- `dealer_bot.py`: strategy config, quoting, and hedging rules.
- `simulator.py`: synthetic market and customer-flow experiments.
- `tests/test_dealer_bot.py`: strategy and simulator unit tests.
- `benchmark_results.json`: legacy benchmark snapshot.
- `FINDINGS.md`: interpretation of the original snapshot and limitations.
