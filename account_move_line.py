# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Analytic Online, for OpenERP
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

# fields that are considered as forbidden once the move_id has been posted
forbidden_fields = ["move_id"]

msg_invalid_move = _('You cannot add line(s) into an already posted entry')
msg_cannot_remove_line = _(
    'You cannot remove line(s) from an already posted entry')
msg_invalid_journal = _('You cannot move line(s) between journal types')


class account_move_line(osv.osv):
    _name = "account.move.line"
    _inherit = "account.move.line"

    _columns = dict(
        currency_id=fields.many2one('res.currency', 'Currency', help="The mandatory currency code"),

        move_state=fields.related("move_id", "state",
                                  type="char", string="status", readonly=True),

        debit_curr=fields.float('Debit', digits_compute=dp.get_precision('Account')),
        credit_curr=fields.float('Credit', digits_compute=dp.get_precision('Account')),
        currency_rate=fields.float('Used rate', digits=(12,6)),
    )

    def _get_currency(self, cr, uid, context=None):
        """
        override default so the currency is always present (coming from company)
        """
        if context is None:
            context = {}
        if not context.get('journal_id', False):
            return False
        jrn = self.pool.get('account.journal').browse(cr, uid, context['journal_id'])
        cur = jrn.currency and jrn.currency.id or jrn.company_id.currency_id.id
        return cur or False

    _defaults = {
        'credit_curr': 0.0,
        'debit_curr': 0.0,
        'currency_rate': 1.0,
    }

    def _check_currency_company(self, cr, uid, ids, context=None):
        """
        disable check constraint on secondary currency.
        The idea is to always have a currency and a rate on every single move line.
        """
        return True

    def _default_get(self, cr, uid, fields, context=None):
        """add other default valued related to multicurrency
        """
        data = super(account_move_line, self)._default_get(cr, uid, fields, context=context)

        move_obj = self.pool.get('account.move')
        if context.get('journal_id'):
            total_curr = 0.0
            #in account.move form view, it is not possible to compute total debit and credit using
            #a browse record. So we must use the context to pass the whole one2many field and compute the total
            if context.get('line_id'):
                for move_line_dict in move_obj.resolve_2many_commands(cr, uid, 'line_id', context.get('line_id'), context=context):
                    data['currency_id'] = data.get('currency_id') or move_line_dict.get('currency_id')
                    total_curr += move_line_dict.get('debit_curr', 0.0) - move_line_dict.get('credit_curr', 0.0)

            #compute the total of current move
            data['debit_curr'] = total_curr < 0 and -total_curr or 0.0
            data['credit_curr'] = total_curr > 0 and total_curr or 0.0

        return data

    def is_move_posted(self, cr, uid, move_id, context=None):
        """internal helper function
        """
        move_osv = self.pool.get('account.move')

        if move_id:
            move = move_osv.browse(cr, uid, move_id, context=context)
            return move.state == 'posted'

    def _compute_multicurrency(self, cr, uid, vals, context=None):
        if context is None:
            context={}
        account_obj = self.pool.get('account.account')
        cur_obj = self.pool.get('res.currency')

        #compute actual rate when amounts in both base and transaction curr are given
        amount = vals.get('amount_currency', 0.0)
        d = vals.get('debit', False)
        c = vals.get('credit', False)
        if 'amount_currency' in vals:
            vals['currency_rate'] = abs(amount / (vals.get('debit', 0.0)-vals.get('credit', 0.0)))

        #make sure the secondary currency is always present
        if 'account_id' and 'currency_id' in vals:
            account = account_obj.browse(cr, uid, vals['account_id'], context=context)
            if (vals.get('amount_currency', False) is False) and vals.get('currency_id') == account.company_id.currency_id.id:
                vals['amount_currency'] = cur_obj.compute(cr, uid, account.company_id.currency_id.id,
                                                          account.company_id.currency_id.id,
                                                          vals.get('debit', 0.0)-vals.get('credit', 0.0),
                                                          context=context)

        #compute debit and credit in transaction currency when not provided
        amount = vals.get('amount_currency', 0.0)
        if 'amount_currency' in vals:
            cur_browse = cur_obj.browse(cr, uid, vals.get('currency_id'), context=context)
            vals['debit_curr'] = cur_obj.round(cr, uid, cur_browse, amount>0.0 and amount or 0.0)
            vals['credit_curr'] = cur_obj.round(cr, uid, cur_browse, amount<0.0 and -amount or 0.0)

        return vals

    def onchange_currency(self, cr, uid, ids, account_id, debit, credit, currency_id, date=False, journal=False, context=None):
        """override onchange to pass both debit and credit amount, not only signed amount
        that might be computed only during the save process
        """
        amount = debit - credit
        result = super(account_move_line,self).onchange_currency(cr, uid, ids, account_id, amount, currency_id,
                                                               date=date, journal=journal, context=context)
        if 'value' in result:
            result['value']['amount_currency'] = amount
        return result

    def write(self, cr, uid, ids, vals, context=None, check=True,
              update_check=True):

        if context is None:
            context={}
        if isinstance(ids, (int, long)):
            ids = [ids]

        #processing vals to get complete multicurrency data
        vals = self._compute_multicurrency(cr, uid, vals, context=context)

        #enforce stricter security rules on
        #the account.move.line / account.move relationship related to the
        #posted status
        target_move_id = vals.get('move_id', False)

        target_journal_id = None
        if target_move_id:
            move_osv = self.pool.get('account.move')
            target_journal_id = move_osv.browse(cr, uid, target_move_id,
                                                context=context).journal_id.id

        for aml in self.browse(cr, uid, ids, context=context):

            current_move = getattr(aml, 'move_id', None)
            if current_move:
                current_move_id = aml.move_id.id
                current_journal_id = aml.move_id.journal_id

            else:
                current_move_id = None
                current_journal_id = None

            # if the user tries to move away a line from an account_move which
            # if already posted
            if current_move_id and self.is_move_posted(
                    cr, uid, current_move_id, context=context) and \
                target_move_id and \
                    not current_move_id == target_move_id:
                raise osv.except_osv(_('Error!'), msg_cannot_remove_line)

            # if the user is trying to move an acm into an account_move
            #  which is posted
            if target_move_id and not target_move_id == current_move_id and \
                    self.is_move_posted(
                        cr, uid, target_move_id, context=context):
                raise osv.except_osv(_('Error!'), msg_invalid_move)

            # we don't allow switching from one journal_id (journal type)
            #  to the other even for draft entries
            if target_journal_id and \
                    not target_journal_id == current_journal_id:
                raise osv.except_osv(_('Error!'), msg_invalid_journal)

        return super(account_move_line, self).write(
            cr, uid, ids, vals,
            context=context, check=check,
            update_check=update_check)

    def create(self, cr, uid, vals, context=None):

        """
        add a security check to ensure no one is
        creating new account.move.line inside and already posted account.move
        """
        move_id = vals.get('move_id', False)
        if move_id and self.is_move_posted(cr, uid, move_id, context=context):
            raise osv.except_osv(_('Error!'), msg_invalid_move)

        #processing vals to get complete multicurrency data
        vals = self._compute_multicurrency(cr, uid, vals, context=context)

        return super(account_move_line, self).create(cr, uid, vals,
                                                     context=context)

