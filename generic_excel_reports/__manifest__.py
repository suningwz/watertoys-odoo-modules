# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Global Dynamic Export Excel Reports For all Application in Odoo',
    'version': '12.0.0.5',
    'category': 'Extra Tools',
    'sequence': 4,
    'summary': 'Easy to Export Excel view for all applications i.e CRM,Sales,Purchase,Invoices,Payment,Picking,Customer,Product Etc..',
    'description': """
	 BrowseInfo developed a new odoo/OpenERP module apps.
	 This module use for 
	-Export data in Excel
    Dynamic Global Export Excel Report for modules
    Dynamic Global Export Excel
    Global Export Excel Report
    Dynamic/Global Export Excel Report For all Application-xls
    Dynamic / Global Export Excel Report For all Application-xls
    export data in xls
    xls data export
     global reports
     export reports
     Global Dynamic Export Excel Reports
     Global Export Excel Reports
     Global Export Excel Reports
     Export Excel Reports
     Export data in Excel Reports



	-Global data Export
	-Global Export data for any object.
	-Export Sales Order in Excel, Export Sales data in Excel , Export purchase order in Excel, Export Purchase data in Excel.
	-Export Stock in Excel, Export Product data in Excel, Export Invoice on Excel, Export Product in Excel
	-Dynamic export,export in excel, Excel lead, excel sales order, download sales data, download purchase data, download invoice data
	-BI reporinng
	-Business intelligence, Odoo BI, Accounting Reports
	-XLS reports odoo
	-Odoo xls report
        excel export report on Odoo, Odoo excel export, download excel report, generic export excel report, dynamic excel export report
	reporte de exportacion, تقرير التصدير, Liste exportieren, export rapport, Rapport d'exportation, relatório de exportação, rapporto di esportazione
 
   """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    "price": 17,
    "currency": 'EUR',
    'depends': ['base'],
    'data': [   "security/ir.model.access.csv",
		        "views/generic_excel_report_view.xml",
                "views/template_view.xml"
            ],
	'qweb': [ ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
    'live_test_url':'https://youtu.be/4OzU2mgWKRk',
}
