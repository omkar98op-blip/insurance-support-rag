---
article_id: KB-005
title: Recurring payment failures
category: billing
product: Billing Portal
last_reviewed: 2026-04-07
---
# Recurring payment failures

When an autopay attempt fails, the system retries twice: at 3 days and at 7 days after the original due date.

After the third failure the policy enters GRACE status for 10 days. A cancellation notice is issued on day 11.

Common failure reasons:
- Insufficient funds — retry succeeds in most cases once funds are available.
- Expired card — the customer must update the payment method; retries will not succeed.
- Bank block on recurring merchants — the customer must authorise the merchant with their bank.

A payment made during GRACE status restores the policy immediately with no lapse in coverage. A payment made after cancellation requires reinstatement, which is not guaranteed.
