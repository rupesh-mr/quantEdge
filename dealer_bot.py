"""Inventory-aware quoting and simple hedging rules for QuantEdge."""
from dataclasses import dataclass
from math import ceil, floor, isfinite


@dataclass
class StrategyConfig:
    base_edge_bps: float = 8.0
    volatility_multiplier: float = 0.25
    inventory_skew_bps_per_lot: float = 1.5
    excess_inventory_skew_bps_per_lot: float = 2.0
    max_quote_edge_bps: float = 80.0
    inventory_soft_limit: int = 20
    inventory_hard_limit: int = 35
    hedge_threshold: int = 12
    hedge_fraction: float = 0.75
    exchange_fee_bps: float = 1.0


class QuantEdgeDealer:
    """A small, inspectable rule-based strategy."""

    def __init__(self, config=None):
        self.config = config or StrategyConfig()

    @staticmethod
    def _round_to_tick(price, tick, side):
        # A customer BUY is our ask (round up); a customer SELL is our bid (round down).
        units = price / tick
        rounded = ceil(units - 1e-12) if side == "BUY" else floor(units + 1e-12)
        return round(rounded * tick, 10)

    def quote_one(self, order, market_price, volatility_bps, tick_size, position):
        """Return quote price, or None to decline the RFQ.

        side is the customer's side: BUY means we sell; SELL means we buy.
        volatility_bps is recent mean absolute price change in basis points.
        """
        c = self.config
        try:
            qty = int(order.get("quantity", 1))
            side = str(order["side"]).upper()
            market_price = float(market_price)
            volatility_bps = float(volatility_bps)
            tick_size = float(tick_size)
            position = int(position)
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            return None

        if (qty <= 0 or side not in ("BUY", "SELL")
                or not isfinite(market_price) or market_price <= 0
                or not isfinite(tick_size) or tick_size <= 0
                or not isfinite(volatility_bps)):
            return None
        if c.inventory_hard_limit < 0 or c.inventory_soft_limit < 0:
            return None

        projected_position = position - qty if side == "BUY" else position + qty
        if abs(projected_position) > c.inventory_hard_limit:
            return None
        if abs(position) >= c.inventory_hard_limit and abs(projected_position) >= abs(position):
            return None

        vol_component = max(0.0, volatility_bps) * max(0.0, c.volatility_multiplier)
        spread_edge_bps = min(max(0.0, c.max_quote_edge_bps),
                              max(0.0, c.base_edge_bps + vol_component))

        inventory_skew = position * c.inventory_skew_bps_per_lot
        excess = max(0, abs(position) - c.inventory_soft_limit)
        if excess:
            inventory_skew += (1 if position > 0 else -1) * (
                excess * c.excess_inventory_skew_bps_per_lot
            )
        inventory_skew = max(-c.max_quote_edge_bps,
                             min(c.max_quote_edge_bps, inventory_skew))
        reservation_price = market_price * (1 - inventory_skew / 10000.0)

        if side == "BUY":
            raw_quote = reservation_price * (1 + spread_edge_bps / 10000.0)
        else:
            raw_quote = reservation_price * (1 - spread_edge_bps / 10000.0)

        if not isfinite(raw_quote) or raw_quote <= 0:
            return None
        return max(tick_size, self._round_to_tick(raw_quote, tick_size, side))

    def hedge_one(self, product_id, position, lot_size=1):
        """Return (SELL or BUY, quantity) to reduce a large position."""
        c = self.config
        try:
            position, lot_size = int(position), int(lot_size)
        except (TypeError, ValueError, OverflowError):
            return None
        if lot_size <= 0 or abs(position) < c.hedge_threshold:
            return None
        quantity = (int(abs(position) * c.hedge_fraction) // lot_size) * lot_size
        quantity = min(abs(position), quantity)
        if quantity <= 0:
            return None
        return ("SELL" if position > 0 else "BUY", quantity)

    def quote(self, orders, market, portfolio):
        """Local adapter for the synthetic experiment."""
        result = {}
        prices = market["prices"]
        products = market["products"]
        positions = portfolio.get("positions", {})
        for order in orders:
            pid = order["product_id"]
            result[order["order_id"]] = self.quote_one(
                order, prices[pid],
                market.get("volatility_bps", {}).get(pid, 0.0),
                products[pid]["tick_size"], positions.get(pid, 0)
            )
        return result

    def hedge(self, market, portfolio):
        """Return (product_id, side, quantity) tuples for the local experiment."""
        actions = []
        for pid, pos in portfolio.get("positions", {}).items():
            lot = market["products"][pid].get("lot_size", 1)
            action = self.hedge_one(pid, pos, lot)
            if action:
                actions.append((pid, action[0], action[1]))
        return actions
