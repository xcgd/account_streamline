# -*- coding: utf-8 -*-

from datetime import datetime

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv

from openerp.addons.report_webkit.webkit_report import WebKitParser


class payment_suggestion_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payment_suggestion_parser, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'date': self.get_date,
            'get_partners': self.get_partners,
            'get_totals': self.get_totals,
            'debit_credit': self.get_debit_credit,
            'get_voucher': self.get_voucher,
            'title': self.get_title,
        })

    def get_date(self):
        return self.formatLang(str(datetime.today()), date_time=True)

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

    def get_totals(self, partners):
        ''' Go through the grouped-by-partner list and compute totals to be
        displayed at the top of the report. '''

        voucher_count = 0
        total = 0
        for partner, partner_details in partners.iteritems():
            for voucher in partner_details['vouchers']:
                voucher_count += len(voucher.line_dr_ids)
            total += partner_details['total']

        return voucher_count, len(partners), total

    def get_debit_credit(self, br):
        return _('Debit') if br.type == 'dr' else _('Credit')

    def get_voucher(self, br):
        #  This report operates on payment.suggestion opjects; return the first
        # linked voucher.
        return br.voucher_ids[0]

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
            [('res_model', '=', 'payment.suggestion'),
             ('res_id', 'in', ids)],
            context=context)
        # remove previous items
        ir_att_osv.unlink(cr, uid, data_ids)

    def create(self, cr, uid, ids, datas, context=None):
        ids = self._check_vouchers(cr, uid, ids, context)

        # remove previous items
        self.remove_previous(cr, uid, ids, context=context)
        # call parent
        return super(payment_suggestion_report, self).create(
            cr, uid, ids, datas, context)

    def _check_vouchers(self, cr, uid, ids, context):
        ''' - Only print Remittance Letters for non-posted vouchers.
        - Disallow separate journals. '''

        journal = 0

        sugg_obj = pooler.get_pool(cr.dbname).get('payment.suggestion')
        suggs = sugg_obj.browse(cr, uid, ids, context=context)

        ids = []

        for sugg in suggs:
            vouchers = []

            for voucher in sugg.voucher_ids:

                if voucher.state != 'posted':
                    vouchers.append(voucher.id)

                    if journal:
                        if voucher.journal_id != journal:
                            raise osv.except_osv(
                                _('Error'),
                                _('Payment Suggestions must apply to one '
                                  'journal only.'))
                    else:
                        journal = voucher.journal_id

            sugg_obj.write(cr, uid, [sugg.id],
                           { 'voucher_ids': [(6, 0, vouchers)] },
                           context=context)

            if vouchers:
                ids.append(sugg.id)

        if not ids:
            raise osv.except_osv(
                _('Error'),
                _('No draft voucher selected.')
            )

        return ids


payment_suggestion_report('report.account_streamline.payment_suggestion',
                          'payment.suggestion',
                          'addons/account_streamline/report/payment_suggestion.mako',
                          parser=payment_suggestion_parser)
