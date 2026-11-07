import io
from html import escape

import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import BinaryBytes


class CommissionReportWizard(models.TransientModel):
    _name = 'ep.commission.report.wizard'
    _description = 'Commission Report Preview and Excel Export'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Salesperson')
    date_from = fields.Date(required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(required=True, default=fields.Date.today)
    statement_id = fields.Many2one('ep.commission.statement')
    preview_html = fields.Html(readonly=True)
    xlsx_file = fields.Binary(readonly=True)
    xlsx_filename = fields.Char(readonly=True)

    def _dataset(self):
        self.ensure_one()
        if self.date_to < self.date_from:
            raise UserError(_('End date must be on or after start date.'))
        if self.company_id not in self.env.companies:
            raise UserError(_('This company is not in your allowed companies.'))
        domain = [('company_id', '=', self.company_id.id), ('recognition_date', '>=', self.date_from),
                  ('recognition_date', '<=', self.date_to)]
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.statement_id:
            domain.append(('statement_id', '=', self.statement_id.id))
        entries = self.env['ep.commission.entry'].search(domain, order='recognition_date, move_id, id')
        rows = [{
            'date': e.recognition_date, 'source': e.name,
            'salesperson': e.user_id.name, 'customer': e.partner_id.name or '',
            'product': e.product_id.display_name or '', 'type': dict(e._fields['entry_type'].selection).get(e.entry_type),
            'base': e.base_company_currency, 'rate': e.rate, 'amount': e.amount,
            'reference': e.name,
        } for e in entries]
        return {'rows': rows, 'total': sum(r['amount'] for r in rows),
                'currency': self.company_id.currency_id.name, 'count': len(rows),
                'paid': self.statement_id.paid_amount if self.statement_id else None,
                'due': self.statement_id.due_amount if self.statement_id else None}

    def action_preview(self):
        self.ensure_one()
        data = self._dataset()
        headers = ['Date', 'Invoice / reference', 'Salesperson', 'Customer', 'Product', 'Type', 'Base', 'Rate %', 'Commission']
        cells = []
        for row in data['rows'][:100]:
            values = [str(row['date']), row['source'], row['salesperson'], row['customer'], row['product'], row['type'],
                      f"{row['base']:,.2f}", f"{row['rate']:,.2f}", f"{row['amount']:,.2f}"]
            cells.append('<tr>%s</tr>' % ''.join('<td>%s</td>' % escape(str(v)) for v in values))
        table = '<table class="table table-striped table-sm"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
            ''.join('<th>%s</th>' % escape(h) for h in headers), ''.join(cells))
        more = '<p>%s</p>' % escape(_('Showing first 100 rows; Excel includes every matching row.')) if data['count'] > 100 else ''
        self.preview_html = '<div><h4>%s — %s %s</h4><p>%s: %s</p>%s%s</div>' % (
            escape(_('Commission preview')), data['total'], escape(data['currency']),
            escape(_('Rows')), data['count'], table, more)
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
                'view_mode': 'form', 'target': 'new'}

    def action_export_xlsx(self):
        self.ensure_one()
        data = self._dataset()
        stream = io.BytesIO()
        book = xlsxwriter.Workbook(stream, {'in_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False})
        bold = book.add_format({'bold': True, 'bg_color': '#E6F2EC'})
        money = book.add_format({'num_format': '#,##0.00;[Red]-#,##0.00'})
        day = book.add_format({'num_format': 'yyyy-mm-dd'})
        summary = book.add_worksheet('Summary')
        summary_rows = [
            ('Company', self.company_id.name), ('Salesperson', self.user_id.name if self.user_id else _('All permitted')),
            ('From', str(self.date_from)), ('To', str(self.date_to)), ('Currency', data['currency']),
            ('Rows', data['count']), ('Commission total', data['total']),
            ('Generated at', str(fields.Datetime.now())),
        ]
        if self.statement_id:
            summary_rows += [('Paid', data['paid']), ('Due', data['due'])]
        for idx, (label, value) in enumerate(summary_rows):
            summary.write(idx, 0, label, bold)
            summary.write(idx, 1, value, money if isinstance(value, (int, float)) and label != 'Rows' else None)
        summary.set_column(0, 0, 24)
        summary.set_column(1, 1, 32)
        detail = book.add_worksheet('Details')
        headers = ['Date', 'Invoice / reference', 'Salesperson', 'Customer', 'Product', 'Type',
                   'Base (' + data['currency'] + ')', 'Rate %', 'Commission (' + data['currency'] + ')']
        for col, label in enumerate(headers):
            detail.write(0, col, label, bold)
        for n, row in enumerate(data['rows'], 1):
            detail.write_datetime(n, 0, row['date'], day)
            for col, key in enumerate(('source', 'salesperson', 'customer', 'product', 'type'), 1):
                value = row[key] or ''
                detail.write_string(n, col, "'" + value if value[:1] in '=+-@' else value)
            detail.write_number(n, 6, row['base'], money)
            detail.write_number(n, 7, row['rate'])
            detail.write_number(n, 8, row['amount'], money)
        detail.freeze_panes(1, 0)
        detail.autofilter(0, 0, max(1, data['count']), 8)
        detail.set_column(0, 0, 14)
        detail.set_column(1, 5, 24)
        detail.set_column(6, 8, 20)
        book.close()
        self.write({'xlsx_file': BinaryBytes(stream.getvalue()),
                    'xlsx_filename': 'commission_%s_%s.xlsx' % (self.date_from, self.date_to)})
        return {'type': 'ir.actions.act_url',
                'url': '/web/content?model=ep.commission.report.wizard&id=%s&field=xlsx_file&filename_field=xlsx_filename&download=true' % self.id,
                'target': 'self'}
