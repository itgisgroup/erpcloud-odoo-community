import io
import zipfile

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCommission(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Commission Seller', 'login': 'commission.seller.test',
            'group_ids': [(6, 0, [cls.env.ref('erpcloud_sales_commission.group_commission_user').id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Commission Manager Test', 'login': 'commission.manager.test',
            'group_ids': [(6, 0, [cls.env.ref('erpcloud_sales_commission.group_commission_manager').id])],
        })
        cls.finance = cls.env['res.users'].create({
            'name': 'Commission Finance Test', 'login': 'commission.finance.test',
            'group_ids': [(6, 0, [cls.env.ref('erpcloud_sales_commission.group_commission_finance').id])],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Commission Test Buyer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Commission Test Item', 'list_price': 1000.0, 'invoice_policy': 'order',
            'taxes_id': [(5, 0, 0)],
        })
        cls.plan = cls.env['ep.commission.plan'].create({
            'name': 'Standard 5 percent', 'user_id': cls.salesperson.id,
            'date_from': '2020-01-01', 'recognition': 'posted',
            'rule_ids': [(0, 0, {'scope': 'default', 'rate': 5})],
        })
        cls.plan.action_activate()

    def _invoice(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'user_id': self.salesperson.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1,
                                   'price_unit': 1000, 'discount': 10})],
        })
        order.action_confirm()
        move = order._create_invoices()
        move.action_post()
        return move

    def test_posted_and_idempotent(self):
        move = self._invoice()
        entry = self.env['ep.commission.entry'].search([('move_id', '=', move.id)])
        self.assertEqual(len(entry), 1)
        self.assertAlmostEqual(entry.base_company_currency, 900)
        self.assertAlmostEqual(entry.amount, 45)
        entry._sync_moves(move)
        self.assertEqual(self.env['ep.commission.entry'].search_count([('move_id', '=', move.id)]), 1)
        with self.assertRaises(UserError):
            entry.write({'amount': 99})

    def test_statement_and_excel(self):
        move = self._invoice()
        today = fields.Date.today()
        statement = self.env['ep.commission.statement'].create({
            'user_id': self.salesperson.id, 'date_from': today.replace(day=1), 'date_to': today})
        statement.action_collect()
        self.assertAlmostEqual(statement.amount, 45)
        statement.with_user(self.manager).action_approve()
        self.assertEqual(statement.state, 'approved')
        payout = self.env['ep.commission.payout'].with_user(self.finance).create({
            'statement_id': statement.id, 'amount': 20, 'reference': 'BANK-TEST'})
        self.assertEqual(statement.state, 'partially_paid')
        self.assertAlmostEqual(statement.due_amount, 25)
        with self.assertRaises(ValidationError):
            self.env['ep.commission.payout'].with_user(self.finance).create({
                'statement_id': statement.id, 'amount': 30, 'reference': 'OVERPAY'})
        wizard = self.env['ep.commission.report.wizard'].create({
            'company_id': self.env.company.id, 'user_id': self.salesperson.id,
            'date_from': today.replace(day=1), 'date_to': today,
            'statement_id': statement.id})
        data = wizard._dataset()
        self.assertEqual(data['count'], 1)
        self.assertAlmostEqual(data['total'], 45)
        wizard.action_preview()
        self.assertIn('45', wizard.preview_html)
        wizard.action_export_xlsx()
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(wizard.xlsx_file.content)))
        report = self.env.ref('erpcloud_sales_commission.action_report_commission_statement')
        html, _ = report._render_qweb_html(report.report_name, [statement.id])
        self.assertIn(b'45', html)
        self.assertEqual(report.report_type, 'qweb-pdf')
        self.assertIn('/report/html/', statement.action_preview()['url'])

    def test_own_record_access(self):
        move = self._invoice()
        own = self.env['ep.commission.entry'].with_user(self.salesperson)
        self.assertEqual(own.search_count([('move_id', '=', move.id)]), 1)
        other = self.env['res.users'].create({
            'name': 'Other Commission Seller', 'login': 'commission.other.test',
            'group_ids': [(6, 0, [self.env.ref('erpcloud_sales_commission.group_commission_user').id])],
        })
        self.assertEqual(self.env['ep.commission.entry'].with_user(other).search_count([('move_id', '=', move.id)]), 0)
        with self.assertRaises(AccessError):
            self.env['ep.commission.entry'].with_user(other).browse(own.search([('move_id', '=', move.id)]).id).read(['amount'])

    def test_refund_uses_original_rate(self):
        move = self._invoice()
        credit = move._reverse_moves(default_values_list=[{'invoice_date': fields.Date.today()}], cancel=False)
        self.assertEqual(len(credit), 1)
        credit.invoice_line_ids.filtered(lambda l: l.display_type == 'product').write({'price_unit': 200, 'discount': 0})
        credit.action_post()
        refunds = self.env['ep.commission.entry'].search([('move_id', '=', credit.id)])
        self.assertEqual(len(refunds), 1)
        self.assertAlmostEqual(refunds.amount, -10)
        self.assertAlmostEqual(sum(self.env['ep.commission.entry'].search([
            ('move_id', 'in', [move.id, credit.id])]).mapped('amount')), 35)
        refunds._sync_moves(credit)
        self.assertEqual(self.env['ep.commission.entry'].search_count([('move_id', '=', credit.id)]), 1)

    def test_fully_paid_waits(self):
        self.plan.write({'recognition': 'paid'})
        move = self._invoice()
        self.assertFalse(self.env['ep.commission.entry'].search([('move_id', '=', move.id)]))
        bank = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.env.company.id)], limit=1)
        payment = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=move.ids).create({'journal_id': bank.id})
        payment.action_create_payments()
        self.assertEqual(move.payment_state, 'paid')
        self.assertEqual(self.env['ep.commission.entry'].search_count([('move_id', '=', move.id)]), 1)

    def test_product_rule_precedence(self):
        self.env['ep.commission.rule'].create({
            'plan_id': self.plan.id, 'scope': 'product', 'product_id': self.product.id, 'rate': 7})
        move = self._invoice()
        entry = self.env['ep.commission.entry'].search([('move_id', '=', move.id)])
        self.assertAlmostEqual(entry.amount, 63)
        self.assertEqual(entry.rate, 7)

    def test_reset_repost_and_cancel_keep_audit(self):
        move = self._invoice()
        move.button_draft()
        ledger = self.env['ep.commission.entry']
        self.assertAlmostEqual(sum(ledger.search([('move_id', '=', move.id)]).mapped('amount')), 0)
        self.assertEqual(ledger.search_count([('move_id', '=', move.id), ('entry_type', '=', 'reversal')]), 1)
        move.action_post()
        self.assertAlmostEqual(sum(ledger.search([('move_id', '=', move.id)]).mapped('amount')), 45)
        self.assertEqual(ledger.search_count([('move_id', '=', move.id), ('entry_type', '=', 'earning')]), 2)
        move.button_cancel()
        self.assertAlmostEqual(sum(ledger.search([('move_id', '=', move.id)]).mapped('amount')), 0)

    def test_adjustment_and_state_guards(self):
        adjustment = self.env['ep.commission.adjustment'].with_user(self.manager).create({
            'company_id': self.env.company.id, 'user_id': self.salesperson.id,
            'amount': -5, 'date': fields.Date.today(),
            'reason': 'Correction for sample dispute', 'reference': 'CORR-001'})
        with self.assertRaises(UserError):
            adjustment.with_user(self.manager).with_context(commission_adjustment_approval=True).write({'state': 'approved'})
        adjustment.with_user(self.manager).action_approve()
        self.assertEqual(adjustment.entry_id.entry_type, 'adjustment')
        self.assertAlmostEqual(adjustment.entry_id.amount, -5)
        with self.assertRaises(UserError):
            self.env['ep.commission.entry'].with_user(self.manager).create({
                'name': 'FORGED', 'user_id': self.salesperson.id, 'company_id': self.env.company.id,
                'currency_id': self.env.company.currency_id.id, 'amount': 999,
                'recognition_date': fields.Date.today(), 'entry_type': 'adjustment'})
        statement = self.env['ep.commission.statement'].with_user(self.manager).create({
            'user_id': self.salesperson.id, 'date_from': fields.Date.today().replace(day=1),
            'date_to': fields.Date.today()})
        with self.assertRaises(UserError):
            statement.with_user(self.manager).with_context(commission_statement_transition=True).write({'state': 'paid'})

    def test_cross_company_entry_is_hidden(self):
        other_company = self.env['res.company'].create({
            'name': 'Other Commission Company', 'currency_id': self.env.company.currency_id.id})
        entry = self.env['ep.commission.entry'].sudo().with_context(commission_internal_create=True).create({
            'name': 'OTHER-COMPANY-TEST', 'company_id': other_company.id,
            'user_id': self.salesperson.id, 'currency_id': other_company.currency_id.id,
            'amount': 10, 'recognition_date': fields.Date.today(), 'entry_type': 'adjustment'})
        restricted = self.env['ep.commission.entry'].with_user(self.manager)
        self.assertEqual(restricted.search_count([('id', '=', entry.id)]), 0)
        with self.assertRaises(AccessError):
            restricted.browse(entry.id).read(['amount'])

    def test_reject_and_reopen_draft(self):
        statement = self.env['ep.commission.statement'].with_user(self.manager).create({
            'user_id': self.salesperson.id, 'date_from': fields.Date.today().replace(day=1),
            'date_to': fields.Date.today()})
        with self.assertRaises(UserError):
            statement.with_user(self.manager).action_reject()
        statement.with_user(self.manager).rejection_reason = 'Incorrect sales assignment'
        statement.with_user(self.manager).action_reject()
        self.assertEqual(statement.state, 'rejected')
        statement.with_user(self.manager).action_reopen()
        self.assertEqual(statement.state, 'draft')

    def test_currency_conversion_from_invoice(self):
        eur = self.env.ref('base.EUR')
        eur.active = True
        self.env['res.currency.rate'].create({
            'name': fields.Date.today(), 'currency_id': eur.id,
            'company_id': self.env.company.id, 'rate': 2})
        pricelist = self.env['product.pricelist'].create({'name': 'Commission EUR QA', 'currency_id': eur.id})
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'user_id': self.salesperson.id,
            'pricelist_id': pricelist.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1,
                                   'price_unit': 100, 'discount': 10})],
        })
        order.action_confirm()
        move = order._create_invoices()
        move.action_post()
        entry = self.env['ep.commission.entry'].search([('move_id', '=', move.id)])
        self.assertEqual(move.currency_id, eur)
        self.assertAlmostEqual(entry.base_move_currency, 90)
        converted = eur._convert(90, self.env.company.currency_id, self.env.company, move.invoice_date)
        self.assertAlmostEqual(entry.base_company_currency, converted)
        self.assertAlmostEqual(entry.amount, self.env.company.currency_id.round(converted * 0.05))

    def test_excel_escapes_formula_text(self):
        self.partner.name = '=2+2'
        move = self._invoice()
        wizard = self.env['ep.commission.report.wizard'].create({
            'company_id': self.env.company.id, 'user_id': self.salesperson.id,
            'date_from': fields.Date.today().replace(day=1), 'date_to': fields.Date.today()})
        wizard.action_export_xlsx()
        with zipfile.ZipFile(io.BytesIO(wizard.xlsx_file.content)) as book:
            strings = book.read('xl/sharedStrings.xml')
            summary = book.read('xl/worksheets/sheet1.xml')
        self.assertIn(b"'=2+2", strings)
        self.assertIn(b'<v>45</v>', summary)
