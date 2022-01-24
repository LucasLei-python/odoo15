# -*- coding: utf-8 -*-
{
    'name': "Sales周报月报",

    'summary': """
        ERP Sales周报月报模块""",

    'description': """
        Sales周报月报
    """,

    'author': "Lucas",
    'website': "http://crm.szsunray.com:9020",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'auth_oauth','xl_crm'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}