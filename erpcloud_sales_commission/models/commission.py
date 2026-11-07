from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class CommissionPlan(models.Model):
    _name = 'ep.commission.plan'
    _description = 'Commission Plan'
    _order = 'date_from desc, id desc'
    _check_company_auto = True

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    date_from = fields.Date(required=True, default=fields.Date.today)
    date_to = fields.Date()
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')], default='draft', required=True)
    recognition = fields.Selection([('posted', 'Posted invoice'), ('paid', 'Fully paid invoice')], default='posted', required=True)
    rule_ids = fields.One2many('ep.commission.rule', 'plan_id', string='Rates')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for plan in self:
            if plan.date_to and plan.date_to < plan.date_from:
                raise ValidationError(_('End date must be on or after start date.'))

    @api.constrains('state', 'company_id', 'user_id', 'date_from', 'date_to')
    def _check_overlap(self):
        for plan in self.filtered(lambda p: p.state == 'active'):
            others = self.search([('id', '!=', plan.id), ('state', '=', 'active'),
                                  ('company_id', '=', plan.company_id.id), ('user_id', '=', plan.user_id.id)])
            for other in others:
                if (not plan.date_to or other.date_from <= plan.date_to) and (not other.date_to or plan.date_from <= other.date_to):
                    raise ValidationError(_('Active plans for one salesperson cannot overlap.'))

    def action_activate(self):
        self.write({'state': 'active'})

    def action_archive(self):
        self.write({'state': 'archived'})


class CommissionRule(models.Model):
    _name = 'ep.commission.rule'
    _description = 'Commission Rate Rule'
    _order = 'id'

    plan_id = fields.Many2one('ep.commission.plan', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='plan_id.company_id', store=True)
    scope = fields.Selection([('product', 'Product'), ('category', 'Category'), ('default', 'Default')], required=True, default='default')
    product_id = fields.Many2one('product.product')
    category_id = fields.Many2one('product.category')
    rate = fields.Float(required=True, digits=(6, 4))

    @api.constrains('scope', 'product_id', 'category_id', 'rate', 'plan_id')
    def _check_rule(self):
        for rule in self:
            if not 0 <= rule.rate <= 100:
                raise ValidationError(_('Rate must be between 0 and 100.'))
            if rule.scope == 'product' and not rule.product_id or rule.scope == 'category' and not rule.category_id:
                raise ValidationError(_('Select a product or category for this rule.'))
            key = [('plan_id', '=', rule.plan_id.id), ('scope', '=', rule.scope), ('id', '!=', rule.id)]
            if rule.scope == 'product':
                key.append(('product_id', '=', rule.product_id.id))
            elif rule.scope == 'category':
                key.append(('category_id', '=', rule.category_id.id))
            if self.search_count(key):
                raise ValidationError(_('Only one rule is allowed for the same scope and target.'))


class CommissionException(models.Model):
    _name = 'ep.commission.exception'
    _description = 'Commission Exception'
    _order = 'id desc'

    move_line_id = fields.Many2one('account.move.line', required=True, ondelete='cascade', index=True)
    move_id = fields.Many2one(related='move_line_id.move_id', store=True)
    company_id = fields.Many2one(related='move_line_id.company_id', store=True)
    reason = fields.Text(required=True)
    state = fields.Selection([('open', 'Open'), ('resolved', 'Resolved')], default='open', required=True)
    resolved_by = fields.Many2one('res.users', readonly=True)
    resolved_at = fields.Datetime(readonly=True)
    resolution_note = fields.Text()

    _line_unique = models.Constraint('UNIQUE(move_line_id)', 'One exception per invoice line.')

    def action_resolve(self):
        for exception in self:
            if not exception.resolution_note:
                raise UserError(_('Write a resolution note before closing an exception.'))
            exception.write({'state': 'resolved', 'resolved_by': self.env.uid, 'resolved_at': fields.Datetime.now()})


class CommissionEntry(models.Model):
    _name = 'ep.commission.entry'
    _description = 'Commission Earning Ledger'
    _order = 'recognition_date desc, id desc'
    _check_company_auto = True

    name = fields.Char(required=True)
    move_line_id = fields.Many2one('account.move.line', readonly=True, index=True, ondelete='restrict')
    move_id = fields.Many2one('account.move', readonly=True, index=True, ondelete='restrict')
    sale_order_id = fields.Many2one('sale.order', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', required=True, index=True)
    company_id = fields.Many2one('res.company', required=True, index=True)
    currency_id = fields.Many2one('res.currency', required=True)
    move_currency_id = fields.Many2one('res.currency')
    base_move_currency = fields.Monetary(currency_field='move_currency_id', readonly=True)
    base_company_currency = fields.Monetary(currency_field='currency_id', readonly=True)
    rate = fields.Float(digits=(6, 4), readonly=True)
    amount = fields.Monetary(currency_field='currency_id', readonly=True)
    recognition_date = fields.Date(required=True, index=True)
    plan_id = fields.Many2one('ep.commission.plan', readonly=True)
    rule_id = fields.Many2one('ep.commission.rule', readonly=True)
    recognition_policy = fields.Selection([('posted', 'Posted'), ('paid', 'Fully paid')], readonly=True)
    entry_type = fields.Selection([('earning', 'Earning'), ('refund', 'Refund'),
                                   ('adjustment', 'Adjustment'), ('reversal', 'Reversal')], required=True)
    source_version = fields.Integer(readonly=True, default=1)
    reversal_of_id = fields.Many2one('ep.commission.entry', readonly=True)
    reason = fields.Text(readonly=True)
    statement_id = fields.Many2one('ep.commission.statement', index=True, ondelete='restrict')

    _line_version_once = models.Constraint('UNIQUE(move_line_id, source_version)', 'This invoice line version already has a commission entry.')

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su or not (self.env.context.get('commission_sync_running') or self.env.context.get('commission_internal_create')):
            raise AccessError(_('Commission entries can only be created by the reconciliation service.'))
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) != {'statement_id'}:
            raise UserError(_('Commission ledger snapshots are immutable. Use an adjustment.'))
        if 'statement_id' in vals and any(e.statement_id.state != 'draft' for e in self if e.statement_id):
            raise UserError(_('An approved statement cannot be changed.'))
        return super().write(vals)

    def unlink(self):
        raise UserError(_('Commission entries cannot be deleted.'))

    @api.model
    def _exception(self, line, reason):
        existing = self.env['ep.commission.exception'].search([('move_line_id', '=', line.id)], limit=1)
        if existing:
            if existing.reason != reason:
                existing.write({'reason': reason, 'state': 'open'})
        else:
            self.env['ep.commission.exception'].create({'move_line_id': line.id, 'reason': reason})

    @api.model
    def _rule_for(self, plan, product):
        rules = plan.rule_ids
        for candidates in (
            rules.filtered(lambda r: r.scope == 'product' and r.product_id == product),
            rules.filtered(lambda r: r.scope == 'category' and r.category_id == product.categ_id),
            rules.filtered(lambda r: r.scope == 'default'),
        ):
            if len(candidates) == 1:
                return candidates
            if len(candidates) > 1:
                return self.env['ep.commission.rule']
        return self.env['ep.commission.rule']

    @api.model
    def _sync_moves(self, moves):
        if self.env.context.get('commission_sync_running'):
            return
        ledger = self.with_context(commission_sync_running=True)
        for move in moves.filtered(lambda m: m.state == 'posted' and m.move_type in ('out_invoice', 'out_refund')):
            lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.price_subtotal)
            previous_entries = ledger.search([('move_line_id', 'in', lines.ids)], order='source_version desc, id desc')
            latest = {}
            for entry in previous_entries:
                latest.setdefault(entry.move_line_id.id, entry)
            reversed_ids = set(ledger.search([('reversal_of_id', 'in', [e.id for e in latest.values()]),
                                              ('entry_type', '=', 'reversal')]).mapped('reversal_of_id').ids)
            exceptions = {e.move_line_id.id: e for e in self.env['ep.commission.exception'].search([
                ('move_line_id', 'in', lines.ids)])}
            plan_cache = {}
            for line in lines:
                previous = latest.get(line.id)
                if previous and previous.id not in reversed_ids:
                    continue
                version = previous.source_version + 1 if previous else 1
                if move.move_type == 'out_refund':
                    ledger._sync_refund(line, version, exceptions.get(line.id))
                else:
                    ledger._sync_invoice(line, version, plan_cache, exceptions.get(line.id))
            if move.move_type == 'out_invoice':
                reversals = self.env['account.move'].search([
                    ('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', 'out_refund')])
                if reversals:
                    ledger.with_context(commission_sync_running=False)._sync_moves(reversals)

    @api.model
    def _sync_invoice(self, line, version=1, plan_cache=None, exception=None):
        orders = line.sale_line_ids.order_id
        users = orders.user_id
        if not orders or len(users) != 1 or not users.id:
            self._exception(line, _('Invoice line must link to sale orders with one salesperson.'))
            return
        move = line.move_id
        invoice_date = move.invoice_date or fields.Date.context_today(self)
        plan_cache = plan_cache if plan_cache is not None else {}
        key = (move.company_id.id, users.id, invoice_date)
        if key not in plan_cache:
            plan_cache[key] = self.env['ep.commission.plan'].search([
                ('company_id', '=', move.company_id.id), ('user_id', '=', users.id), ('state', '=', 'active'),
                ('date_from', '<=', invoice_date), '|', ('date_to', '=', False), ('date_to', '>=', invoice_date),
            ])
        plans = plan_cache[key]
        if not plans:
            return
        if len(plans) != 1:
            self._exception(line, _('More than one commission plan applies.'))
            return
        plan = plans[0]
        if plan.recognition == 'paid' and move.payment_state != 'paid':
            return
        rule = self._rule_for(plan, line.product_id)
        if not rule:
            self._exception(line, _('No commission rate applies to this product.'))
            return
        company_currency = move.company_id.currency_id
        base = move.currency_id._convert(line.price_subtotal, company_currency, move.company_id, invoice_date)
        self.create({
            'name': '%s / %s' % (move.name, line.name or line.product_id.display_name),
            'move_line_id': line.id, 'move_id': move.id, 'sale_order_id': orders[:1].id,
            'partner_id': move.partner_id.id, 'product_id': line.product_id.id,
            'user_id': users.id, 'company_id': move.company_id.id,
            'currency_id': company_currency.id, 'move_currency_id': move.currency_id.id,
            'base_move_currency': line.price_subtotal, 'base_company_currency': base,
            'rate': rule.rate, 'amount': company_currency.round(base * rule.rate / 100),
            'recognition_date': fields.Date.context_today(self), 'plan_id': plan.id,
            'rule_id': rule.id, 'recognition_policy': plan.recognition, 'entry_type': 'earning',
            'source_version': version,
        })
        if exception:
            exception.write({'state': 'resolved', 'resolution_note': _('Resolved by successful reconciliation.'),
                             'resolved_by': self.env.uid, 'resolved_at': fields.Datetime.now()})

    @api.model
    def _sync_refund(self, line, version=1, exception=None):
        move = line.move_id
        original = move.reversed_entry_id
        if not original:
            self._exception(line, _('Credit note is not linked to its original invoice.'))
            return
        candidates = self.search([('move_id', '=', original.id), ('entry_type', '=', 'earning'),
                                  ('product_id', '=', line.product_id.id)])
        candidates = candidates.filtered(lambda e: not self.search_count([
            ('reversal_of_id', '=', e.id), ('entry_type', '=', 'reversal')]))
        if len(candidates) != 1:
            self._exception(line, _('Refund must match exactly one original earning for the product.'))
            return
        source = candidates[0]
        previous_refunds = self.search([('reversal_of_id', '=', source.id), ('entry_type', '=', 'refund')])
        previous_refunds = previous_refunds.filtered(lambda e: not self.search_count([
            ('reversal_of_id', '=', e.id), ('entry_type', '=', 'reversal')]))
        refunded = sum(abs(e.base_company_currency) for e in previous_refunds)
        invoice_date = move.invoice_date or fields.Date.context_today(self)
        company_currency = move.company_id.currency_id
        base = move.currency_id._convert(abs(line.price_subtotal), company_currency, move.company_id, invoice_date)
        if company_currency.compare_amounts(refunded + base, source.base_company_currency) > 0:
            self._exception(line, _('Refund exceeds the original commission base.'))
            return
        self.create({
            'name': '%s / %s' % (move.name, line.name or line.product_id.display_name),
            'move_line_id': line.id, 'move_id': move.id, 'sale_order_id': source.sale_order_id.id,
            'partner_id': move.partner_id.id, 'product_id': line.product_id.id,
            'user_id': source.user_id.id, 'company_id': move.company_id.id,
            'currency_id': company_currency.id, 'move_currency_id': move.currency_id.id,
            'base_move_currency': -abs(line.price_subtotal), 'base_company_currency': -base,
            'rate': source.rate, 'amount': -company_currency.round(base * source.rate / 100),
            'recognition_date': fields.Date.context_today(self), 'plan_id': source.plan_id.id,
            'rule_id': source.rule_id.id, 'recognition_policy': source.recognition_policy,
            'entry_type': 'refund', 'reversal_of_id': source.id, 'source_version': version,
        })
        if exception:
            exception.write({'state': 'resolved', 'resolution_note': _('Resolved by successful reconciliation.'),
                             'resolved_by': self.env.uid, 'resolved_at': fields.Datetime.now()})

    @api.model
    def _reverse_moves(self, moves):
        if not moves:
            return
        originals = self.search([('move_id', 'in', moves.ids), ('entry_type', 'in', ('earning', 'refund'))])
        for source in originals:
            if self.search_count([('reversal_of_id', '=', source.id), ('entry_type', '=', 'reversal')]):
                continue
            self.with_context(commission_internal_create=True).create({
                'name': _('Reversal: %s') % source.name,
                'move_id': source.move_id.id, 'sale_order_id': source.sale_order_id.id,
                'partner_id': source.partner_id.id, 'product_id': source.product_id.id,
                'user_id': source.user_id.id, 'company_id': source.company_id.id,
                'currency_id': source.currency_id.id, 'move_currency_id': source.move_currency_id.id,
                'base_move_currency': -source.base_move_currency,
                'base_company_currency': -source.base_company_currency,
                'rate': source.rate, 'amount': -source.amount,
                'recognition_date': fields.Date.context_today(self), 'plan_id': source.plan_id.id,
                'rule_id': source.rule_id.id, 'recognition_policy': source.recognition_policy,
                'entry_type': 'reversal', 'reversal_of_id': source.id,
                'reason': _('Source invoice was reset to draft or cancelled.'),
            })

    @api.model
    def _cron_sync(self):
        params = self.env['ir.config_parameter'].sudo()
        key = 'erpcloud_sales_commission.last_scanned_move_id'
        last_id = int(params.get_param(key, '0'))
        moves = self.env['account.move'].sudo().search([
            ('id', '>', last_id), ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund'))], order='id', limit=500)
        self.sudo()._sync_moves(moves)
        if moves:
            params.set_param(key, str(moves[-1].id))


class CommissionStatement(models.Model):
    _name = 'ep.commission.statement'
    _description = 'Commission Statement'
    _order = 'date_from desc, id desc'
    _check_company_auto = True

    name = fields.Char(required=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    state = fields.Selection([('draft', 'Draft'), ('rejected', 'Rejected'), ('approved', 'Approved'),
                              ('partially_paid', 'Partially paid'), ('paid', 'Paid')], default='draft', required=True)
    entry_ids = fields.One2many('ep.commission.entry', 'statement_id', readonly=True)
    payout_ids = fields.One2many('ep.commission.payout', 'statement_id', readonly=True)
    amount = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=True)
    paid_amount = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=True)
    due_amount = fields.Monetary(currency_field='currency_id', compute='_compute_totals', store=True)
    approved_by = fields.Many2one('res.users', readonly=True)
    approved_at = fields.Datetime(readonly=True)
    rejection_reason = fields.Text()
    rejected_by = fields.Many2one('res.users', readonly=True)
    rejected_at = fields.Datetime(readonly=True)

    @api.depends('entry_ids.amount', 'payout_ids.amount')
    def _compute_totals(self):
        for statement in self:
            statement.amount = sum(statement.entry_ids.mapped('amount'))
            statement.paid_amount = sum(statement.payout_ids.mapped('amount'))
            statement.due_amount = statement.amount - statement.paid_amount

    @api.constrains('date_from', 'date_to', 'company_id', 'user_id')
    def _check_period(self):
        for statement in self:
            if statement.date_to < statement.date_from:
                raise ValidationError(_('End date must be on or after start date.'))
            others = self.search([('id', '!=', statement.id), ('company_id', '=', statement.company_id.id),
                                  ('user_id', '=', statement.user_id.id), ('date_from', '<=', statement.date_to),
                                  ('date_to', '>=', statement.date_from)])
            if others:
                raise ValidationError(_('Statement periods for this salesperson cannot overlap.'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('state', 'draft') != 'draft' or vals.get('approved_by') for vals in vals_list):
            raise UserError(_('Create a draft statement, then use Approve.'))
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals and not (self.env.su and self.env.context.get('commission_statement_transition')):
            raise UserError(_('Use the approval or payout action to change statement status.'))
        if {'company_id', 'user_id', 'date_from', 'date_to', 'name'}.intersection(vals) and any(s.state != 'draft' for s in self):
            raise UserError(_('Approved statements are locked.'))
        return super().write(vals)

    def action_collect(self):
        for statement in self:
            if statement.state != 'draft':
                raise UserError(_('Only draft statements can collect earnings.'))
            entries = self.env['ep.commission.entry'].search([
                ('company_id', '=', statement.company_id.id), ('user_id', '=', statement.user_id.id),
                ('statement_id', '=', False), ('recognition_date', '>=', statement.date_from),
                ('recognition_date', '<=', statement.date_to)])
            entries.write({'statement_id': statement.id})
            statement.name = '%s / %s / %s' % (statement.user_id.name, statement.date_from, statement.date_to)

    def action_approve(self):
        if not self.env.user.has_group('erpcloud_sales_commission.group_commission_manager'):
            raise AccessError(_('Only commission managers can approve statements.'))
        for statement in self:
            if statement.state != 'draft' or not statement.entry_ids:
                raise UserError(_('Collect earnings before approval.'))
            if statement.user_id == self.env.user:
                raise UserError(_('You cannot approve your own commission statement.'))
            exceptions = self.env['ep.commission.exception'].sudo().search_count([
                ('company_id', '=', statement.company_id.id), ('state', '=', 'open'),
                ('move_id.invoice_date', '>=', statement.date_from),
                ('move_id.invoice_date', '<=', statement.date_to)])
            if exceptions:
                raise UserError(_('Resolve commission exceptions before approval.'))
            statement.sudo().with_context(commission_statement_transition=True).write({
                'state': 'approved', 'approved_by': self.env.uid,
                'approved_at': fields.Datetime.now()})

    def action_reject(self):
        if not self.env.user.has_group('erpcloud_sales_commission.group_commission_manager'):
            raise AccessError(_('Only commission managers can reject statements.'))
        for statement in self:
            if statement.state != 'draft' or not (statement.rejection_reason or '').strip():
                raise UserError(_('Add a rejection reason to a draft statement.'))
            statement.sudo().with_context(commission_statement_transition=True).write({
                'state': 'rejected', 'rejected_by': self.env.uid,
                'rejected_at': fields.Datetime.now()})

    def action_reopen(self):
        if not self.env.user.has_group('erpcloud_sales_commission.group_commission_manager'):
            raise AccessError(_('Only commission managers can reopen rejected statements.'))
        for statement in self:
            if statement.state != 'rejected':
                raise UserError(_('Only rejected statements can be reopened.'))
            statement.sudo().with_context(commission_statement_transition=True).write({'state': 'draft'})

    def action_preview(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url',
                'url': '/report/html/erpcloud_sales_commission.report_statement/%s' % self.id,
                'target': 'new'}

    def action_print(self):
        self.ensure_one()
        return self.env.ref('erpcloud_sales_commission.action_report_commission_statement').report_action(self)

    def action_export(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'ep.commission.report.wizard',
                'view_mode': 'form', 'target': 'new',
                'context': {'default_statement_id': self.id, 'default_company_id': self.company_id.id,
                            'default_user_id': self.user_id.id, 'default_date_from': self.date_from,
                            'default_date_to': self.date_to}}


class CommissionPayout(models.Model):
    _name = 'ep.commission.payout'
    _description = 'Commission Payout Record'
    _order = 'date desc, id desc'

    statement_id = fields.Many2one('ep.commission.statement', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='statement_id.company_id', store=True)
    currency_id = fields.Many2one(related='statement_id.currency_id')
    amount = fields.Monetary(required=True, currency_field='currency_id')
    date = fields.Date(required=True, default=fields.Date.today)
    reference = fields.Char(required=True)
    note = fields.Text()
    recorded_by = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        payouts = super().create(vals_list)
        for payout in payouts:
            if payout.amount <= 0 or payout.statement_id.state not in ('approved', 'partially_paid') or payout.statement_id.due_amount < -payout.currency_id.rounding / 2:
                raise ValidationError(_('Payout must be positive and cannot exceed an approved balance.'))
            payout.statement_id.sudo().with_context(commission_statement_transition=True).state = (
                'paid' if payout.currency_id.is_zero(payout.statement_id.due_amount) else 'partially_paid')
        return payouts

    def write(self, vals):
        if {'amount', 'statement_id', 'date', 'reference'}.intersection(vals):
            raise UserError(_('Payout records are immutable. Record a correcting payout through finance.'))
        return super().write(vals)

    def unlink(self):
        raise UserError(_('Payout records cannot be deleted.'))


class CommissionAdjustment(models.Model):
    _name = 'ep.commission.adjustment'
    _description = 'Commission Adjustment Request'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Salesperson', required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    amount = fields.Monetary(required=True, currency_field='currency_id')
    date = fields.Date(required=True, default=fields.Date.today)
    reason = fields.Text(required=True)
    reference = fields.Char(required=True)
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], default='draft', required=True)
    approved_by = fields.Many2one('res.users', readonly=True)
    entry_id = fields.Many2one('ep.commission.entry', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('state', 'draft') != 'draft' or vals.get('entry_id') for vals in vals_list):
            raise UserError(_('Create a draft adjustment, then use Approve.'))
        return super().create(vals_list)

    def action_approve(self):
        if not self.env.user.has_group('erpcloud_sales_commission.group_commission_manager'):
            raise AccessError(_('Only commission managers can approve adjustments.'))
        for adjustment in self:
            if adjustment.state != 'draft' or not adjustment.reason.strip() or not adjustment.amount:
                raise UserError(_('A nonzero adjustment with a reason is required.'))
            entry = self.env['ep.commission.entry'].sudo().with_context(commission_internal_create=True).create({
                'name': adjustment.reference, 'user_id': adjustment.user_id.id,
                'company_id': adjustment.company_id.id, 'currency_id': adjustment.currency_id.id,
                'move_currency_id': adjustment.currency_id.id, 'base_move_currency': 0,
                'base_company_currency': 0, 'amount': adjustment.amount,
                'recognition_date': adjustment.date, 'entry_type': 'adjustment',
                'reason': adjustment.reason,
            })
            adjustment.sudo().with_context(commission_adjustment_approval=True).write({
                'state': 'approved', 'approved_by': self.env.uid, 'entry_id': entry.id})

    def write(self, vals):
        if 'state' in vals and not (self.env.su and self.env.context.get('commission_adjustment_approval')):
            raise UserError(_('Use Approve adjustment to create the ledger entry.'))
        if {'amount', 'company_id', 'user_id', 'date', 'reason', 'reference'}.intersection(vals) and any(a.state == 'approved' for a in self):
            raise UserError(_('Approved adjustments are locked.'))
        return super().write(vals)
