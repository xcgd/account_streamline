# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013, 2015 XCG Consulting (http://www.xcg-consulting.fr/)
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

from openerp.osv import osv, fields
from openerp.tools.translate import _


class res_company(osv.Model):
    _inherit = "res.company"

    _columns = {
        'remittance_letter_top': fields.text(
            _('Remittance Letter - top message'),
            help=_('Message to write at the top of Remittance Letter '
            'reports. Available variables: "$iban" for the IBAN; "$date" for '
            'the payment date. HTML tags are allowed.'),
            translate=True),

        'remittance_letter_bottom': fields.text(
            _('Remittance Letter - bottom message'),
            help=_('Message to write at the bottom of Remittance Letter '
            'reports. HTML tags are allowed.'),
            translate=True),
        'allow_duplicate_ref_on_account_move_same_account': fields.boolean(
            "Allow duplicate (reference, account) on journals",
            ),
    }

    _defaults = {
        'remittance_letter_top': lambda *a: '''
<p>
Mr / Mrs,
</p>
<p>
We are informing you about the payment of the following invoices by transfer
on your account (IBAN «$iban») on «$date».<br/>
We remain available should you have any query regarding this payment.
</p>
''',
    }
