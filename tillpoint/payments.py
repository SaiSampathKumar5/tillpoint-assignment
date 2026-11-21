"""Payment provider webhooks. The provider retries a delivery until it gets a 2xx, so events can repeat."""
from . import db


class PaymentError(Exception):
    pass


class Payments:
    def __init__(self, conn):
        self.conn = conn

    def handle_event(self, event, now=None):
        """event: dict(id, type, order_id, amount_cents). Returns the order's status after the event."""
        if event.get("type") != "payment.succeeded":
            return None
        order = self.conn.execute("SELECT * FROM orders WHERE id = ?", (event["order_id"],)).fetchone()
        if order is None:
            raise PaymentError(f"payment for unknown order {event['order_id']}")
        if order["status"] == "cancelled":
            raise PaymentError(f"order {order['id']} is cancelled")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            # The provider retries a delivery until it gets a 2xx, so the same event id can arrive again.
            # If we already stored this event id, do nothing and just report the order's current status.
            seen = self.conn.execute("SELECT 1 FROM payments WHERE event_id = ?", (event["id"],)).fetchone()
            if seen is not None:
                self.conn.execute("COMMIT")
                return self.conn.execute("SELECT status FROM orders WHERE id = ?", (order["id"],)).fetchone()["status"]
            self.conn.execute(
                "INSERT INTO payments (order_id, event_id, amount_cents, received_at) VALUES (?, ?, ?, ?)",
                (order["id"], event["id"], event["amount_cents"], db.to_iso(now or db.utcnow())),
            )
            status = self.conn.execute("SELECT status FROM orders WHERE id = ?", (order["id"],)).fetchone()["status"]
            if status == "pending" and self.paid_cents(order["id"]) >= order["total_cents"]:
                self.conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order["id"],))
                status = "paid"
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return status

    def paid_cents(self, order_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS paid FROM payments WHERE order_id = ?", (order_id,)
        ).fetchone()
        return row["paid"]
