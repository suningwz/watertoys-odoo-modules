# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    user_id = fields.Many2one('res.users', string='Salesperson')
    commision_percentage_group = fields.Many2one(string='Comision Group', related="user_id.department_id")