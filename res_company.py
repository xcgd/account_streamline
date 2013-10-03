from openerp.osv import osv, fields


class res_company(osv.Model):
    _name = "res.company"
    _inherit = "res.company"

    _columns = {
        'message_voucher_draft': fields.text('Message Voucher Draft'),
        'message_voucher_validate': fields.text('Message Voucher Validate'),
    }
