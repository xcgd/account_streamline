# -*- coding: utf-8 -*-

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
