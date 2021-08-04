# -*- coding: utf-8 -*-
{
    'name': 'POS Salesperson',
    'version': '12.0',
    'author': 'Preway IT Solutions',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'summary': 'This apps helps you set salesperson on pos orderline from pos interface | Assign Sales Person on POS | POS Sales Person',
    'description': """
- Odoo POS Orderline user
- Odoo POS Orderline salesperson
- Odoo POS Salesperson
- Odoo POS Item Salesperson
- Odoo POS Item User
- Odoo POS product salesperson
    """,
    'data': [
        'views/pos_assets.xml',
        'views/pos_config_view.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'price': 25.0,
    'currency': "EUR",
    'application': True,
    'installable': True,
    'live_test_url': 'https://youtu.be/xnM8rchcD2o',
    "images":["static/description/Banner.png"],
}
