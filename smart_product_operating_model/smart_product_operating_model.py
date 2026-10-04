"""
Smart Product Operating Model - simple base version

Manages products through their lifecycle, tracks operating metrics
(sales, stock, cost, quality), and recommends actions with simple rules.
Run:  python smart_product_operating_model.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
import json


class Stage(Enum):
    IDEA = "Idea"
    DEVELOPMENT = "Development"
    LAUNCH = "Launch"
    GROWTH = "Growth"
    MATURITY = "Maturity"
    RETIRED = "Retired"


STAGE_ORDER = list(Stage)


@dataclass
class Product:
    product_id: str
    name: str
    price: float
    unit_cost: float
    stock: int
    reorder_level: int = 20
    stage: Stage = Stage.IDEA
    monthly_sales: List[int] = field(default_factory=list)   # units sold per month
    quality_score: float = 100.0                              # 0-100
    defect_rate: float = 0.0                                  # 0-1

    # ---- core metrics ----
    @property
    def margin(self) -> float:
        return (self.price - self.unit_cost) / self.price if self.price else 0.0

    @property
    def revenue(self) -> float:
        return sum(self.monthly_sales) * self.price

    @property
    def profit(self) -> float:
        return sum(self.monthly_sales) * (self.price - self.unit_cost)

    @property
    def sales_trend(self) -> float:
        """Percent change between the last two months."""
        if len(self.monthly_sales) < 2 or self.monthly_sales[-2] == 0:
            return 0.0
        prev, last = self.monthly_sales[-2], self.monthly_sales[-1]
        return (last - prev) / prev * 100


class OperatingModel:
    def __init__(self):
        self.products: Dict[str, Product] = {}

    # ---- product management ----
    def add_product(self, product: Product):
        self.products[product.product_id] = product

    def record_sales(self, product_id: str, units: int):
        p = self.products[product_id]
        p.monthly_sales.append(units)
        p.stock = max(0, p.stock - units)

    def restock(self, product_id: str, units: int):
        self.products[product_id].stock += units

    def advance_stage(self, product_id: str):
        p = self.products[product_id]
        i = STAGE_ORDER.index(p.stage)
        if i < len(STAGE_ORDER) - 1:
            p.stage = STAGE_ORDER[i + 1]

    # ---- smart rules ----
    def recommend(self, product_id: str) -> List[str]:
        p = self.products[product_id]
        actions = []

        if p.stage == Stage.RETIRED:
            return ["Product retired - no action."]

        # Inventory
        if p.stock <= p.reorder_level:
            actions.append(f"Restock: stock ({p.stock}) at/below reorder level ({p.reorder_level}).")

        # Pricing / margin
        if p.margin < 0.20:
            actions.append(f"Review pricing or cost: margin is {p.margin:.0%} (target >= 20%).")

        # Quality
        if p.defect_rate > 0.05 or p.quality_score < 80:
            actions.append("Quality alert: investigate defects before scaling production.")

        # Demand and lifecycle
        trend = p.sales_trend
        if p.stage == Stage.LAUNCH and trend > 10:
            actions.append("Strong launch traction - move to Growth stage.")
        elif p.stage == Stage.GROWTH and trend < 2 and len(p.monthly_sales) >= 3:
            actions.append("Growth is flattening - consider moving to Maturity stage.")
        elif p.stage == Stage.MATURITY and trend < -10:
            actions.append("Sales declining in Maturity - plan refresh or retirement.")
        elif trend < -20:
            actions.append(f"Sales dropped {trend:.0f}% - run a promotion or investigate demand.")

        return actions or ["No action needed - operating normally."]

    # ---- reporting ----
    def report(self):
        print("=" * 70)
        print("SMART PRODUCT OPERATING MODEL - STATUS REPORT")
        print("=" * 70)
        total_rev = total_profit = 0.0
        for p in self.products.values():
            total_rev += p.revenue
            total_profit += p.profit
            print(f"\n[{p.product_id}] {p.name}  | Stage: {p.stage.value}")
            print(f"  Price: {p.price:.2f}  Cost: {p.unit_cost:.2f}  Margin: {p.margin:.0%}")
            print(f"  Stock: {p.stock}  Revenue: {p.revenue:,.2f}  Profit: {p.profit:,.2f}")
            print(f"  Sales trend (last month): {p.sales_trend:+.1f}%")
            for a in self.recommend(p.product_id):
                print(f"  -> {a}")
        print("\n" + "-" * 70)
        print(f"TOTAL REVENUE: {total_rev:,.2f}   TOTAL PROFIT: {total_profit:,.2f}")
        print("=" * 70)

    def export_json(self, path: str = "operating_model.json"):
        data = [
            {
                "id": p.product_id,
                "name": p.name,
                "stage": p.stage.value,
                "margin": round(p.margin, 3),
                "revenue": p.revenue,
                "profit": p.profit,
                "stock": p.stock,
                "recommendations": self.recommend(p.product_id),
            }
            for p in self.products.values()
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported to {path}")


# ---- demo ----
if __name__ == "__main__":
    model = OperatingModel()

    model.add_product(Product("P001", "Smart Thermostat", price=120, unit_cost=80,
                              stock=150, stage=Stage.LAUNCH))
    model.add_product(Product("P002", "Smart Light Bulb", price=15, unit_cost=13,
                              stock=330, stage=Stage.GROWTH, defect_rate=0.07))
    model.add_product(Product("P003", "Smart Door Lock", price=200, unit_cost=110,
                              stock=400, stage=Stage.MATURITY))

    for pid, sales in {"P001": [20, 30, 40], "P002": [100, 102, 103], "P003": [80, 70, 55]}.items():
        for s in sales:
            model.record_sales(pid, s)

    model.report()
    model.export_json()
