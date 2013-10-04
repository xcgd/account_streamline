# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class payment_notice_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payment_notice_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'debit_credit': self.get_debit_credit,
            'format_amount': self.format_amount,
            'message': self.get_message,
            'sepa_generated': self.sepa_generated,
        })

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

    def get_message(self, this_br):
       company = this_br.company_id
       if not company:
           return ''
       iban = this_br.partner_bank_id.acc_number
       date = this_br.date
       if this_br.state == 'posted':
           return company.message_voucher_validate.replace('$iban', iban).replace('$date', str(date))
       return ''

    def sepa_generated(self, this_br):
        if this_br.batch_id:
            return True
        return False

class payment_notice_report(WebKitParser):
    def remove_previous(self, cr, uid, ids, context=None):
        # get attachement model
        ir_att_osv = pooler.get_pool(cr.dbname).get('ir.attachment')
        # previous ids
        data_ids = ir_att_osv.search(
            cr,
            uid,
            [('res_model', '=', 'account.voucher'),
             ('res_id', 'in', ids)],
            context=context)
        # remove previous items
        ir_att_osv.unlink(cr, uid, data_ids)

    def create(self, cr, uid, ids, datas, context=None):
        # remove previous items
        self.remove_previous(cr, uid, ids, context=context)
        # call parent
        return super(payment_notice_report, self).create(cr, uid, ids, datas, context)


payment_notice_report('report.account_streamline.payment_notice',
               'account.voucher',
               'addons/account_streamline/report'
               '/payment_notice.mako',
               parser=payment_notice_parser)
