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

**My decision:** If the same order gets a second, different payment, the system keeps both payments and flags the order for a refund. It does not reject the payment and it does not refund automatically.

**Why:** The money really arrived, so it must be recorded. If I rejected the second payment, the money would be taken from the customer but we would have no record of it. An automatic refund is risky, because some customers may pay twice on purpose, and a wrong refund loses money. So a person checks it and decides.

**What it costs:** A person has to look at the flags and refund by hand. The customer waits until someone does this. This version has no button to mark a flag as "refunded", so the list only grows. The daily report still counts the extra money until it is refunded. Also, only the extra amount is flagged, so if the customer paid in parts, I flag only the part above the order total.

**What I built:** A new table `refund_flags` in `db.py`. In `payments.py`, when the total received is more than the order total, the extra amount is saved as a flag. This is in the same transaction as the payment. A repeated webhook with the same id is ignored, so it is never flagged twice. In `api.py`, I added `GET /refund-flags`, so support can see the list.

**How I verified it:** I wrote 5 tests in `tests/test_report6.py`: a single payment gives no flag, a second payment is kept and flagged, a repeated webhook is not flagged again, only the extra part is flagged when paid in parts, and the flags show in the API. All 13 older tests and these tests pass.

**Commits:** 86fe932

## Other things I noticed

Problems outside the reports: what, where, and whether you fixed them. Write `none` if there were none.

- Product price is saved separately in each worker. If the price changes in one worker, the other worker may still use the old price. I did not fix this.
- cancel reads the order status before it starts its transaction, so two cancels at the same time could give the stock back twice. I did not fix this.
- A bad JSON body can crash server.py. I did not fix this.
- A payment for a cancelled order is rejected, so the provider keeps retrying while the customer's money may already be taken. I did not fix this.

## Session logs

Which AI tools you used, and one line per file in `session_logs/`.

Tool used: Claude (claude.ai chat). No other AI tool.

- session_logs/claude_session.md: the full conversation with Claude about this assignment, from the first message to the last.

My folder had no git repository, so the git commits were created with two helper scripts written by Claude (make_commits.py and add_report6.py). They contain the same fixes described above.
