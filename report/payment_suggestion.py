# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class payment_suggestion_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payment_suggestion_parser, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_partners': self.get_partners,
            'debit_credit': self.get_debit_credit,
            'format_amount': self.format_amount,
            'title': self.get_title,
        })

    def get_partners(self, sugg_br):
        ''' sugg_br is a payment.suggestion which contains the selected
        vouchers. Group these vouchers by partner then return a list the
        template can iterate on. Compute totals as well. '''

        res = {}
        for voucher in sugg_br.voucher_ids:
            partner = voucher.partner_id
            if partner not in res:
                res[partner] = { 'vouchers': [], 'total': 0 }
            res[partner]['vouchers'].append(voucher)
            res[partner]['total'] += voucher.amount
        return res

    def get_debit_credit(self, br):
        return _('Debit') if br.type == 'debit' else _('Credit')

    def format_amount(self, amount, br):
        # little check
        if not amount:
            return '0.00'
        # shortcut
        position = br.currency_id.position
        symbol = br.currency_id.symbol
        # currency after
        if position == 'after':
            return '%s %s' % (amount, symbol)
        # currency before
        if position == 'before':
            return '%s %s' % (symbol, amount)
        return amount.strip()

    def get_title(self, br):
        return _('Payment Suggestion')


class payment_suggestion_report(WebKitParser):
    def remove_previous(self, cr, uid, ids, context=None):
        # get attachement model
        ir_att_osv = pooler.get_pool(cr.dbname).get('ir.attachment')
        # previous ids
        data_ids = ir_att_osv.search(
            cr,
            uid,
            [('res_model', '=', 'account.streamline.payment.suggestion'),
             ('res_id', 'in', ids)],
            context=context)
        # remove previous items
        ir_att_osv.unlink(cr, uid, data_ids)

    def create(self, cr, uid, ids, datas, context=None):
        # remove previous items
        self.remove_previous(cr, uid, ids, context=context)
        # call parent
        return super(payment_suggestion_report, self).create(
            cr, uid, ids, datas, context)


payment_suggestion_report('report.account_streamline.payment_suggestion',
                          'payment.suggestion',
                          'addons/account_streamline/report/payment_suggestion.mako',
                          parser=payment_suggestion_parser)
