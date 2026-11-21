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
            paid = self.paid_cents(order["id"])
            if status == "pending" and paid >= order["total_cents"]:
                self.conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order["id"],))
                status = "paid"
            # A second, different payment for the same order: keep it (the money really arrived),
            # but flag the extra amount so a person can refund it.
            already_flagged = self.conn.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) AS n FROM refund_flags WHERE order_id = ?", (order["id"],)
            ).fetchone()["n"]
            extra = paid - order["total_cents"] - already_flagged
            if extra > 0:
                self.conn.execute(
                    "INSERT INTO refund_flags (order_id, event_id, amount_cents, flagged_at) VALUES (?, ?, ?, ?)",
                    (order["id"], event["id"], extra, db.to_iso(now or db.utcnow())),
                )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return status

    def refund_flags(self):
        """Orders that received more money than their total. Support refunds these by hand."""
        rows = self.conn.execute(
            "SELECT order_id, event_id, amount_cents, flagged_at FROM refund_flags ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def paid_cents(self, order_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS paid FROM payments WHERE order_id = ?", (order_id,)
        ).fetchone()
        return row["paid"]
