# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################
{
    "name" : "account_streamline",
    "version" : "0.1",
    "author" : "XCG Consulting",
    "category": 'Accounting',
    "description": """Enhancements to the account module to streamline its
    usage.
    """,
    'website': 'http://www.openerp-experts.com',
    'init_xml': [],
    "depends" : ['base', 'account_accountant'],
    "data": [
        'account_move_line_search_unreconciled.xml',
        'account_move_line_tree.xml',
    ],
    #'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    #'certificate': '0080331923549',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
