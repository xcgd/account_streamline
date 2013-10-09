# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools.translate import _
from osv import osv

from report_webkit.webkit_report import WebKitParser


class remittance_letter_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(remittance_letter_parser, self).__init__(cr, uid, name, context=context)
        self.__check_vouchers(cr, uid, context)
        self.localcontext.update({
            'debit_credit': self.get_debit_credit,
            'format_amount': self.format_amount,
            'message': self.get_message,
        })

    def __check_vouchers(self, cr, uid, context=None):
        """ This function check if the message for payment
        is set in the company settings and raise in the other case.
        """
        company_osv = self.pool.get('res.company')
        company_id = company_osv._company_default_get(cr, uid, 'account.voucher', context=context)
        company_br = company_osv.browse(cr, uid, company_id, context=context)
        if not company_br.message_voucher_validate:
            raise osv.except_osv(
                _('Error'),
                _('Please set the message for payments'
                  ' in your company settings.')
            )

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


class remittance_letter_report(WebKitParser):
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
        return super(remittance_letter_report, self).create(
            cr, uid, ids, datas, context)


remittance_letter_report('report.account_streamline.remittance_letter',
                         'account.voucher',
                         'addons/account_streamline/report/remittance_letter.mako',
                         parser=remittance_letter_parser)
