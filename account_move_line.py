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
from lxml import etree
from openerp.addons.analytic_structure.MetaAnalytic import MetaAnalytic

# fields that are considered as forbidden once the move_id has been posted
forbidden_fields = ["move_id"]

msg_invalid_move = _('You cannot add line(s) into an already posted entry')
msg_cannot_remove_line = _(
    'You cannot remove line(s) from an already posted entry')
msg_invalid_journal = _('You cannot move line(s) between journal types')


class aml_streamline_mail_thread(osv.AbstractModel):
    """Inherit from mail.thread by copy (with a different name) and bypass its
    "create" function as we want to avoid the generation of notifications at
    creation.
    """

    _name = 'account.move.line.streamline.mail.thread'
    _inherit = 'mail.thread'

    def create(self, cr, uid, vals, context=None):
        return osv.AbstractModel.create(
            self, cr, uid, vals, context=context
        )


class account_move_line(osv.osv):
    __metaclass__ = MetaAnalytic
    _name = 'account.move.line'

    _inherit = [
        'account.move.line',
        'account.move.line.streamline.mail.thread',
    ]

    def _get_reconcile_date(self, cr, uid, ids, field_name, arg, context):
        move_line_osv = self.pool['account.move.line']
        result = {}
        move_lines = move_line_osv.browse(cr, uid, ids, context=context)
        for move_line in move_lines:
            result[move_line.id] = (
                move_line.reconcile_id and
                move_line.reconcile_id.create_date or
                None
            )

        return result

    def onchange_partner_id(self, cr, uid, ids,
                            move_id, partner_id, account_id=None,
                            debit=0, credit=0,
                            date=False, journal=False,
                            context=None):
        """
        we override this function to set the date_maturity if it is not set
        """
        res = super(account_move_line, self).onchange_partner_id(
            cr, uid, ids, move_id,
            partner_id, account_id,
            debit, credit, date, journal,
            context=context)
        if (
            'date_maturity' in res['value'] and
            not res['value']['date_maturity']
        ):
            res['value']['date_maturity'] = date
        return res

    _columns = dict(
        currency_id=fields.many2one('res.currency',
                                    'Currency',
                                    help="The mandatory currency code"),
        move_state=fields.related("move_id", "state",
                                  type="char", string="status", readonly=True),
        debit_curr=fields.float('Debit T',
                                digits_compute=dp.get_precision('Account'),
                                help="This is the debit amount "
                                     "in transaction currency"),
        credit_curr=fields.float('Credit T',
                                 digits_compute=dp.get_precision('Account'),
                                 help="This is the credit "
                                      "amount in transaction currency"),
        currency_rate=fields.float('Used rate', digits=(12, 6)),
        date_reconcile=fields.function(
            _get_reconcile_date,
            method=True,
            string="Reconcile Date",
            type='date',
            store={
                'account.move.line': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['reconcile_id'],
                    20
                    ),
            }
        ),

        # Redefine these fields for mail-thread tracking.
        # Track the description and the account to know which lines events are
        # for.
        name=fields.char(
            'Name',
            size=64,
            required=True,
            track_visibility='always',
        ),
        account_id=fields.many2one(
            'account.account',
            'Account',
            required=True,
            ondelete='cascade',
            domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
            select=2,
            track_visibility='always',
        ),
        date_maturity=fields.date(
            'Due date',
            select=True,
            track_visibility='onchange',
        ),
    )

    _analytic = 'account_move_line'

    def __modify_analysis_fields(self, doc, field, ans_dict, context):
        '''
        Factorization
        '''
        doc.xpath("//field[@name='%s']" % field)[0].\
            set('modifiers', '{"tree_invisible": %s, "readonly": true}' %
                str(
                    (
                        (not 'analytic_view' in context) and
                        (not 'complete_view' in context) and
                        (not 'item_complete_view' in context) and
                        (not 'item_analytic_view' in context)
                    ) or (not len(ans_dict))
                ).lower())

    def __set_column_invisible_by_context(self, doc, arch,
                                          field, list_test,
                                          context):
        if not field in arch:
            return
        for test in list_test:
            if test in context:
                doc.xpath("//field[@name='%s']" % field)[0].set(
                    'modifiers',
                    '{"tree_invisible": true, "readonly": true}'
                )
                break

    def __render_columns(self, doc, arch, context):
        # Set the columns invisible depending on the context
        self.__set_column_invisible_by_context(
            doc, arch, 'partner_id',
            [
                'payment_view',
                'reconcile_view',
                'simple_view'
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'journal_id',
            [
                'analytic_view',
                'payment_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'internal_sequence_number',
            [
                'simple_view',
                'analytic_view',
                'item_simple_view',
                'item_analytic_view',
                'reconcile_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'date',
            [
                'simple_view',
                'complete_view',
                'item_complete_view',
                'item_simple_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'date_maturity',
            [
                'simple_view',
                'analytic_view',
                'item_simple_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'date_created',
            [
                'simple_view',
                'analytic_view',
                'item_simple_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'currency_id',
            [
                'analytic_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'debit',
            [
                'analytic_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'credit',
            [
                'analytic_view',
                'item_analytic_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'account_tax_id',
            [
                'simple_view',
            ],
            context
        )
        self.__set_column_invisible_by_context(
            doc, arch, 'state',
            [
                'payment_view',
                'reconcile_view',
            ],
            context
        )

    def convert_modifiers(self, doc):
        fields = doc.xpath("//field")
        for field in fields:
            mod = field.get('modifiers')
            if mod is not None:
                mod = mod.replace('"invisible"', '"tree_invisible"')
                doc.xpath(
                    "//field[@name='%s']" % field.get(
                        'name')
                )[0].set('modifiers', mod)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """Override this function to dynamically hide undefined analytic
        fields. Note that there is no need to rename them as that has been done
        before via the "fields_get" function.
        """

        if context is None:
            context = {}

        res = super(account_move_line, self).\
            fields_view_get(cr, uid, view_id=view_id,
                            view_type=view_type, context=context,
                            toolbar=toolbar, submenu=False)

        ans_obj = self.pool['analytic.structure']

        # display analysis codes only when present on a related structure,
        # with dimension name as label
        ans_dict = ans_obj.get_dimensions_names(
            cr, uid, 'account_move_line', context=context
        )

        doc = etree.XML(res['arch'])
        if 'fields' in res:
            fields = res['fields']
            for ordering in ans_dict:
                anf = 'a{}_id'.format(ordering)
                if anf in fields:
                    self.__modify_analysis_fields(doc, anf, ans_dict, context)
            self.__render_columns(doc, fields, context)

        self.convert_modifiers(doc)

        res['arch'] = etree.tostring(doc)
        return res

    def _get_currency(self, cr, uid, context=None):
        """
        override default so the currency is
        always present (coming from company)
        """
        if context is None:
            context = {}
        if not context.get('journal_id', False):
            return False
        jrn = self.pool['account.journal'].browse(cr, uid,
                                                  context['journal_id'])
        cur = jrn.currency and jrn.currency.id or jrn.company_id.currency_id.id
        return cur or False

    _defaults = {
        # recall standard default to make ure it is locally used (not in super)
        'currency_id': _get_currency,

        'credit_curr': 0.0,
        'debit_curr': 0.0,
        'currency_rate': 1.0,
    }

    def _check_currency_company(self, cr, uid, ids, context=None):
        """
        disable check constraint on secondary currency.
        The idea is to always have a currency and a
        rate on every single move line.
        """
        return True

    _constraints = [
        (_check_currency_company,
         "If you see this, the constraint redefined "
         "in account_streamline.account_move_line._check_currency_company "
         "is not working!",
         ['currency_id']),
    ]

    def _default_get(self, cr, uid, fields, context=None):
        """add other default values related to multicurrency
        """
        data = super(account_move_line, self)._default_get(cr, uid,
                                                           fields,
                                                           context=context)

        move_obj = self.pool['account.move']
        if context.get('journal_id'):
            total_curr = 0.0
            # in account.move form view, it is not possible total
            # compute total debit and credit using
            # a browse record. So we must use the context to pass
            # the whole one2many field and compute the total
            if context.get('line_id'):
                for move_line_dict in move_obj.resolve_2many_commands(
                    cr, uid, 'line_id', context.get('line_id'), context=context
                ):
                    data['currency_id'] = (
                        data.get('currency_id') or
                        move_line_dict.get('currency_id')
                    )
                    total_curr += (
                        move_line_dict.get('debit_curr', 0.0) -
                        move_line_dict.get('credit_curr', 0.0)
                    )

            # compute the total of current move
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

        # some data to evaluate
        account_obj = self.pool['account.account']
        cur_obj = self.pool['res.currency']
        amount_trans = vals.get('amount_currency', 0.0)
        amount_curr = (
            vals.get('debit_curr', 0.0) -
            vals.get('credit_curr', 0.0)
        )

        amount_base = vals.get('debit', 0.0) - vals.get('credit', 0.0)
        currency_trans = vals.get('currency_id', False)

        cur_browse = cur_obj.browse(cr, uid, currency_trans, context=context)

        # report net currency amount if necessary
        if amount_trans == 0.0 and not amount_curr == 0.0:
            amount_trans = vals['amount_currency'] = amount_curr

        # compute actual rate ONLY when amounts in
        # BOTH base and transaction curr are given
        if (
            not amount_trans == 0.0 and
            currency_trans and
            not amount_base == 0.0
        ):
            # vals['currency_rate'] = cur_obj.round(
            #    cr, uid, cur_browse, abs(amount_trans / amount_base)
            # )
            vals['currency_rate'] = abs(amount_trans / amount_base)

        # make sure the secondary currency is always present
        # by copying the base amount and currency
        if 'account_id' in vals and ('debit' in vals or 'credit' in vals):
            currency_base = account_obj.browse(
                cr, uid, vals['account_id'], context=context
            ).company_id.currency_id.id
            if (
                amount_trans == 0.0 and
                (currency_trans == currency_base or not currency_trans)
            ):
                amount_trans = vals['amount_currency'] = cur_obj.compute(
                    cr, uid, currency_base, currency_base,
                    amount_base,
                    context=context
                )

                currency_trans = vals['currency_id'] = currency_base
                cur_browse = cur_obj.browse(
                    cr, uid, currency_trans, context=context)
                vals['currency_rate'] = 1.0

        #TODO : create proper tests!!!

        # compute debit and credit in transaction currency when not provided
        # this should happen only with generated transaction,
        # not with manual entries
        if not amount_trans == 0.0 and currency_trans:
            vals['debit_curr'] = cur_obj.round(
                cr, uid, cur_browse, amount_trans > 0.0 and amount_trans)
            vals['credit_curr'] = cur_obj.round(
                cr, uid, cur_browse, amount_trans < 0.0 and -amount_trans)

        return vals

    def onchange_currency(self, cr, uid, ids, account_id,
                          debit, credit, currency_id, date=False,
                          journal=False, context=None):
        """override onchange to pass both debit and
        credit amount, not only signed amount
        that might be computed only during the save process
        """

        amount = debit - credit
        result = super(account_move_line, self).onchange_currency(
            cr, uid, ids, account_id, amount, currency_id,
            date=date, journal=journal, context=context
        )
        # the context is already updated by the previous statement
        context_rate = currency_id and self.pool['res.currency'].browse(
            cr, uid, currency_id, context=context).rate

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

        # processing vals to get complete multicurrency data
        vals = self._compute_multicurrency(cr, uid, vals, context=context)

        # enforce stricter security rules on
        # the account.move.line / account.move relationship related to the
        # posted status
        target_move_id = vals.get('move_id', False)

        target_journal_id = None
        if target_move_id:
            move_osv = self.pool.get('account.move')
            target_journal_id = move_osv.browse(cr, uid, target_move_id,
                                                context=context).journal_id.id

        # Whether it is safe to remove the "move_id" key from values being set;
        # this is necessary when modifying lines from posted account.move
        # objects as unmodified lines are written with a "move_id" key which
        # results in validation checks not passing as they think the "move_id"
        # is being modified.
        same_move_id = target_move_id

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
                    self.is_move_posted(cr, uid, target_move_id,
                                        context=context):
                raise osv.except_osv(_('Error!'), msg_invalid_move)

            if same_move_id and current_move_id != target_move_id:
                same_move_id = False

            # we don't allow switching from one journal_id (journal type)
            #  to the other even for draft entries
            if target_journal_id and \
                    not target_journal_id == current_journal_id:
                raise osv.except_osv(_('Error!'), msg_invalid_journal)

        if same_move_id:
            vals.pop('move_id')

        return super(account_move_line, self).write(
            cr, uid, ids, vals,
            context=context, check=check,
            update_check=update_check)

    def create(self, cr, uid, vals, context=None):

        if context is None:
            context = {}

        # No notification when creating lines.
        context.update({
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
        })

        # add a security check to ensure no one is
        # creating new account.move.line inside and already posted account.move
        #TODO : write proper tests!!!
        move_id = vals.get('move_id', False)
        if move_id and self.is_move_posted(cr, uid, move_id, context=context):
            raise osv.except_osv(_('Error!'), msg_invalid_move)

        # processing vals to get complete multicurrency data
        vals = self._compute_multicurrency(cr, uid, vals, context=context)

        return super(account_move_line, self).create(
            cr, uid, vals, context=context
        )

    def _get_lines_to_reconcile(self, cr, uid, ids, context={}):
        """This method make several integrity checks, and return the
        lines that are not reconciled among the ids provided.
        :param cr: cursor
        :param uid: user id
        :param ids: list of id (int or long) of move lines
        :param context: the context
        :return: iterable of browse_record
        """
        # if some lines are already reconciled, they are just ignored
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)

        # Better than a constraint in the account_move_reconcile object
        # as it would be raised at the end, wasting time and resources
        if not unrec_lines:
            raise osv.except_osv(
                _('Error!'),
                _('Entry is already reconciled.')
            )
            
        # Maybe change the SELECT to use count(distinct (a,p))?
        cr.execute('SELECT account_id, partner_id '
                   'FROM account_move_line '
                   'WHERE id IN %s '
                   'GROUP BY account_id,partner_id',
                   (tuple(ids),))
        r = cr.fetchall()
        if len(r) > 1:
            raise osv.except_osv(
                _('Error!'),
                _('All entries must have the same account AND same partner '
                  'to be reconciled.')
                )

        return unrec_lines

    def _compute(self, cr, uid, unrec_lines, context={}):
        """Compute debit and credit and some associated values on a list of
        unreconciled move lines.
        Also do the following checks::
        - that each line is valid,
        - that each line are on the same company
        - that all line have the same second currency if not reconciling on
        company currency.
        """
        credit = debit = credit_curr = debit_curr = 0.0
        amount_currency_writeoff = writeoff = currency_rate_difference = 0.0
        account_id = False
        partner_id = False
        currency_id = False
        # XXX a SQL request might faster there (rather than calculating until
        # a company is not in the list
        company_list = []
        # unrec_ids will be used to store all the id for this reconcile, and
        # also all the newly created lines too
        unrec_ids = []

        for line in unrec_lines:
            # these are the received lines filtered out of already reconciled
            # lines we compute allocation totals in both currencies

            account_id = line.account_id.id
            partner_id = line.partner_id and line.partner_id.id or False
            currency_id = line.currency_id and line.currency_id.id or False

            if line.state != 'valid':
                raise osv.except_osv(
                    _("Error!"),
                    _("Entry \"%s\" is not valid !") % line.name
                )

            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(
                    _("Warning!"),
                    _("To reconcile the entries company "
                      "should be the same for all entries.")
                )
            company_list.append(line.company_id.id)

            # control on second currency : must always be the same
            if (
                context.get('reconcile_second_currency', True) and
                currency_id and not currency_id == line['currency_id']['id']
            ):
                raise osv.except_osv(
                    _("Error!"),
                    _("All entries must have the same second currency! "
                      "Reconcile on company currency otherwise.")
                )

            credit += line.credit or 0.0
            credit_curr += line.credit_curr or 0.0
            debit += line.debit or 0.0
            debit_curr += line.debit_curr or 0.0
            # the computed write off is the net currency amount
            amount_currency_writeoff += (
                (line.debit_curr or 0.0) - (line.credit_curr or 0.0)
            )

            # get only relevant ids of lines to reconcile
            unrec_ids.append(line.id)
        return (credit, debit, credit_curr, debit_curr,
            amount_currency_writeoff, writeoff, currency_rate_difference,
            account_id, partner_id , currency_id, unrec_ids)

    def reconcile_partial(self, cr, uid, ids, type='auto',
                          writeoff_acc_id=False, writeoff_period_id=False,
                          writeoff_journal_id=False, context=None):
        """This method is completely overridden in order
        to include a full multicurrency support
        The context will determine if second currency is used
        for reconciliation or not 'reconcile_second_currency'
        Many optimisations and integrity controls are added.
        Finally, the original code is documented for an easier maintenance.
        """
        move_rec_obj = self.pool['account.move.reconcile']
        merges = []
        unmerge = []
        total = 0.0
        merges_rec = []
        if context is None:
            context = {}
        # if some lines are already reconciled, they are just ignored
        unrec_lines = self._get_lines_to_reconcile(cr, uid, ids, context)

        for line in unrec_lines:
            if line.account_id.currency_id:
                currency_id = line.account_id.currency_id
            else:
                currency_id = line.company_id.currency_id
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    if not line2.reconcile_id:
                        if line2.id not in merges:
                            merges.append(line2.id)
                        if line2.account_id.currency_id:
                            total += line2.amount_currency
                        else:
                            total += (line2.debit or 0.0) - (line2.credit or 0.0)
                merges_rec.append(line.reconcile_partial_id.id)
            else:
                unmerge.append(line.id)
                if line.account_id.currency_id:
                    total += line.amount_currency
                else:
                    total += (line.debit or 0.0) - (line.credit or 0.0)
        if self.pool['res.currency'].is_zero(cr, uid, currency_id, total):
            res = self.reconcile(cr, uid, merges+unmerge, context=context, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id)
            return res
        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_partial_ids': map(lambda x: (4,x,False), merges+unmerge)
        }, context=reconcile_context)
        move_rec_obj.reconcile_partial_check(cr, uid, [r_id] + merges_rec, context=reconcile_context)
        return True

    def reconcile(self, cr, uid, ids, type='auto',
                  writeoff_acc_id=False, writeoff_period_id=False,
                  writeoff_journal_id=False, context=None):
        """This method is completely overridden in order
        to include a full multicurrency support
        The context will determine if second currency is used
        for reconciliation or not 'reconcile_second_currency'
        In addition, when matching the transaction amounts,
        differences must be processed as both exchange difference and
        write-off, when applicable. Many optimisations and integrity
        controls are added. Finally, the original code is
        documented for an easier maintenance.
        """
        account_obj = self.pool['account.account']
        move_obj = self.pool['account.move']
        move_rec_obj = self.pool['account.move.reconcile']
        partner_obj = self.pool['res.partner']
        currency_obj = self.pool['res.currency']

        # if some lines are already reconciled, they are just ignored
        unrec_lines = self._get_lines_to_reconcile(cr, uid, ids, context)

        if context is None:
            context = {}

        # unrec_ids will be used to store all the id for this reconcile, and
        # also all the newly created lines too

        (credit, debit, credit_curr, debit_curr, amount_currency_writeoff,
            writeoff, currency_rate_difference, account_id, partner_id ,
            currency_id, unrec_ids) = self._compute(
                cr, uid, unrec_lines, context)

        # we need some browse records
        account = account_obj.browse(cr, uid, account_id, context=context)
        company_currency = account.company_id.currency_id
        currency = currency_obj.browse(cr, uid, currency_id, context=context)

        if not account.reconcile:
            raise osv.except_osv(
                _("Error"),
                _("The account is not defined to be reconciled!")
            )

        # Use date in context or today
        date = context.get('date_p', time.strftime('%Y-%m-%d'))
        # If date_p in context => take this date
        # this is so old school...
        # if context.has_key('date_p') and context['date_p']:
        #     date = context['date_p']
        # else:
        #     date = time.strftime('%Y-%m-%d')

        # We will be using a context key to define the
        # reconciliation currency (base or trans)
        if context.get('reconcile_second_currency', True):
            # the actual write off is the conversion of the second
            # currency net amount to base currency at current date
            writeoff = currency_obj.compute(
                cr, uid, currency.id, company_currency.id,
                amount_currency_writeoff, context={'date': date}
            )
            currency_rate_difference = debit - credit - writeoff
        else:
            writeoff = debit - credit

        if context.get('fy_closing'):
            # We don't want to generate any write-off
            # when being called from the
            # wizard used to close a fiscal year (and it doesn't give us any
            # writeoff_acc_id).
            pass
        else:
        # this condition is replaced as we separate
        # write off from exchange difference
        # elif (not currency_obj.is_zero(
        #     cr, uid, account.company_id.currency_id, writeoff
        # )) or
        #    (account.currency_id and
        # (not currency_obj.is_zero(
        #      cr, uid, account.currency_id, currency
        # ))):

            # create exchange difference transaction
            if not currency_obj.is_zero(
                cr, uid, currency, currency_rate_difference
            ):
                if currency_rate_difference > 0:
                    # this is a gain account comes from account_voucher module
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

                if not exchange_diff_acc_id:
                    raise osv.except_osv(
                        _('Warning!'),
                        _('You have to configure an account '
                          'for the exchange gain/loss.')
                    )

                libelle = _('Exchange difference')

                exchange_diff_lines = [
                    (0, 0, {
                        'name': libelle,
                        'debit': self_debit,
                        'credit': self_credit,
                        'account_id': account_id,
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': (
                            currency_id or
                            (account.currency_id.id or False)
                        ),
                        'amount_currency': 0.0
                    }),
                    (0, 0, {
                        'name': libelle,
                        'debit': debit,
                        'credit': credit,
                        'account_id': exchange_diff_acc_id,
                        'analytic_account_id': context.get(
                            'analytic_id', False
                        ),
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': (
                            currency_id or
                            (account.currency_id.id or False)
                        ),
                        'amount_currency': 0.0
                    })
                ]

                exchange_diff_move_id = move_obj.create(cr, uid, {
                    'period_id': writeoff_period_id,
                    'journal_id': writeoff_journal_id,
                    'date': date,
                    'state': 'draft',
                    'line_id': exchange_diff_lines
                })

                # The generated transaction needs to be
                # added to the allocation block
                exchange_diff_line_ids = self.search(
                    cr, uid,
                    [
                        ('move_id', '=', exchange_diff_move_id),
                        ('account_id', '=', account_id)
                    ]
                )
                # the following case should never happen but still...
                if account_id == exchange_diff_acc_id:
                    exchange_diff_line_ids = [exchange_diff_line_ids[1]]

                # add the created lines to the reconcile block
                unrec_ids += exchange_diff_line_ids

            # create write off transaction
            if not currency_obj.is_zero(cr, uid, company_currency, writeoff):
                if not writeoff_acc_id:
                    raise osv.except_osv(
                        _('Warning!'),
                        _('You have to provide an account '
                          'for the write off entry.')
                    )
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

                writeoff_lines = [
                    (0, 0, {
                        'name': libelle,
                        'debit': self_debit,
                        'credit': self_credit,
                        'account_id': account_id,
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': (
                            currency_id or
                            (account.currency_id.id or False)
                        ),
                        'amount_currency':-1 * amount_currency_writeoff
                    }),
                    (0, 0, {
                        'name': libelle,
                        'debit': debit,
                        'credit': credit,
                        'account_id': writeoff_acc_id,
                        'analytic_account_id': context.get(
                            'analytic_id', False
                        ),
                        'date': date,
                        'partner_id': partner_id,
                        'currency_id': (
                            currency_id or
                            (account.currency_id.id or False)
                        ),
                        'amount_currency': amount_currency_writeoff
                    })
                ]

                writeoff_move_id = move_obj.create(cr, uid, {
                    'period_id': writeoff_period_id,
                    'journal_id': writeoff_journal_id,
                    'date': date,
                    'state': 'draft',
                    'line_id': writeoff_lines
                })

                # when the write off is posted in the original account,
                # the reconciliation block receives only the secondary
                # computed line to add up to 0
                # the other one is therefore left open
                writeoff_line_ids = self.search(
                    cr, uid,
                    [
                        ('move_id', '=', writeoff_move_id),
                        ('account_id', '=', account_id)
                    ],
                )
                # the following case should never happen but still...
                if account_id == writeoff_acc_id:
                    writeoff_line_ids = [writeoff_line_ids[1]]

                # add the created lines to the reconcile block
                unrec_ids += writeoff_line_ids

        # marking the lines as reconciled does not change their validity,
        # so there is no need to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid,
                                   {'type': type,
                                    },
                                   context=reconcile_context)

        # Do not use the magic tuples as it is extremely costly on large collections
        self.write(cr, uid, unrec_ids, {'reconcile_id': r_id,
                                        'reconcile_partial_id': False,
                                        },
                   context=context)

        wf_service = netsvc.LocalService("workflow")
        # trigger the workflow on any item listening to move lines
        for id in unrec_ids:
            wf_service.trg_trigger(uid, 'account.move.line', id, cr)

        # tested before in the method that there is an unrec_line
        # also done before is finding partner_id that need to be the same
        # for all unrec_lines
        if (
            partner_id and
            not partner_obj.has_something_to_reconcile(
                cr, uid, partner_id, context=context
            )
        ):
            partner_obj.mark_as_reconciled(
                cr, uid, [partner_id], context=context
            )

        return r_id
