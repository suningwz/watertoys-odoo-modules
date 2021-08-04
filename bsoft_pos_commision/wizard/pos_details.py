# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    employee_ids = fields.Many2many(
        'hr.employee', string='Cajero')



    def generate_report(self):
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids, 'employee_ids':self.employee_ids.ids}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)
