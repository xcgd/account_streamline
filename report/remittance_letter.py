# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class remittance_letter_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(remittance_letter_parser, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'debit_credit': self.get_debit_credit,
            'get_voucher': self.get_voucher,
            'bottom_message': self.get_bottom_message,
            'top_message': self.get_top_message,
            'title': self.get_title,
        })

    def get_debit_credit(self, br):
        return _('Debit') if br.type == 'dr' else _('Credit')

    def get_voucher(self, br):
        # This report already operates on account.voucher objects.
        return br

    def get_bottom_message(self, br):
        company = br.company_id
        if not company:
            return ''

        return self.translate(company.remittance_letter_bottom)

    def get_top_message(self, br):
        company = br.company_id
        if not company:
            return ''

        iban = br.iban or ''
        date = br.date or ''

        return (self.translate(company.remittance_letter_top)
                .replace('$iban', iban)
                .replace('$date', str(date)))

    def get_title(self, br):
        return _('Remittance Letter')

    def translate(self, message):
        ''' Translate text according to the currently selected language. '''

        trans_obj = self.pool['ir.translation']
        trans_ids = trans_obj.search(
            self.cr, self.uid,
            [
                ('src', '=', message),
                ('lang', '=', self.localcontext['lang'])
            ],
            context=self.localcontext)
        if not trans_ids:
            return '' if message is False else message
        translated_value = trans_obj.browse(
            self.cr, self.uid, trans_ids[0], context=self.localcontext).value
        # Replace False by empty string (False indicating a missing value)
        if translated_value is False:
            return ''
        return translated_value


class remittance_letter_report(WebKitParser):
    def remove_previous(self, cr, uid, ids, context=None):
        # get attachment model
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
        ids = self._check_vouchers(cr, uid, ids, context)

        # remove previous items
        self.remove_previous(cr, uid, ids, context=context)
        # call parent
        return super(remittance_letter_report, self).create(
            cr, uid, ids, datas, context)

    def _check_vouchers(self, cr, uid, ids, context):
        ''' - Only print Remittance Letters for posted vouchers. '''

        voucher_obj = pooler.get_pool(cr.dbname).get('account.voucher')
        vouchers = voucher_obj.browse(cr, uid, ids, context=context)

        ids = []

        for voucher in vouchers:
            if voucher.state == 'posted':
                ids.append(voucher.id)

        if not ids:
            raise osv.except_osv(
                _('Error'),
                _('No posted voucher selected.')
            )

        return ids


remittance_letter_report('report.account_streamline.remittance_letter',
                         'account.voucher',
                         'addons/account_streamline/report/remittance_letter.mako',
                         parser=remittance_letter_parser)
