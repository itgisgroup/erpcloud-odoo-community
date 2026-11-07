# Release record — Sales Commission Ledger 20.0.1.0.0

Date: 2026-11-07. Publisher: ERPCloud (`info@erpcloud.vn`). Edition: Odoo 20 Community. License: LGPL-3. Price: Free. Dependencies: Odoo `sale` and `account`, plus `xlsxwriter` from standard Odoo 20 Python requirements.

## Product boundary

Invoice line subtotal after discount and before tax; one salesperson per sale source; plan per salesperson/company/period; product → category → default rate; posted or fully paid recognition; linked credit note reversal; immutable ledger and adjustments; statement approval; manual payout record; on-screen preview, QWeb HTML/PDF and XLSX. No payroll, bank transfer, accounting payout entry, team split or POS.

## QA evidence

- Clean Odoo 20 CE installation and 14 automated cases, 0 failures, 0 errors: `reports/erpcloud_sales_commission-test.log`. Odoo source SHA: `24b59ae7617e6b6ccf466d8b8cfebd541baa8b89`.
- Tests cover actual invoice payment, refund, reset/repost/cancel audit, rule priority, approval and payout, multi-company and user isolation, currency conversion, Excel formula defense and immutable ledger.
- Real 10,000-line invoice: 10,000 ledger entries; create 89.07 s, post/sync 20.36 s, report dataset 0.11 s, XLSX 0.56 s. Evidence: `reports/erpcloud_sales_commission-10k.log`.
- Real browser screenshots at 1440 px and 390 px, no mobile horizontal overflow. Separate English and Vietnamese sample data. Media folder includes actual UI WebM, PDF (`%PDF-1.4`, 37,395 bytes) and XLSX (6,646 bytes) exported from the module.
- Installation and uninstall from a ZIP on a disposable clean CE database succeeded.

## Publication gate

The public Community repository must contain this exact tested package on branch `20.0`. Scan and publish from Odoo Apps dashboard, then verify the anonymous listing and current screenshots. Source push alone does not establish marketplace publication.
