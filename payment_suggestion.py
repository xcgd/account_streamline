# This object stores groups of vouchers the user has selected to get them
# validated. It can store a "Payment Suggestion" report that refers to all the
# vouchers.

from openerp.osv import fields, orm
from openerp.tools.translate import _


class payment_suggestion(orm.TransientModel):
    _name = 'payment.suggestion'

    _columns = {
        'voucher_ids': fields.many2many(
            'account.voucher',
            'payment_suggestion_rel',
            'payment_suggestion_id',
            'voucher_id',
            _('Vouchers')),
    }

    def print_payment_suggestion(self, cr, uid, ids, context=None):
        ''' Create a payment suggestion object then use it to generate (and to
        store) a report. '''

        # The context contains account.voucher references; update it to refer
        # to payment suggestions.
        if 'active_model' in context:
            context['active_model'] = 'account.streamline.payment.suggestion'
        if 'active_ids' in context:
            ids = context['active_ids']
            del context['active_ids']
        if 'active_id' in context:
            del context['active_id']

        sugg_id = self.create(cr, uid,
                              { 'voucher_ids': [(6, 0, ids)] },
                              context=context)

        # The report generator uses "active_ids"...
        context['active_ids'] = [sugg_id]

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_streamline.payment_suggestion',
            'datas': { 'ids': [sugg_id],
                      'model': 'payment.suggestion' },
            'context': context,
        }
