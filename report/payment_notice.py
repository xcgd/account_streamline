# -*- coding: utf-8 -*-

from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class payment_notice_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payment_notice_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'message': self.get_message,
            'sepa_generated': self.sepa_generated,
        })

    def get_message(self, this_br):
       company = this_br.partner_id.bank_ids.company_id
       if this_br.state == 'draft':
           return company.message_voucher_draft
       if this_br.state == 'posted':
           return company.message_voucher_validate

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
