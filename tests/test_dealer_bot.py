import unittest
from optimize import candidate_configs
from dealer_bot import QuantEdgeDealer, StrategyConfig
from simulator import run_session


class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.bot = QuantEdgeDealer()

    def test_quote_is_positive_and_tick_aligned(self):
        q = self.bot.quote_one({"side": "BUY", "quantity": 2}, 100, 10, .01, 0)
        self.assertIsNotNone(q)
        self.assertGreater(q, 0)
        self.assertAlmostEqual(q / .01, round(q / .01), places=7)

    def test_invalid_inputs_are_declined(self):
        for order, price, vol, tick, pos in [
            ({"side": "HOLD", "quantity": 1}, 100, 10, .01, 0),
            ({"side": "BUY", "quantity": 0}, 100, 10, .01, 0),
            ({"side": "BUY", "quantity": 1}, -1, 10, .01, 0),
            ({"side": "BUY", "quantity": 1}, 100, float("nan"), .01, 0),
            ({}, 100, 10, .01, 0),
            ({"side": "BUY", "quantity": 1}, 100, 10, 0, 0),
        ]:
            self.assertIsNone(self.bot.quote_one(order, price, vol, tick, pos))

    def test_order_that_breaches_hard_limit_is_declined(self):
        bot = QuantEdgeDealer(StrategyConfig(inventory_hard_limit=5))
        self.assertIsNone(bot.quote_one({"side": "SELL", "quantity": 2}, 100, 5, .01, 4))

    def test_long_inventory_shifts_both_quotes_down(self):
        ask_flat = self.bot.quote_one({"side": "BUY", "quantity": 1}, 100, 10, .01, 0)
        ask_long = self.bot.quote_one({"side": "BUY", "quantity": 1}, 100, 10, .01, 10)
        bid_flat = self.bot.quote_one({"side": "SELL", "quantity": 1}, 100, 10, .01, 0)
        bid_long = self.bot.quote_one({"side": "SELL", "quantity": 1}, 100, 10, .01, 10)
        self.assertLess(ask_long, ask_flat)
        self.assertLess(bid_long, bid_flat)

    def test_short_inventory_shifts_quotes_up(self):
        ask_flat = self.bot.quote_one({"side": "BUY", "quantity": 1}, 100, 10, .01, 0)
        ask_short = self.bot.quote_one({"side": "BUY", "quantity": 1}, 100, 10, .01, -10)
        self.assertGreater(ask_short, ask_flat)

    def test_soft_limit_increases_inventory_skew(self):
        cfg = StrategyConfig(inventory_skew_bps_per_lot=0.1,
                             excess_inventory_skew_bps_per_lot=3.0,
                             inventory_soft_limit=2)
        bot = QuantEdgeDealer(cfg)
        quote_inside = bot.quote_one({"side": "BUY", "quantity": 1}, 100, 0, .01, 2)
        quote_outside = bot.quote_one({"side": "BUY", "quantity": 1}, 100, 0, .01, 5)
        self.assertLess(quote_outside, quote_inside)

    def test_position_at_hard_limit_can_only_reduce(self):
        bot = QuantEdgeDealer(StrategyConfig(inventory_hard_limit=5))
        self.assertIsNotNone(bot.quote_one({"side": "BUY", "quantity": 1}, 100, 5, .01, 5))
        self.assertIsNone(bot.quote_one({"side": "SELL", "quantity": 1}, 100, 5, .01, 5))


class HedgeTests(unittest.TestCase):
    def setUp(self):
        self.bot = QuantEdgeDealer()

    def test_no_hedge_below_threshold(self):
        self.assertIsNone(self.bot.hedge_one("X", 11))

    def test_hedge_reduces_position(self):
        side, qty = self.bot.hedge_one("X", 20)
        self.assertEqual(side, "SELL")
        self.assertGreater(qty, 0)
        self.assertLess(qty, 20)

    def test_invalid_lot_size_is_ignored(self):
        self.assertIsNone(self.bot.hedge_one("X", 20, 0))

    def test_short_position_is_bought_back(self):
        self.assertEqual(self.bot.hedge_one("X", -20), ("BUY", 15))


class OptimizerTests(unittest.TestCase):
    def test_candidate_grid_is_nonempty_and_unique(self):
        candidates = list(candidate_configs())
        self.assertEqual(len(candidates), 54)
        self.assertEqual(len({tuple(sorted(vars(c).items())) for c in candidates}), 54)

    def test_candidates_have_risk_limits(self):
        for config in candidate_configs():
            self.assertGreater(config.inventory_hard_limit, 0)
            self.assertGreaterEqual(config.base_edge_bps, 0)
            self.assertGreater(config.hedge_threshold, 0)


class SimulatorTests(unittest.TestCase):
    def test_reproducible_with_same_seed(self):
        a = run_session(seed=123, n_steps=100, strategy="quantedge")
        b = run_session(seed=123, n_steps=100, strategy="quantedge")
        self.assertEqual(a, b)

    def test_unknown_strategy_fails_fast(self):
        with self.assertRaises(ValueError):
            run_session(seed=1, n_steps=5, strategy="not-a-strategy")

    def test_stress_modes_are_supported(self):
        for mode in ("balanced", "one_sided", "informed"):
            result = run_session(seed=22, n_steps=100, strategy="quantedge", flow_mode=mode)
            self.assertEqual(result["steps"], 100)
            self.assertGreaterEqual(result["max_abs_position"], 0)

    def test_drawdown_metrics_are_nonnegative(self):
        result = run_session(seed=12, n_steps=100)
        self.assertGreaterEqual(result["max_drawdown_from_peak"], 0)
        self.assertGreaterEqual(result["max_loss_from_start"], 0)

    def test_stochastic_execution_reports_partial_fill_and_markout_metrics(self):
        result = run_session(seed=22, n_steps=500, execution_model="stochastic")
        self.assertEqual(result["execution_model"], "stochastic")
        self.assertGreater(result["fills"], 0)
        self.assertGreater(result["markout_1_step_observations"], 0)
        self.assertGreater(result["markout_5_step_observations"], 0)
        self.assertGreaterEqual(result["partial_fills"], 0)
        self.assertIsNotNone(result["mean_markout_1_step_bps"])

    def test_stochastic_execution_is_reproducible(self):
        a = run_session(seed=44, n_steps=150, execution_model="stochastic")
        b = run_session(seed=44, n_steps=150, execution_model="stochastic")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
