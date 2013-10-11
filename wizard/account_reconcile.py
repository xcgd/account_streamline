# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 XCG Consulting (www.xcg-consulting.fr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_move_line_reconcile(osv.TransientModel):
    """
    Account move line reconcile wizard, with option to reconcile by base or transaction currency
    """
    _name = 'account.move.line.reconcile'
    _inherit = "account.move.line.reconcile"

    _columns = {
        'force_by_base': fields.boolean('Reconcile by base currency'),
        'company_currency_id': fields.many2one('res.currency', 'Company Currency', readonly=True),
        'trans_currency_id': fields.many2one('res.currency', 'Transaction Currency', readonly=True),
        'credit_curr': fields.float('Credit amount', readonly=True, digits_compute=dp.get_precision('Account')),
        'debit_curr': fields.float('Debit amount', readonly=True, digits_compute=dp.get_precision('Account')),
        'writeoff_curr': fields.float('Write-Off amount', readonly=True, digits_compute=dp.get_precision('Account')),
    }

    def trans_rec_get(self, cr, uid, ids, context=None):
        '''
        This is rewritten to get amount in both currencies
        '''
        account_move_line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        credit = debit = credit_curr = debit_curr = 0
        account_id = company_currency_id = trans_currency_id = force = False
        count = 0
        for line in account_move_line_obj.browse(cr, uid, context['active_ids'], context=context):
            if not line.reconcile_id and not line.reconcile_id.id:
                count += 1
                credit += line.credit
                debit += line.debit
                credit_curr += line.credit_curr
                debit_curr += line.debit_curr
                account_id = line.account_id.id
                company_currency_id = line.account_id.company_id.currency_id.id
                if trans_currency_id and trans_currency_id != line.currency_id.id:
                    trans_currency_id = None
                    force = True
                else:
                    trans_currency_id = line.currency_id.id
        res = {'trans_nbr': count,
               'account_id': account_id,
               'force_by_base': force,
               'company_currency_id': company_currency_id,
               'trans_currency_id': trans_currency_id,
               'credit': credit,
               'debit': debit,
               'writeoff': debit - credit,
               'credit_curr': credit_curr,
               'debit_curr': debit_curr,
               'writeoff_curr': debit_curr - credit_curr, }
        return res

    def default_get(self, cr, uid, fields, context=None):
        res = super(account_move_line_reconcile, self).default_get(cr, uid, fields, context=context)
        data = self.trans_rec_get(cr, uid, context['active_ids'], context)
        if 'company_currency_id' in fields:
            res.update({'company_currency_id': data['company_currency_id']})
        if 'trans_currency_id' in fields:
            res.update({'trans_currency_id': data['trans_currency_id']})
        if 'force_by_base' in fields:
            res.update({'force_by_base': data['force_by_base']})
        if 'credit_curr' in fields:
            res.update({'credit_curr': data['credit_curr']})
        if 'debit' in fields:
            res.update({'debit_curr': data['debit_curr']})
        if 'writeoff_curr' in fields:
            res.update({'writeoff_curr': data['writeoff_curr']})
        return res

    #TODO : is there a better than override all methods???
    def trans_rec_addendum_writeoff(self, cr, uid, ids, context=None):
        if self.read(cr, uid, ids, context=context)[0]['force_by_base']:
            context['reconcile_second_currency'] = True
        else:
            context['reconcile_second_currency'] = False
        return super(account_move_line_reconcile, self).trans_rec_addendum_writeoff(cr, uid, ids, context=context)

    def trans_rec_reconcile_partial_reconcile(self, cr, uid, ids, context=None):
        if self.read(cr, uid, ids, context=context)[0]['force_by_base']:
            context['reconcile_second_currency'] = True
        else:
            context['reconcile_second_currency'] = False
        return super(account_move_line_reconcile, self).trans_rec_reconcile_partial_reconcile(cr, uid, ids, context=context)

    def trans_rec_reconcile_full(self, cr, uid, ids, context=None):
        this = self.read(cr, uid, ids, context=context)[0]
        if not this['trans_nbr']:
            raise osv.except_osv(
                _('Error'),
                _('Your entries are already reconciled'),
            )
        if this['force_by_base']:
            context['reconcile_second_currency'] = True
        else:
            context['reconcile_second_currency'] = False
        return super(account_move_line_reconcile, self).trans_rec_reconcile_full(cr, uid, ids, context=context)
