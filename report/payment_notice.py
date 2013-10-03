# -*- coding: utf-8 -*-

from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class payment_notice_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payment_notice_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'format_amount': self.format_amount,
            'message': self.get_message,
            'sepa_generated': self.sepa_generated,
        })

    def format_amount(self, amount, br):
        # little check
        if not amount:
            return ''
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
       company = this_br.partner_id.bank_ids.company_id
       if this_br.state == 'draft':
           print company.message_voucher_draft
       if this_br.state == 'posted':
           print company.message_voucher_validate

    def sepa_generated(self, this_br):
        if this_br.batch_id:
            return True
        return False

class payment_notice_report(WebKitParser):
    pass


payment_notice_report('report.account_streamline.payment_notice',
               'account.voucher',
               'addons/account_streamline/report'
               '/payment_notice.mako',
               parser=payment_notice_parser)
