"""Report 6: a customer who pays twice for one order is flagged for a refund."""
import unittest

from tillpoint import db
from tillpoint.api import App


def event(event_id, order_id, amount):
    return {"id": event_id, "type": "payment.succeeded", "order_id": order_id, "amount_cents": amount}


class PaidTwiceTest(unittest.TestCase):
    def setUp(self):
        self.app = App(db.connect())
        self.app.catalog.add_product("A", "Apple", 1000, 10)
        self.order = self.app.orders.create("bob", [("A", 1)])
        self.total = self.order["total_cents"]

    def test_single_payment_is_not_flagged(self):
        self.app.payments.handle_event(event("e1", self.order["id"], self.total))
        self.assertEqual(self.app.payments.refund_flags(), [])

    def test_second_payment_is_kept_and_flagged(self):
        pay = self.app.payments
        pay.handle_event(event("e1", self.order["id"], self.total))
        self.assertEqual(pay.handle_event(event("e2", self.order["id"], self.total)), "paid")
        self.assertEqual(pay.paid_cents(self.order["id"]), 2 * self.total)   # both payments are recorded
        flags = pay.refund_flags()
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["order_id"], self.order["id"])
        self.assertEqual(flags[0]["amount_cents"], self.total)

    def test_retry_of_the_second_payment_is_not_flagged_again(self):
        pay = self.app.payments
        pay.handle_event(event("e1", self.order["id"], self.total))
        pay.handle_event(event("e2", self.order["id"], self.total))
        pay.handle_event(event("e2", self.order["id"], self.total))          # provider retry
        self.assertEqual(len(pay.refund_flags()), 1)

    def test_only_the_extra_part_is_flagged(self):
        pay = self.app.payments
        pay.handle_event(event("e1", self.order["id"], 600))
        pay.handle_event(event("e2", self.order["id"], self.total))          
        flags = pay.refund_flags()
        self.assertEqual([f["amount_cents"] for f in flags], [600])

    def test_flags_are_visible_in_the_api(self):
        self.app.handle("POST", "/webhooks/payments", event("e1", self.order["id"], self.total))
        self.app.handle("POST", "/webhooks/payments", event("e2", self.order["id"], self.total))
        status, body = self.app.handle("GET", "/refund-flags")
        self.assertEqual(status, 200)
        self.assertEqual(body["flags"][0]["amount_cents"], self.total)


if __name__ == "__main__":
    unittest.main()
