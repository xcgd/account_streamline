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
from openerp import netsvc
import time
from datetime import datetime
from lxml import etree

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

        debit_curr=fields.float('Debit T', digits_compute=dp.get_precision('Account'),
                                help="This is the debit amount in transaction currency"),
        credit_curr=fields.float('Credit T', digits_compute=dp.get_precision('Account'),
                                help="This is the credit amount in transaction currency"),
        currency_rate=fields.float('Used rate', digits=(12, 6)),
        a1_id=fields.many2one('analytic.code', "Analysis Code 1",
                               domain=[('nd_id.ns_id.model_name', '=', 'account_move_line'),
                                       ('nd_id.ns_id.ordering', '=', '1')]),
        a2_id=fields.many2one('analytic.code', "Analysis Code 1",
                               domain=[('nd_id.ns_id.model_name', '=', 'account_move_line'),
                                       ('nd_id.ns_id.ordering', '=', '2')]),
        a3_id=fields.many2one('analytic.code', "Analysis Code 1",
                               domain=[('nd_id.ns_id.model_name', '=', 'account_move_line'),
                                       ('nd_id.ns_id.ordering', '=', '3')]),
        a4_id=fields.many2one('analytic.code', "Analysis Code 1",
                               domain=[('nd_id.ns_id.model_name', '=', 'account_move_line'),
                                       ('nd_id.ns_id.ordering', '=', '4')]),
        a5_id=fields.many2one('analytic.code', "Analysis Code 1",
                               domain=[('nd_id.ns_id.model_name', '=', 'account_move_line'),
                                       ('nd_id.ns_id.ordering', '=', '5')]),
    )

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        res = super(account_move_line, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        ans_obj = self.pool.get('analytic.structure')

        #display analysis codes only when present on a related structure, with dimension name as label
        ans_ids = ans_obj.search(cr, uid, [('model_name', '=', 'account_move_line')], context=context)
        ans_br = ans_obj.browse(cr, uid, ans_ids,context=context)
        ans_dict = dict()
        for ans in ans_br:
            ans_dict[ans.ordering] = ans.nd_id.name

        doc = etree.XML(res['arch'])

        for field in res['fields']:
            if field == 'a1_id':
                res['fields'][field]['string'] = ans_dict.get('1', 'A1')
                doc.xpath("//field[@name='a1_id']")[0].set('modifiers', '{"tree_invisible": %s}' %
                                    str(((not 'analytic_view' in context) and
                                        (not 'complete_view' in context)) or 
                                        (not '1' in ans_dict)).lower())
            if field == 'a2_id':
                res['fields'][field]['string'] = ans_dict.get('2', 'A2')
                doc.xpath("//field[@name='a2_id']")[0].set('modifiers', '{"tree_invisible": %s}' %
                                    str(((not 'analytic_view' in context) and
                                        (not 'complete_view' in context)) or 
                                        (not '2' in ans_dict)).lower())
            if field == 'a3_id':
                res['fields'][field]['string'] = ans_dict.get('3', 'A3')
                doc.xpath("//field[@name='a3_id']")[0].set('modifiers', '{"tree_invisible": %s}' %
                                    str(((not 'analytic_view' in context) and
                                        (not 'complete_view' in context)) or 
                                        (not '3' in ans_dict)).lower())
            if field == 'a4_id':
                res['fields'][field]['string'] = ans_dict.get('4', 'A4')
                doc.xpath("//field[@name='a4_id']")[0].set('modifiers', '{"tree_invisible": %s}' %
                                    str(((not 'analytic_view' in context) and
                                        (not 'complete_view' in context)) or 
                                        (not '4' in ans_dict)).lower())
            if field == 'a5_id':
                res['fields'][field]['string'] = ans_dict.get('5', 'A5')
                doc.xpath("//field[@name='a5_id']")[0].set('modifiers', '{"tree_invisible": %s}' %
                                    str(((not 'analytic_view' in context) and
                                        (not 'complete_view' in context)) or 
                                        (not '5' in ans_dict)).lower())
        res['arch'] = etree.tostring(doc)
        return res

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

    _constraints = [
        (_check_currency_company,
         "If you see this, the constraint redefined "
         "in account_numergy.account_move_line._check_currency_company is not working!",
         ['currency_id']),
    ]

    def _default_get(self, cr, uid, fields, context=None):
        """add other default values related to multicurrency
        """
        data = super(account_move_line, self)._default_get(cr, uid, fields, context=context)

        move_obj = self.pool.get('account.move')
        if context.get('journal_id'):
            total_curr = 0.0
            #in account.move form view, it is not possible to compute total debit and credit using
            #a browse record. So we must use the context to pass the whole one2many field and compute the total
            if context.get('line_id'):
                for move_line_dict in move_obj.resolve_2many_commands(cr, uid, 'line_id', context.get('line_id'),
                                                                      context=context):
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
            context = {}

        #some data to evaluate
        account_obj = self.pool.get('account.account')
        cur_obj = self.pool.get('res.currency')
        amount_trans = vals.get('amount_currency', 0.0)
        amount_curr = vals.get('debit_curr', 0.0) - vals.get('credit_curr', 0.0)
        amount_base = vals.get('debit', 0.0) - vals.get('credit', 0.0)
        currency_trans = vals.get('currency_id', False)

        cur_browse = cur_obj.browse(cr, uid, currency_trans, context=context)

        #report net currency amount if necessary
        if amount_trans == 0.0 and not amount_curr == 0.0:
            amount_trans = vals['amount_currency'] = amount_curr

        #compute actual rate ONLY when amounts in BOTH base and transaction curr are given
        if not amount_trans == 0.0 and currency_trans and not amount_base == 0.0:
            #vals['currency_rate'] = cur_obj.round(cr, uid, cur_browse, abs(amount_trans / amount_base))
            vals['currency_rate'] = abs(amount_trans / amount_base)

        #make sure the secondary currency is always present by copying the base amount and currency
        if 'account_id' in vals:
            currency_base = account_obj.browse(cr, uid, vals['account_id'], context=context).company_id.currency_id.id
            if amount_trans == 0.0 and (currency_trans == currency_base or not currency_trans):
                amount_trans = vals['amount_currency'] = cur_obj.compute(cr, uid, currency_base,
                                                        currency_base,
                                                        vals.get('debit', 0.0) - vals.get('credit', 0.0),
                                                        context=context)

                currency_trans = vals['currency_id'] = currency_base
                cur_browse = cur_obj.browse(cr, uid, currency_trans, context=context)
                vals['currency_rate'] = 1.0

        #TODO : create proper tests!!!

        #compute debit and credit in transaction currency when not provided
        #this should happen only with generated transaction, not with manual entries
        if not amount_trans == 0.0:
            vals['debit_curr'] = cur_obj.round(cr, uid, cur_browse, amount_trans > 0.0 and amount_trans)
            vals['credit_curr'] = cur_obj.round(cr, uid, cur_browse, amount_trans < 0.0 and -amount_trans)

        return vals

    def onchange_currency(self, cr, uid, ids, account_id, debit, credit, currency_id, date=False, journal=False,
                          context=None):
        """override onchange to pass both debit and credit amount, not only signed amount
        that might be computed only during the save process
        """

        amount = debit - credit
        result = super(account_move_line, self).onchange_currency(cr, uid, ids, account_id, amount, currency_id,
                                                                  date=date, journal=journal, context=context)
        # the context is already updated by the previous statement
        context_rate = currency_id and self.pool.get('res.currency').browse(cr, uid, currency_id, context=context).rate

        if 'value' in result:
            result['value']['amount_currency'] = amount
            result['value']['currency_rate'] = context_rate
        return result

    def write(self, cr, uid, ids, vals, context=None, check=True,
              update_check=True):

        if context is None:
            context = {}
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
                current_journal_id = aml.move_id.journal_id.id

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
        #TODO : write proper tests!!!
        move_id = vals.get('move_id', False)
        if move_id and self.is_move_posted(cr, uid, move_id, context=context):
            raise osv.except_osv(_('Error!'), msg_invalid_move)

        #processing vals to get complete multicurrency data
        vals = self._compute_multicurrency(cr, uid, vals, context=context)

        return super(account_move_line, self).create(cr, uid, vals,
                                                     context=context)

    def reconcile(self, cr, uid, ids, type='auto',
                  writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        '''This method is completely overridden in order to include a full multicurrency support
          The context will determine if second currency is used for reconciliation or not 'reconcile_second_currency'
          In addition, when matching the transaction amounts, differences must be processed as
          both exchange difference and write-off, when applicable.
          Finally, the original code is documented for an easier maintenance.
        '''
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = credit_curr = debit_curr = 0.0
        amount_currency_writeoff = writeoff = currency_rate_difference = 0.0
        account_id = False
        partner_id = False
        currency_id = False

        if context is None:
            context = {}

        company_list = []
        for line in self.browse(cr, uid, ids, context=context):
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company '
                                                      'should be the same for all entries.'))
            company_list.append(line.company_id.id)

        for line in unrec_lines:
            # these are the received lines filtered out of already reconciled lines
            # we compute allocation totals in both currencies
            if line.state <> 'valid':
                raise osv.except_osv(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)

            # control on second currency : must always be the same to authorise reconciliation on second currency
            #TODO : the context key should be given by the reconciliation wizard
            if context.get('reconcile_second_currency', True) and \
                    currency_id and not currency_id == line['currency_id']['id']:
                raise osv.except_osv(_('Error!'),
                        _('All entries must have the same second currency! Reconcile on company currency otherwise.'))
            # control on account : reconciliation must be on one account only
            # TODO : check accuracy of this control
            if account_id and not account_id == line['account_id']['id']:
                raise osv.except_osv(_('Error!'),
                        _('All entries must have the same account to be reconciled.'))

            credit += line['credit']
            credit_curr += line['credit_curr']
            debit += line['debit']
            debit_curr += line['debit_curr']
            amount_currency_writeoff += line['amount_currency'] or 0.0

            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
            currency_id = line['currency_id'] and line['currency_id']['id'] or False

        # we need some browse records
        account = account_obj.browse(cr, uid, account_id, context=context)
        company_currency = account.company_id.currency_id
        currency = currency_obj.browse(cr, uid, currency_id, context=context)

        # Use date in context or today
        date = context.get('date_p', time.strftime('%Y-%m-%d'))
        # If date_p in context => take this date
        # this is so old school...
        # if context.has_key('date_p') and context['date_p']:
        #     date = context['date_p']
        # else:
        #     date = time.strftime('%Y-%m-%d')

        # We will be using a context key to define the reconciliation currency (base or trans)
        if context.get('reconcile_second_currency', True):
            # the actual write off is the conversion of the second currency net amount to base currency at current date
            writeoff = currency_obj.compute(cr, uid, currency.id, company_currency.id,
                                            amount_currency_writeoff, context={'date': date})
            currency_rate_difference = debit - credit - writeoff
        else:
            writeoff = debit - credit

        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s '\
                   'GROUP BY account_id,reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        if not unrec_lines:
            raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        if r[0][1] is not None:
            raise osv.except_osv(_('Error!'), _('Some entries are already reconciled.'))

        if context.get('fy_closing'):
            # We don't want to generate any write-off when being called from the
            # wizard used to close a fiscal year (and it doesn't give us any
            # writeoff_acc_id).
            pass
        else:
        # this condition is replaced as we separate write off from exchange difference
        # elif (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
        #    (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):

            # create exchange difference transaction
            if not currency_obj.is_zero(cr, uid, currency, currency_rate_difference):
                if currency_rate_difference > 0:
                    # this is a gain (account comes from account_voucher module)
                    exchange_diff_acc_id = account.company_id.income_currency_exchange_account_id.id
                    debit = currency_rate_difference
                    credit = 0.0
                    self_credit = currency_rate_difference
                    self_debit = 0.0
                else:
                    # this is a loss
                    exchange_diff_acc_id = account.company_id.expense_currency_exchange_account_id.id
                    debit = 0.0
                    credit = -currency_rate_difference
                    self_credit = 0.0
                    self_debit = -currency_rate_difference

                libelle = _('Exchange difference')

                exchange_diff_lines = [
                    (0, 0, {
                        'name': libelle,
                        'debit': self_debit,
                        'credit': self_credit,
                        'account_id': account_id,
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': currency_id or (account.currency_id.id or False),
                        'amount_currency': 0.0
                    }),
                    (0, 0, {
                        'name': libelle,
                        'debit': debit,
                        'credit': credit,
                        'account_id': exchange_diff_acc_id,
                        'analytic_account_id': context.get('analytic_id', False),
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': currency_id or (account.currency_id.id or False),
                        'amount_currency': 0.0
                    })
                ]

                exchange_diff_move_id = move_obj.create(cr, uid, {
                    'period_id': writeoff_period_id,
                    'journal_id': writeoff_journal_id,
                    'date':date,
                    'state': 'draft',
                    'line_id': exchange_diff_lines
                })

                # The generated transaction needs to be added to the allocation block
                exchange_diff_line_ids = self.search(cr, uid,
                                            [('move_id', '=', exchange_diff_move_id), ('account_id', '=', account_id)])
                # the following case should never happen but still...
                if account_id == exchange_diff_acc_id:
                    exchange_diff_line_ids = [exchange_diff_line_ids[1]]
                ids += exchange_diff_line_ids

            # create write off transaction
            if not currency_obj.is_zero(cr, uid, company_currency, writeoff):
                if not writeoff_acc_id:
                    raise osv.except_osv(_('Warning!'), _('You have to provide an account '
                                                          'for the write off entry.'))
                if writeoff > 0:
                    debit = writeoff
                    credit = 0.0
                    self_credit = writeoff
                    self_debit = 0.0
                else:
                    debit = 0.0
                    credit = -writeoff
                    self_credit = 0.0
                    self_debit = -writeoff
                # If comment exist in context, take it
                if 'comment' in context and context['comment']:
                    libelle = context['comment']
                else:
                    libelle = _('Write-Off')

                # this code is dead anyway as the context keys are never set anywhere!!!
                # cur_id = False
                # amount_currency_writeoff = 0.0
                # if context.get('company_currency_id',False) != context.get('currency_id',False):
                #     cur_id = context.get('currency_id',False)
                #     for line in unrec_lines:
                #         if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                #             amount_currency_writeoff += line.amount_currency
                #         else:
                #             tmp_amount = currency_obj.compute(cr, uid,
                #                                               line.account_id.company_id.currency_id.id,
                #                                               context.get('currency_id',False),
                #                                               abs(line.debit-line.credit),
                #                                               context={'date': line.date})
                #             amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount


                writeoff_lines = [
                    (0, 0, {
                        'name': libelle,
                        'debit': self_debit,
                        'credit': self_credit,
                        'account_id': account_id,
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': currency_id or (account.currency_id.id or False),
                        'amount_currency': -1 * amount_currency_writeoff
                    }),
                    (0, 0, {
                        'name': libelle,
                        'debit': debit,
                        'credit': credit,
                        'account_id': writeoff_acc_id,
                        'analytic_account_id': context.get('analytic_id', False),
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': currency_id or (account.currency_id.id or False),
                        'amount_currency': amount_currency_writeoff
                    })
                ]

                writeoff_move_id = move_obj.create(cr, uid, {
                    'period_id': writeoff_period_id,
                    'journal_id': writeoff_journal_id,
                    'date':date,
                    'state': 'draft',
                    'line_id': writeoff_lines
                })

                # when the write off is posted in the original account,
                # the reconciliation block receives only the second computed line to add up to 0
                # the other one is therefore left open
                writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
                # the following case should never happen but still...
                if account_id == writeoff_acc_id:
                    writeoff_line_ids = [writeoff_line_ids[1]]
                ids += writeoff_line_ids

        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_id': map(lambda x: (4, x, False), ids),
            'line_partial_ids': map(lambda x: (3, x, False), ids)
        })
        wf_service = netsvc.LocalService("workflow")
        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            wf_service.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id
