# -*- coding: utf-8 -*-


from odoo.osv.expression import AND
from datetime import timedelta
import pytz
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = "pos.order"

    commision_percentage = fields.Float(string='Comision %', related='employee_id.commision_percentage')
    commision_value = fields.Float(compute='compute_commision', string='Comision', store=True)
    cost_value = fields.Float(compute='compute_commision', string='Coste', store=True)

    @api.depends('commision_percentage', 'lines')
    def compute_commision(self):
        for order in self:
            order.commision_value = sum(order.lines.mapped('commision_value'))
            order.cost_value = sum(order.lines.mapped('cost_subtotal'))

    def write(self, vals):
        for order in self:
            if vals.get('state') and vals['state'] == 'paid' and order.name == '/':
                vals['name'] = order.config_id.sequence_id._next()
                for line in order.lines:
                    line.sudo()._purchase_service_generation()
        return super(PosOrder, self).write(vals)

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    # ashcode
    commision_percentage = fields.Float(compute='compute_x', string='X', store=True)
    commision_value = fields.Float(compute='compute_commision', string='Comision', store=True)
    cost_unitario = fields.Float(compute='compute_cost_unitario', string='Coste Unitario', store=True)
    cost_subtotal = fields.Float(compute='compute_cost_subtotal', string='Coste Subtotal', store=True)
    # ashcode ####
    user_id = fields.Many2one('res.users', string='Salesperson')
    commision_percentage_group = fields.Many2one(string='Comision Group', related="user_id.department_id")
    product_commision_staf = fields.Float(string='Comision P', related='product_id.x_comision_staf')
    product_commision_agency = fields.Float(string='Comision P', related='product_id.x_comision_agency')
    product_commision_ventas = fields.Float(string='Comision P', related='product_id.x_comision_ventas')
    sell_utility = fields.Float(compute='compute_sell_utility', string='Utilidad', store=True)

    @api.depends('user_id', 'commision_percentage_group', 'product_commision_agency', 'product_commision_ventas', 'product_commision_staf' )
    def compute_x(self):
        for line in self:
            department = line.user_id.department_id.name
            if department == "Agencia":
                line.commision_percentage = line.product_commision_agency
            elif department == "Ventas":
                line.commision_percentage = line.product_commision_ventas
            else:
                line.commision_percentage = line.product_commision_staf

    @api.depends('commision_percentage', 'price_subtotal')
    def compute_commision(self):
        for line in self:
            line.commision_value = line.commision_percentage * (line.price_subtotal - line.cost_subtotal) / 100

    @api.depends('commision_percentage', 'price_subtotal')
    def compute_commision(self):
        for line in self:
            line.commision_value = line.commision_percentage * (line.price_subtotal-line.cost_subtotal)/100

    @api.depends('price_subtotal', 'cost_subtotal')
    def compute_sell_utility(self):
        for line in self:
            line.sell_utility = line.price_subtotal-line.cost_subtotal

    @api.depends('product_id')
    def compute_cost_unitario(self):
        for line in self:
            line.cost_unitario = line.product_id.standard_price

    @api.depends('product_id','cost_unitario')
    def compute_cost_subtotal(self):
        for line in self:
            line.cost_subtotal = line.cost_unitario * line.qty

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        """ Returns the values to create the purchase order line from the current SO line.
            :param purchase_order: record of purchase.order
            :rtype: dict
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        self.ensure_one()
        # compute quantity from SO line UoM
        product_quantity = self.qty
        if quantity:
            product_quantity = quantity

        purchase_qty_uom = self.product_uom_id._compute_quantity(product_quantity, self.product_id.uom_po_id)

        # determine vendor (real supplier, sharing the same partner as the one from the PO, but with more accurate informations like validity, quantity, ...)
        # Note: one partner can have multiple supplier info for the same product
        supplierinfo = self.product_id._select_seller(
            partner_id=purchase_order.partner_id,
            quantity=purchase_qty_uom,
            date=purchase_order.date_order and purchase_order.date_order.date(), # and purchase_order.date_order[:10],
            uom_id=self.product_id.uom_po_id
        )
        fpos = purchase_order.fiscal_position_id
        taxes = fpos.map_tax(self.product_id.supplier_taxes_id) if fpos else self.product_id.supplier_taxes_id
        if taxes:
            taxes = taxes.filtered(lambda t: t.company_id.id == self.company_id.id)

        # compute unit price
        price_unit = 0.0
        if supplierinfo:
            price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.price, self.product_id.supplier_taxes_id, taxes, self.company_id)
            if purchase_order.currency_id and supplierinfo.currency_id != purchase_order.currency_id:
                price_unit = supplierinfo.currency_id.compute(price_unit, purchase_order.currency_id)

        # purchase line description in supplier lang
        product_in_supplier_lang = self.product_id.with_context(
            lang=supplierinfo.name.lang,
            partner_id=supplierinfo.name.id,
        )
        name = '[%s] %s' % (self.product_id.default_code, product_in_supplier_lang.display_name)
        if product_in_supplier_lang.description_purchase:
            name += '\n' + product_in_supplier_lang.description_purchase

        return {
            'name': '[%s] %s' % (self.product_id.default_code, self.name) if self.product_id.default_code else self.name,
            'product_qty': purchase_qty_uom,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': fields.Date.from_string(purchase_order.date_order) + relativedelta(days=int(supplierinfo.delay)),
            'taxes_id': [(6, 0, taxes.ids)],
            'order_id': purchase_order.id,
        }

    def _purchase_service_create(self, quantity=False):
        """ On Sales Order confirmation, some lines (services ones) can create a purchase order line and maybe a purchase order.
            If a line should create a RFQ, it will check for existing PO. If no one is find, the SO line will create one, then adds
            a new PO line. The created purchase order line will be linked to the SO line.
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        PurchaseOrder = self.env['purchase.order']
        supplier_po_map = {}
        sale_line_purchase_map = {}
        for line in self:
            line = line.with_context(force_company=line.company_id.id)
            # determine vendor of the order (take the first matching company and product)
            suppliers = line.product_id.with_context(force_company=line.company_id.id)._select_seller(
                quantity=line.qty, uom_id=line.product_id.uom_id)
            if not suppliers:
                return False
                # raise UserError(_("There is no vendor associated to the product %s. Please define a vendor for this product.") % (line.product_id.display_name,))

            supplierinfo = suppliers[0]
            partner_supplier = supplierinfo.name  # yes, this field is not explicit .... it is a res.partner !

            # determine (or create) PO
            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = PurchaseOrder.search([
                    ('partner_id', '=', partner_supplier.id),
                    ('state', '=', 'draft'),
                    ('company_id', '=', line.company_id.id),
                ], limit=1)
            if not purchase_order:
                values = line._purchase_service_prepare_order_values(supplierinfo)
                purchase_order = PurchaseOrder.create(values)
            else:  # update origin of existing PO
                so_name = line.order_id.pos_reference
                origins = []
                if purchase_order.origin:
                    origins = purchase_order.origin.split(', ') + origins
                if so_name not in origins:
                    origins += [so_name]
                    purchase_order.write({
                        'origin': ', '.join(origins)
                    })
            supplier_po_map[partner_supplier.id] = purchase_order

            # add a PO line to the PO
            values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
            purchase_line = line.env['purchase.order.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
            sale_line_purchase_map[line] |= purchase_line
        return sale_line_purchase_map

    def _purchase_service_generation(self):
        """ Create a Purchase for the first time from the sale line. If the SO line already created a PO, it
            will not create a second one.
        """
        sale_line_purchase_map = {}
        for line in self:
            # Do not regenerate PO line if the SO line has already created one in the past (SO cancel/reconfirmation case)
            if line.product_id.service_to_purchase:
                result = line._purchase_service_create()
                if result:
                    sale_line_purchase_map.update(result)
        return sale_line_purchase_map

    def _purchase_service_prepare_order_values(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """
        self.ensure_one()
        partner_supplier = supplierinfo.name
        fiscal_position_id = self.env['account.fiscal.position'].sudo().get_fiscal_position(partner_supplier.id)
        return {
            'partner_id': partner_supplier.id,
            'partner_ref': partner_supplier.ref,
            'company_id': self.company_id.id,
            'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
            'dest_address_id': False, # False since only supported in stock
            'origin': self.order_id.pos_reference,
            'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
            'fiscal_position_id': fiscal_position_id,
        }

class ReportSaleDetails(models.AbstractModel):

    _inherit = 'report.point_of_sale.report_saledetails'
    _description = 'Point of Sale Details'

    user_id = fields.Many2one('res.users', string='Salesperson')
    x_seller_ids = fields.Many2many('hr.employee', string='Salespersons')
    # sell_utility = fields.Many2one('pos.order.line', string='Met. Pago')

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, employee_ids=False, x_seller_ids=False):
        """ Serialise the orders of the requested time period, configs and sessions.

        :param date_start: The dateTime to start, default today 00:00:00.
        :type date_start: str.
        :param date_stop: The dateTime to stop, default date_start + 23:59:59.
        :type date_stop: str.
        :param config_ids: Pos Config id's to include.
        :type config_ids: list of numbers.
        :param session_ids: Pos Config id's to include.
        :type session_ids: list of numbers.

        :returns: dict -- Serialised sales.
        """
        domain = [('state', 'in', ['paid','invoiced','done'])]

        if (session_ids):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                [('date_order', '>=', fields.Datetime.to_string(date_start)),
                ('date_order', '<=', fields.Datetime.to_string(date_stop))]
            ])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        if employee_ids:
            domain = AND([domain, [('employee_id', 'in', employee_ids)]])

        orders = self.env['pos.order'].search(domain)

        user_currency = self.env.company.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id, line.sell_utility, line.user_id, line.price_unit, line.discount,line.cost_unitario, order.employee_id,line.commision_percentage, line.commision_value)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount':0.0, 'base_amount':0.0})
                        taxes[tax['id']]['tax_amount'] += tax['amount']
                        taxes[tax['id']]['base_amount'] += tax['base']
                else:
                    taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount':0.0, 'base_amount':0.0})
                    taxes[0]['base_amount'] += line.price_subtotal_incl

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment,
                     pos_payment_method AS method
                WHERE payment.payment_method_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
            """, (tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []

        return {
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': sorted([{
                'sell_utility': sell_utility,
                'date_order': order.date_order,
                'product_id': product.id,
                'user_id': user_id.name,
                'product_name': product.name,
                'code': product.default_code,
                'commision_value': commision_value,
                'commision_percentage': commision_percentage,
                'employee_id': employee_id.name,
                'quantity': qty,
                'price_unit': price_unit,
                'cost_unitario': cost_unitario,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, sell_utility, user_id, price_unit, discount, cost_unitario, employee_id, commision_percentage, commision_value), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        employee_ids = self.env['hr.employee'].browse(data['employee_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids, False, employee_ids.ids))
        return data