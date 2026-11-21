# NOTES

Fill in every field below before you submit. We read this file first: a submission with an empty field is not graded.
Write in your own words. If you did not fix something, set Status to `not fixed` and say what you found and tried; that still counts.
Status is one of: `fixed`, `partly fixed`, `not fixed`. Commits: the short hashes of the commits for this item, or `none`.

## 1. Report

> Finance says that on some days the revenue in the daily report is higher than what the payment provider paid out, and a few orders show more money received than their total.

**Status:** fixed

**What I saw:** Same payment was counted two times. Paid amount was 2000 for an order of 1000.

**Root cause:** The payment provider sends the same webhook again if it gets no reply. The code saved every copy. It did not check the payment id.

**Fix and why:** Before saving, the code checks if this id is already saved. If yes, it does nothing. This is in payments.py.

**How I verified it:** I made a test that sends the same event two times. The old code gave 2000, the new code gives 1000. Test: test_report1_repeated_webhook_is_counted_once.

**Commits:** d05bd41, 80f6d70

## 2. Report

> Products show as sold out, or nearly, while the shelf is full. Staff say it gets worse on days when many customers abandon checkout.

**Status:** fixed

**What I saw:** After a customer cancelled a pending order, the stock stayed low. I reserved 4 of 10, cancelled, and stock was 6 instead of 10.

**Root cause:** Stock is taken when the order is created. But cancel gave stock back only for paid orders. Abandoned checkouts are still pending, so their stock was lost forever.

**Fix and why:** Every cancelled order now gives its stock back (orders.py).

**How I verified it:** Test test_report2_cancelling_pending_order_returns_stock

**Commits:** 017d9a6, 80f6d70

## 3. Report

> Customers in taxed regions who used a coupon say the tax on their receipt is too high. Receipts without a coupon are right.

**Status:** fixed

**What I saw:** After a customer cancelled a pending order, the stock stayed low. I reserved 4 of 10, cancelled, and stock was 6 instead of 10.

**Root cause:** Tax was worked out on the price before the coupon discount.

**Fix and why:** Discount first, then tax on the lower price (pricing.py). Example: a 1000 order in CA with a 10% coupon now has tax 65, not 73.

**How I verified it:** Test test_report3_tax_is_on_the_discounted_price.

**Commits:** c5e7ea6, 80f6d70

## 4. Report

> Our shop in India (UTC+5:30) says sales taken in the morning do not appear in that day's report and turn up under the day before.

**Status:** fixed

**What I saw:** After a customer cancelled a pending order, the stock stayed low. I reserved 4 of 10, cancelled, and stock was 6 instead of 10.

**Root cause:** India is 5:30 ahead of UTC. The code added the offset when it should subtract it, so the day started at the wrong time. This was a + that should be - (reports.py).

**Fix and why:** Discount first, then tax on the lower price (pricing.py). Example: a 1000 order in CA with a 10% coupon now has tax 65, not 73.

**How I verified it:** Two tests, test_report4_day_bounds_for_utc_plus_530 and test_report4_morning_sale_in_india_is_in_that_days_report.

**Commits:** 7a377e3, 80f6d70

## 5. Report

> Ever since we started running two server workers, we have sold more units of an item than we had, and its stock went negative.

**Status:** fixed

**What I saw:** After a customer cancelled a pending order, the stock stayed low. I reserved 4 of 10, cancelled, and stock was 6 instead of 10.

**Root cause:** Each worker keeps its own saved copy of the stock. The code checked that old copy, and then subtracted. Two workers could both sell the last units.

**Fix and why:** One database command checks and subtracts together, so the saved copy isn't used (catalog.py).

**How I verified it:** Test test_report5_two_workers_cannot_oversell. The old code ended with stock -5.

**Commits:** f11fe3e, 80f6d70

## 6. Open question

> Open question from support, no single right answer: sometimes a customer really does pay twice for one order (two separate payments, not a retry of the same one). Today the system records both and says nothing. Decide what should happen, build the smallest version of your decision, and explain what it costs in `NOTES.md`.

**My decision:** TODO: fill in

**Why:** TODO: fill in

**What it costs:** TODO: fill in

**What I built:** TODO: fill in

**How I verified it:** TODO: fill in

**Commits:** TODO: fill in

## Other things I noticed

Problems outside the reports: what, where, and whether you fixed them. Write `none` if there were none.

TODO: fill in

## Session logs

Which AI tools you used, and one line per file in `session_logs/`.

TODO: fill in
