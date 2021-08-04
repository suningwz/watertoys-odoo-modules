# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'BSOFT POS Commision',
    'version' : '1.1',
    'summary': 'POS Commision',
    'sequence': 15,
    'description': """""",
    'category': 'Point of Sale',
    'depends' : ['sale', 'pos_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users.xml',
        'views/pos_commision.xml',
        'wizard/pos_details.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
