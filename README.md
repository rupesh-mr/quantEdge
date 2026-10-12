# QuantEdge

A Python simulator for testing market-making rules under synthetic RFQ flow. It compares quoting and inventory controls, and tests how assumed execution behavior changes results. It is an experiment, not a live trading system.

## Run

Requires Python 3.12 or newer.

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow one_sided
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow informed
python simulator.py --sessions 50 --steps 1200 --seed 100 --flow balanced --execution-model stochastic
python optimize.py --steps 1200 --train-start 100 --train-sessions 20 --validation-start 500 --validation-sessions 20 --holdout-start 1000 --holdout-sessions 50
```

To compare saved legacy and stochastic runs, put the six simulator JSON files in one directory and run:

```bash
python compare_execution.py --directory benchmark_output
```

## What it tests

- Quote prices that respond to volatility and current inventory.
- Position limits and threshold-based hedging.
- Balanced, one-sided, and momentum-associated customer flow.
- Deterministic fills versus synthetic probabilistic allocation and partial fills.
- Parameter search with separate training, validation, and holdout seeds.

## Results

See [FINDINGS.md](FINDINGS.md) for benchmark tables and optimization results. In short, the stochastic execution assumption increased QuantEdge's mean simulated PnL in all three flow scenarios, but also increased drawdown. The optimized configuration reduced drawdown relative to the fixed control, but did not show a clear PnL advantage on the holdout seeds.

These results depend on the simulator's assumptions. Prices, customer flow, competitor quotes, and fill behavior are synthetic; the model does not include calibrated queue priority, latency, or market impact. Results do not establish live-market profitability.

## Files

- `dealer_bot.py`: quoting and hedging rules.
- `simulator.py`: market and RFQ simulation.
- `optimize.py`: parameter search and holdout evaluation.
- `compare_execution.py`: comparison of execution models.
- `tests/`: unit tests.
