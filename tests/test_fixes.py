"""Regression tests for reports 1-5. Each one fails on the old code and passes on the fixed code."""
import os
import tempfile
import unittest

from tillpoint import db, pricing, reports
from tillpoint.catalog import Catalog, OutOfStock
from tillpoint.orders import Orders
from tillpoint.payments import Payments


def make_shop(path=":memory:", stock=10):
    conn = db.connect(path)
    catalog = Catalog(conn)
    catalog.add_product("A", "Apple", 1000, stock)
    conn.execute("INSERT OR IGNORE INTO coupons (code, kind, value) VALUES ('TEN', 'percent', 10)")
    return conn, catalog


class FixesTest(unittest.TestCase):
    def test_report1_repeated_webhook_is_counted_once(self):
        conn, catalog = make_shop()
        order = Orders(conn, catalog).create("bob", [("A", 1)])
        payments = Payments(conn)
        event = {"id": "evt1", "type": "payment.succeeded", "order_id": order["id"],
                 "amount_cents": order["total_cents"]}
        self.assertEqual(payments.handle_event(event), "paid")
        self.assertEqual(payments.handle_event(event), "paid")  # provider retry
        self.assertEqual(payments.paid_cents(order["id"]), order["total_cents"])

    def test_report2_cancelling_pending_order_returns_stock(self):
        conn, catalog = make_shop(stock=10)
        orders = Orders(conn, catalog)
        order = orders.create("bob", [("A", 4)])
        self.assertEqual(catalog.get_product("A").stock, 6)
        orders.cancel(order["id"])
        self.assertEqual(catalog.get_product("A").stock, 10)

    def test_report3_tax_is_on_the_discounted_price(self):
        coupon = {"code": "TEN", "kind": "percent", "value": 10, "min_subtotal_cents": 0,
                  "max_uses": None, "uses": 0}
        totals = pricing.price_order([(1000, 1)], "CA", coupon)
        self.assertEqual(totals["discount_cents"], 100)
        self.assertEqual(totals["tax_cents"], 65)       # 7.25% of 900
        self.assertEqual(totals["total_cents"], 965)

    def test_report4_day_bounds_for_utc_plus_530(self):
        start, end = reports.day_bounds_utc("2026-11-21", 330)
        self.assertEqual(start, "2026-11-20T18:30:00Z")
        self.assertEqual(end, "2026-11-21T18:30:00Z")

    def test_report4_morning_sale_in_india_is_in_that_days_report(self):
        conn, catalog = make_shop()
        order = Orders(conn, catalog).create("bob", [("A", 1)])
        # 08:00 India time on 21 Nov = 02:30 UTC on 21 Nov
        event = {"id": "e1", "type": "payment.succeeded", "order_id": order["id"],
                 "amount_cents": order["total_cents"]}
        Payments(conn).handle_event(event, now=db.from_iso("2026-11-21T02:30:00Z"))
        report = reports.daily_sales(conn, "2026-11-21", 330)
        self.assertEqual(report["revenue_cents"], order["total_cents"])

    def test_report5_two_workers_cannot_oversell(self):
        path = os.path.join(tempfile.mkdtemp(), "shop.db")
        conn1, catalog1 = make_shop(path, stock=5)
        conn2 = db.connect(path)
        catalog2 = Catalog(conn2)
        catalog1.get_product("A")
        catalog2.get_product("A")                      # both workers have a cached copy: stock 5
        Orders(conn1, catalog1).create("a", [("A", 5)])
        with self.assertRaises(OutOfStock):
            Orders(conn2, catalog2).create("b", [("A", 5)])
        stock = conn1.execute("SELECT stock FROM products WHERE sku = 'A'").fetchone()[0]
        self.assertEqual(stock, 0)
        conn1.close()
        conn2.close()


if __name__ == "__main__":
    unittest.main()
