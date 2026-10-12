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
- Independent seeded streams for price, RFQ flow, and competitor quotes.
- Balanced, one-sided stress, and momentum-associated customer-flow scenarios.
- Risk outputs include PnL dispersion, approximate confidence intervals, maximum absolute position, peak-to-trough drawdown, and maximum loss from session start.

## Research-v2 results

GitHub Actions successfully ran unit tests and the full benchmark matrix: 50 sessions × 1,200 RFQ opportunities for each of three flow modes. [Download benchmark JSON artifacts](https://github.com/rupesh-mr/quantEdge/actions/runs/38264423562).

The adaptive configuration increased mean PnL substantially versus the very conservative QuantEdge configuration, while also increasing inventory exposure and drawdown. Against the managed fixed-spread control, it had lower mean PnL but lower average maximum drawdown in all three scenarios. The one-sided stress case remains challenging. Confidence intervals overlap, so the experiment does not establish a statistically significant PnL improvement.

See [FINDINGS.md](FINDINGS.md) for the full tables and interpretation.

## Caveats and next steps

The customer-flow modes are stylized stress scenarios, not calibrated empirical order flow. Prices remain exogenous; market impact, true queue position, realistic partial fills, and empirically calibrated post-fill markouts are not modeled. The approximate confidence interval reflects variation across simulation seeds, not model uncertainty. These results are not evidence of live-market profitability.

Next: tune parameters on training seeds, freeze one configuration, evaluate on untouched holdout seeds, and calibrate fill/markout assumptions from defensibly sourced data.

## Files

- `dealer_bot.py`: strategy config, quoting, and hedging rules.
- `simulator.py`: synthetic market and customer-flow experiments.
- `tests/test_dealer_bot.py`: strategy and simulator unit tests.
- `benchmark_results.json`: legacy benchmark snapshot.
- `FINDINGS.md`: full research-v2 benchmark results and limitations.
