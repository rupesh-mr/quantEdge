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

## Current model

- Volatility-sensitive quote edge and inventory-skewed reservation price.
- Tick-aligned quoting, hard position limits, and threshold hedging with fees.
- Independent seeded streams for price, RFQ flow, and competitor quotes.
- Balanced, one-sided stress, and momentum-associated customer-flow scenarios.
- Risk outputs include PnL dispersion, approximate confidence intervals, maximum absolute position, peak-to-trough drawdown, and maximum loss from session start.
- Optional stochastic execution mode models probabilistic quote allocation and partial fills, with 1-step and 5-step post-fill markout diagnostics. These are synthetic mechanics, not calibrated exchange behavior.
- The optimizer keeps training, validation, and holdout seeds separate and reports paired seed-wise PnL/drawdown comparisons.

## Research-v2 results

GitHub Actions successfully ran unit tests and the full benchmark matrix: 50 sessions × 1,200 RFQ opportunities for each of three flow modes. [Download benchmark JSON artifacts](https://github.com/rupesh-mr/quantEdge/actions/runs/38264423562).

The adaptive configuration increased mean PnL substantially versus the very conservative QuantEdge configuration, while also increasing inventory exposure and drawdown. Against the managed fixed-spread control, it had lower mean PnL but lower average maximum drawdown in all three scenarios. The one-sided stress case remains challenging. Confidence intervals overlap, so the experiment does not establish a statistically significant PnL improvement.

See [FINDINGS.md](FINDINGS.md) for the full tables and interpretation.

## Caveats and next steps

The customer-flow modes are stylized stress scenarios, not calibrated empirical order flow. Prices remain exogenous; market impact, true queue position, realistic partial fills, and empirically calibrated post-fill markouts are not modeled. The approximate confidence interval reflects variation across simulation seeds, not model uncertainty. These results are not evidence of live-market profitability.

The train/validation/holdout optimization is implemented and its first holdout evaluation is recorded in FINDINGS.md. Next, compare the optional stochastic execution model, then calibrate fill and markout assumptions from defensibly sourced data before interpreting results as market evidence.

## Files

- `dealer_bot.py`: strategy config, quoting, and hedging rules.
- `simulator.py`: synthetic market and customer-flow experiments.
- `tests/test_dealer_bot.py`: strategy and simulator unit tests.
- `benchmark_results.json`: legacy benchmark snapshot.
- `FINDINGS.md`: full research-v2 benchmark results and limitations.
