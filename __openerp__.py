# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################
{
    "name": "Account Streamline",
    "version": "2.0.1",
    "author": "XCG Consulting",
    "category": 'Accounting',
    "description": """Enhancements to the account module to streamline its
    usage.
    """,
    'website': 'http://www.openerp-experts.com',
    'init_xml': [],
    "depends": [
        'base',
        'account_accountant',
        'account_voucher',
        'account_payment',
        'account_sequence',
        'mail',
        'analytic_structure',
        'advanced_filter',
        'report_webkit',
    ],
    "data": [
        'data/partner_data.xml',
        'wizard/account_reconcile_view.xml',
        'wizard/email_remittance.xml',
        'account_move_line_search_unreconciled.xml',
        'account_move_line_tree.xml',
        'account_move_view.xml',
        'account_view.xml',
        'account_voucher.xml',
        'partner_view.xml',
        'payment_selection.xml',
        'payment_suggestion.xml',
        'account_move_line_journal_items.xml',
        'account_move_line_journal_view.xml',
        'account_menu_entries.xml',
        'res_company.xml',
        'data/voucher_report_header.xml',
        'report/payment_suggestion.xml',
        'report/remittance_letter.xml',
        'data/remittance_letter_email_template.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
    ],
    #'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
