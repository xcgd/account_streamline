from openerp.osv import osv, fields


class res_company(osv.Model):
    _name = "res.company"
    _inherit = "res.company"

    _columns = {
        'message_voucher_validate': fields.text(
            'Message Voucher Validate',
            help="""This message will be print in the voucher payment report.
            You can print the iban using `$iban` and the date of the payment
            with `$date`."""
        ),
    }
