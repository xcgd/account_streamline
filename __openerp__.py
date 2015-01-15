# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Streamline, for OpenERP
#    Copyright (C) 2013 XCG Consulting (http://odoo.consulting)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Account Streamline",
    "version": "1.12",
    "author": "XCG Consulting",
    "category": 'Accounting',
    "description": """Enhancements to the account module to streamline its
    usage.
    """,
    'website': 'http://odoo.consulting/',
    'init_xml': [],
    "depends": [
        'base',
        'account_accountant',
        'account_voucher',
        'account_payment',
        'account_sequence',
        'mail',
        'analytic_structure',
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
