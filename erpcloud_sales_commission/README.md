# Sales Commission Ledger for Odoo 20 Community

Free, source available sales commission accounting for one salesperson per sale order. The module creates its own **Commissions** app. It extends Odoo Sales and Invoicing through ORM hooks, without changing their menus, forms, totals or accounting entries.

## Install

1. Use Odoo 20 Community on Odoo.sh or your own server. Python package `xlsxwriter` must be installed in the Odoo environment.
2. Copy `erpcloud_sales_commission` into an addons path. Update the Apps list and install **Sales Commission Ledger**. Odoo installs the declared `sale` and `account` dependencies.
3. In Settings → Users, assign **Commission Salesperson**, **Commission Manager** or **Commission Finance**. Assign a manager to configure plans.
4. Open **Commissions → Configuration → Plans & Rates**. Create a plan for each salesperson and company, set effective dates, recognition at invoice posting or full customer payment, and add exactly one default rate. Optional product and category rates override the default.

Installation creates no plans, commissions or customer sample data. Sales orders and invoices remain in core Odoo.

## Daily workflow

1. Confirm a sale order with one salesperson, create its customer invoice and post it. The app reads the invoiced line subtotal after discount and before tax. For a full payment plan, the invoice must be fully paid before the earning is created.
2. Open **Commissions → Earnings** to inspect the immutable calculation and its source. When a refund is made through a credit note linked to the original invoice, it creates a negative earning using the original rate. Ambiguous source lines appear in **Configuration → Exceptions**.
3. A manager creates a statement for one salesperson, company and period; clicks **Collect earnings** and checks the lines. Resolve open exceptions before **Approve**. Managers cannot approve their own statement.
4. Use **Preview**, **Print PDF**, or **Excel** from the statement. The Excel dialog also previews a filtered table. A Finance user records a payout with date and external reference in **Commissions → Payouts**. Partial payouts keep an outstanding balance.
5. Managers use **Configuration → Adjustments** for signed, reasoned corrections. Existing approved earnings and payouts are not overwritten.

The payout record is an audit record only. It does **not** make a bank transfer, payroll entry, or journal entry.

## Quy trình nhanh (Tiếng Việt)

1. Cài Odoo 20 Community, bổ sung Python `xlsxwriter`, chép thư mục module vào addons path, cập nhật danh sách Apps và cài **Sales Commission Ledger**.
2. Gán nhóm quyền Hoa hồng cho nhân viên, quản lý và kế toán trong Settings → Users.
3. Tại **Commissions → Configuration → Plans & Rates**, lập chính sách theo người bán/công ty/kỳ; chọn ghi nhận khi hóa đơn ghi sổ hoặc khi khách thanh toán đủ. Thêm tỷ lệ mặc định và tỷ lệ riêng cho sản phẩm/nhóm nếu cần.
4. Xác nhận đơn bán và ghi sổ hóa đơn trong Odoo lõi; mở **Earnings** để kiểm tra. Chứng từ không rõ nguồn được đưa vào **Exceptions**.
5. Quản lý tạo **Statements**, gom phát sinh, phê duyệt, xem trước/in PDF/xuất Excel. Kế toán nhập **Payouts** để ghi nhận số đã chi và số còn phải trả.

## Scope and limits

- One salesperson per invoice line; ambiguous multi-owner or unlinked source lines are flagged for review.
- Product → category → default rate priority. One active plan per salesperson/company/date.
- Commission base uses customer invoice lines, not the entire sale order, so partial invoicing is not double counted.
- Refunds need an explicit Odoo reversal link. A refund with multiple matching original product lines is flagged rather than guessed.
- Customer partial payments are not prorated. Only fully paid invoices qualify under that policy.
- No POS, subscriptions, split commission, team tiers, payroll or automatic payment integration in this release.
- Excel download needs `xlsxwriter`. Odoo Online does not accept custom Python modules.

Support: **info@erpcloud.vn**. License: **LGPL-3**. Source ownership: ERPCloud; no third party addon code or images are included.
