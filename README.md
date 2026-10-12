# QuantEdge: inventory-aware market-making experiment

A standalone Python project for studying RFQ quoting, inventory risk, and hedging through a reproducible synthetic simulator. The results describe this simulator only and should not be interpreted as evidence of live-market profitability.

## Run

Requires Python 3; no third-party dependencies.

```bash
python -m unittest discover -s tests -v
python simulator.py --sessions 50 --steps 1200 --seed 100
```

## Strategy

- Volatility-adjusted quote spreads.
- Inventory-aware reservation-price shifts.
- Hard position limits and tick-aligned quotes.
- Threshold hedging with simulated exchange fees.
- Synthetic benchmark against an unmanaged fixed-spread baseline and a managed fixed-spread control.

## Benchmark snapshot

Across 50 synthetic sessions (seeds 100–149, 1,200 RFQ opportunities each):

| Strategy | Mean PnL | Positive sessions | Mean fills | Mean absolute ending position | Mean max drawdown |
|---|---:|---:|---:|---:|---:|
| Unmanaged fixed spread | 85.87 | 64% | 590.9 | 35.76 | 270.18 |
| Managed fixed-spread control | 75.89 | 94% | 552.3 | 5.02 | 36.53 |
| QuantEdge | 45.36 | 100% | 265.6 | 0.96 | 8.39 |

QuantEdge is more conservative in this sample, but has lower mean PnL and fewer fills than the managed fixed spread control. This is a risk/activity trade-off, not a claim of strategy superiority. Hedging did not trigger in QuantEdge's benchmark sessions; the hedge logic is covered by unit tests but needs additional scenario testing.

## Limitations

The simulator uses synthetic prices and randomized customer flow. It does not model market impact or informed/adverse-selection flow. See [FINDINGS.md](FINDINGS.md) for details.

## Files

- `dealer_bot.py`: quoting and hedging rules.
- `simulator.py`: reproducible synthetic benchmark.
- `tests/test_dealer_bot.py`: unit tests.
- `benchmark_results.json`: saved benchmark output.
- `FINDINGS.md`: interpretation, caveats, and next experiments.
