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

from ast import literal_eval as leval
from copy import deepcopy
import itertools

from openerp.osv import fields, osv
from openerp.tools.translate import _


msg_invalid_line_type = _('Account type %s is not usable in payment vouchers.')
msg_invalid_partner_type = _('Partner %s is not a supplier.')
msg_define_dc_on_journal = _(
    'Please define default credit/debit accounts on the journal "%s".')
msg_already_reconciled = _(
    'The line %s is already reconciled.'
)

move_line_domain = [
    '|',
    ('reconcile_id', '=', False),
    ('reconcile_partial_id', '!=', False),
    ('account_id.type', 'in', ['payable', 'receivable']),
    ('state', '=', 'valid'),
    ('move_id.state', '=', 'posted')
]


class good_to_pay(osv.osv_memory):
    """create vouchers for all invoices that have been selected
    """

    class __container:
        lines = set()

        def add(self, ids, key):
            self.lines.update(ids)
            if key not in self._dict:
                self._dict[key] = set(ids)
            else:
                self._dict[key].update(ids)

        def delete(self, ids):
            self.lines.difference_update(ids)

    _name = "account.move.line.goodtopay"
    _description = "Payment selection for good to pay"

    _columns = {
        'journal_id': fields.many2one(
            'account.journal',
            'Payment Method',
            required=True,
            domain=[('type', 'in', ['bank', 'cash'])]
        ),
        'line_ids': fields.many2many(
            'account.move.line',
            'good_to_pay_rel_',
            'line_id',
            'good_to_pay_id',
            _('Lines'),
        ),
        'generate_report': fields.boolean('Generate Report'),
        'nb_lines': fields.integer('Number of lines'),
        'total_amount': fields.float('Total Amount'),
        'view_selection': fields.selection(
            [('complete', 'Complete view'),
             ('detailed', 'Detailed view')],
            translate=True,
            string='View selector',
            required=True,
        ),
        'partner_id': fields.many2one(
            'res.partner',
            string='Selected Partner',
        ),
        'context_saved': fields.text(),
    }

    def default_get(self, cr, uid, field_list=None, context=None):
        if 'active_ids' not in context:
            return {}

        vals = {}

        vals['context_saved'] = (
            "{'lines_by_partner': {},"
            "'state_line_ids': 'entering_wizard'}"
        )

        aml_obj = self.pool['account.move.line']
        move_lines = aml_obj.search(
            cr, uid,
            move_line_domain + [
                ('id', 'in', context.get('active_ids', [])),
            ],
            context=context
        )

        move_lines = [(6, 0, move_lines)]
        vals['line_ids'] = move_lines

        vals['generate_report'] = True

        return vals

    def create(self, cr, uid, vals, context=None):
        """Override this function to add read-only fields to the list of
        values; otherwise, the _add_missing_default_values function (see
        orm.py) will call a second default_get at validation (which we
        absolutely want to avoid as we initialize some structures there).
        """

        vals['nb_lines'] = 0
        vals['total_amount'] = 0.0

        return super(good_to_pay, self).create(
            cr, uid, vals, context=context
        )

    def _generate_report(self, cr, uid, active_ids, context=None):
        ''' Generate a Payment Suggestion report. '''

        # active_ids contains move-line ids; remove them or the payment
        # suggestion object will use them by default.
        if 'active_ids' in context:
            del context['active_ids']

        return (self.pool['payment.suggestion']
                .print_payment_suggestion(cr, uid, active_ids,
                                          context=context))

    def __check_partner_debits(self, cr, uid, context_saved, context):
        """Loop through selected partners to ensure they all have more credit
        than debit.
        :return False and the first partner having a debit balance, otherwise
        return True.
        """
        aml_osv = self.pool['account.move.line']

        for partner_id, line_ids in context_saved['lines_by_partner'].items():
            total_credit = 0.0
            total_debit = 0.0
            reads = aml_osv.read(
                cr, uid, line_ids, ['credit', 'debit', 'partner_id'], context
            )
            for read in reads:
                total_credit += read['credit']
                total_debit += read['debit']
            if total_credit <= total_debit:
                return False, read['partner_id'][1]
        return True, None

    def _get_account_conflicts(self, cr, uid, line_ids, context=None):
        """Find every partner that is found with two or more different accounts
        in the move lines given in argument.
        Return those partners associated with their accounts in a dictionary.
        """

        aml_osv = self.pool['account.move.line']
        partner_dict = {}
        conflicts = {}
        lines = aml_osv.browse(cr, uid, line_ids, context=context)

        for line in lines:
            if not line.partner_id:
                continue
            partner = line.partner_id.id
            account = line.account_id.id
            if partner in partner_dict:
                first_account = partner_dict[partner]
                if first_account != account:
                    if partner not in conflicts:
                        conflicts[partner] = {first_account}
                    conflicts[partner].add(account)
            else:
                partner_dict[partner] = account

        for partner in conflicts:
            conflicts[partner] = list(conflicts[partner])
        return conflicts

    def _print_conflicts(
        self, cr, uid, conflicts, max_accounts=15, max_partners=5, context=None
    ):
        """Return a dialog box-friendly representation of the conflicts."""

        tr_accounts = tr_partners = unt_accounts = unt_partners = 0
        partner_osv = self.pool['res.partner']
        account_osv = self.pool['account.account']
        partner_ids = conflicts.keys()
        msg = _(
            u"Different accounts are being referred for the same partner(s):"
        )

        for partner_id in partner_ids:
            account_ids = conflicts[partner_id]
            if tr_partners >= max_partners or tr_accounts >= max_accounts:
                unt_partners += 1
                unt_accounts += len(account_ids)
                continue
            else:
                treated_local = 0
                tr_partners += 1

            partner_name = partner_osv.read(
                cr, uid, [partner_id], ['name'], context=context
            )[0]['name']
            msg += '\n' + partner_name + ':'

            for account_id in account_ids:
                if tr_accounts >= max_accounts:
                    break
                else:
                    tr_accounts += 1
                    treated_local += 1

                account = account_osv.read(
                    cr, uid, [account_id], ['code', 'name'], context=context
                )[0]
                msg += '\n*  ' + account['code'] + ' ' + account['name']

            if treated_local != len(account_ids):
                pattern = _(u"({0} more conflicting accounts)")
                msg += '\n' + pattern.format(len(account_ids) - treated_local)

        if unt_partners:
            pattern = _(u"({0} more partners with {1} accounts)")
            msg += '\n' + pattern.format(unt_partners, unt_accounts)

        return msg

    def good_to_pay(self, cr, uid, ids, context=None):

        aml_osv = self.pool['account.move.line']
        avl_osv = self.pool['account.voucher.line']
        voucher_osv = self.pool['account.voucher']
        journal_osv = self.pool['account.journal']

        supplier_to_voucher_map = dict()
        voucher_amounts = dict()

        action = {'type': 'ir.actions.act_window_close'}

        for form in self.read(cr, uid, ids, context=context):

            conflicts = self._get_account_conflicts(
                cr, uid, form['line_ids'], context=context
            )
            if conflicts:
                raise osv.except_osv(
                    _('Error'),
                    self._print_conflicts(cr, uid, conflicts, context=context)
                )

            context_saved = leval(form['context_saved'])
            test, partner_name = self.__check_partner_debits(
                cr, uid, context_saved, context
            )
            if not test:
                raise osv.except_osv(
                    _('Error'),
                    _('The voucher for the partner %s is debit.' %
                      partner_name)
                )
            auto = form['generate_report']
            active_ids = list(
                itertools.chain.from_iterable(
                    context_saved['lines_by_partner'].values()
                )
            )
            for aml in aml_osv.browse(
                    cr, uid, active_ids, context=context):

                # first we need to make sure the line is acceptable to be
                # used in a voucher (ie: account is marked as payable

                if not aml.account_id.type == 'payable':
                    msg = msg_invalid_line_type % aml.account_id.type
                    raise osv.except_osv(_('Error!'), msg)

                if not aml.partner_id or not aml.partner_id.supplier:
                    msg = msg_invalid_partner_type % aml.partner_id.name
                    raise osv.except_osv(_('Error!'), msg)

                if aml.reconcile_id:
                    msg = msg_already_reconciled % aml.name
                    raise osv.except_osv(_('Error!'), msg)

                partner_id = aml.partner_id.id

                if partner_id not in supplier_to_voucher_map:
                    # we don't have a voucher for this supplier yet...
                    # just create a new one for our own use
                    vals = dict()
                    vals['partner_id'] = partner_id
                    # id is stored in fist column, name in second column
                    vals['journal_id'] = form['journal_id'][0]
                    vals['type'] = 'payment'
                    journal = journal_osv.browse(
                        cr, uid, vals['journal_id'])
                    vals['amount'] = 0.0
                    vals['payment_option'] = 'without_writeoff'
                    # Define "pre_line" to ensure the voucher is aware of the
                    # lines we are going to add; otherwise it doesn't show all
                    # of them.
                    vals['pre_line'] = True

                    if not journal.default_credit_account_id or \
                            not journal.default_debit_account_id:
                        raise osv.except_osv(
                            _('Error!'),
                            msg_define_dc_on_journal % journal.name)

                    account_id = journal.default_credit_account_id.id or \
                        journal.default_debit_account_id.id

                    vals['account_id'] = account_id

                    bank_osv = self.pool['res.partner.bank']
                    bank_id = bank_osv.search(
                        cr, uid, [('partner_id', '=', partner_id)],
                        context=context
                    )

                    if bank_id:
                        vals['partner_bank_id'] = bank_id[0]

                    voucher_id = voucher_osv.create(cr, uid, vals,
                                                    context=context)

                    supplier_to_voucher_map[partner_id] = voucher_id
                    voucher_amounts[voucher_id] = 0.0

                else:
                    voucher_id = supplier_to_voucher_map[partner_id]

                # now that we have a voucher id we'll add our line to it
                line_vals = dict()
                line_vals['name'] = aml.name
                line_vals['voucher_id'] = voucher_id
                # Voucher lines must use the same account as the move lines,
                # in order to be able to reconcile them with the move lines
                # created during the validation of the voucher.
                line_vals['account_id'] = aml.account_id.id
                line_vals['type'] = 'dr' if aml.credit else 'cr'
                line_vals['move_line_id'] = aml.id

                avl_id = avl_osv.create(cr, uid, line_vals, context=context)
                avl = avl_osv.browse(cr, uid, avl_id, context=context)

                line_vals2 = dict()
                line_vals2['reconcile'] = True
                line_vals2['amount'] = avl.amount_unreconciled

                avl_osv.write(cr, uid, [avl_id], line_vals2)

                # Add credits, substract debits.
                voucher_amounts[voucher_id] += avl.amount_unreconciled * (
                    1 if aml.credit else -1
                )

            # once every voucher is finished we recompute the voucher totals
            # and write them back to the vouchers
            for voucher_id in voucher_amounts.keys():
                voucher_osv.write(
                    cr, uid, [voucher_id],
                    {'amount': voucher_amounts[voucher_id]})

            if auto:
                action = self._generate_report(
                    cr, uid, voucher_amounts.keys(), context
                )

        return action

    def onchange_view_selector(
        self, cr, uid, ids, selector, partner_id, context_saved, context=None
    ):
        context_saved = leval(context_saved)
        if context_saved['state_line_ids'] == 'entering_wizard':
            context_saved['state_line_ids'] = None
            return {'value': {'context_saved': str(context_saved)}}
        domain = {}
        value = {}
        if not selector:
            selector = 'complete'
            value['view_selection'] = 'complete'
        list_ids = []
        if selector == 'complete':
            list_ids = list(
                itertools.chain.from_iterable(
                    context_saved['lines_by_partner'].values()
                )
            )
            partner_id = None
        else:
            if (
                context_saved['lines_by_partner'] and
                partner_id != context_saved['lines_by_partner'].keys()[0]
            ):
                partner_id = context_saved['lines_by_partner'].keys()[0]
            else:
                domain['line_ids'] = [('partner_id', '=', -1)]

        if list_ids:
            value['line_ids'] = [(6, 0, list_ids)]
        value['partner_id'] = partner_id

        context_saved['state_line_ids'] = 'view_changed'
        value['context_saved'] = str(context_saved)
        return {
            'value': value,
            'domain': domain,
        }

    def onchange_partner_id(
        self, cr, uid, ids, partner_id, context_saved, context=None
    ):
        context_saved = leval(context_saved)
        domain = deepcopy(move_line_domain)
        if (
            context_saved['state_line_ids'] == 'entering_wizard' or
            not partner_id
        ):
            return {
                'value': {},
                'domain': {'line_ids': domain}
            }
        domain.append(('partner_id', '=', partner_id))
        list_ids = context_saved['lines_by_partner'][partner_id]
        context_saved['state_line_ids'] = 'partner_changed'
        res = {
            'value': {
                'line_ids': [(6, 0, list_ids)],
                'context_saved': str(context_saved),
            },
            'domain': {'line_ids': domain},
        }
        conflicts = self._get_account_conflicts(
            cr, uid, list_ids, context=context
        )
        if conflicts:
            res['warning'] = {
                'title': _('Warning'),
                'message': self._print_conflicts(
                    cr, uid, conflicts, context=context
                )
            }
        return res

    def __compile_list_dict(self, list_dict):
        """ This function compile the list of dict into
            a dict of list with an easier format
            i.e: [{'partner_id: (3556, name1), 'id': 20},
                  {'partner_id: (5024, name2), 'id': 53},
                  {'partner_id: (3556, name1), 'id': 59}]
            ->  {3556: [20, 59], 5024: [53]}
        """

        res = {}
        if len(list_dict) == 0:
            return res

        for _dict in list_dict:
            if not _dict['partner_id'][0] in res:
                res[_dict['partner_id'][0]] = [_dict['id']]
            else:
                res[_dict['partner_id'][0]].append(_dict['id'])

        return res

    def __calcul_partner_domain(self, uid, context):
        return {
            'partner_id': [('id', 'in', context['lines_by_partner'].keys())]
        }

    def __entering_wizard(self, cr, uid, ids, list_ids, context):
        move_line_osv = self.pool['account.move.line']
        reads = move_line_osv.read(
            cr, uid, list_ids, ['partner_id'], context=context
        )

        # The "partner_id" field of accounting lines is not compulsory; we
        # however need it to produce vouchers.
        line_ids_wo_partner = [
            read['id'] for read in reads if not read['partner_id']
        ]
        if line_ids_wo_partner:
            lines_wo_partner = move_line_osv.browse(
                cr, uid, line_ids_wo_partner, context=context
            )
            moves_wo_partner = u", ".join({
                line_wo_partner.id: line_wo_partner.move_id.name
                for line_wo_partner in lines_wo_partner
            }.itervalues())
            raise osv.except_osv(
                _(u"Error"),
                _(
                    u"Partners undefined in the following accounting move "
                    u"entries: %s."
                ) % moves_wo_partner
            )

        context['lines_by_partner'] = self.__compile_list_dict(reads)
        res = {
            'value': {
                'view_selection': 'complete',
                'context_saved': context,
            },
            'domain': self.__calcul_partner_domain(uid, context),
        }
        conflicts = self._get_account_conflicts(
            cr, uid, list_ids, context=context
        )
        if conflicts:
            res['warning'] = {
                'title': _('Warning'),
                'message': self._print_conflicts(
                    cr, uid, conflicts, context=context
                )
            }
        return res

    def __substract_wo_dups(self, src, dest):
        return list(set(dest) - set(src))

    def __check_add_del(self, uid, ids, context):
        """ -1 : del, 0: equal (should not happen), 1: add
        """

        src_set = set(
            itertools.chain.from_iterable(
                context['lines_by_partner'].values()
            )
        )
        dst_set = set(ids)

        if dst_set - src_set:
            return 1, dst_set - src_set
        if src_set - dst_set:
            return -1, src_set - dst_set
        return 0, []

    def __delete_line(self, diff, uid, context):
        res = {}
        line = list(diff)[0]
        for key, value in context['lines_by_partner'].items():
            if line in context['lines_by_partner'][key]:
                context['lines_by_partner'][key] = list(set(value) - diff)
                if not context['lines_by_partner'][key]:
                    del context['lines_by_partner'][key]
                    res['partner_id'] = None
                    res['view_selection'] = 'complete'
                    res['context_saved'] = context
        return res

    def __add_line(self, cr, uid, ids, context):
        move_line_osv = self.pool['account.move.line']
        reads = move_line_osv.read(
            cr, uid, ids, ['partner_id'], context
        )
        reads = [read for read in reads if read['partner_id']]
        dict_ids = self.__compile_list_dict(reads)
        for partner_id in dict_ids.keys():
            if partner_id in context['lines_by_partner']:
                context['lines_by_partner'][partner_id].extend(
                    self.__substract_wo_dups(
                        context['lines_by_partner'][partner_id],
                        dict_ids[partner_id]
                    )
                )
            else:
                context['lines_by_partner'][partner_id] = dict_ids[partner_id]
        return {'context_saved': context}

    def __compute_sum_and_nb_lines(self, cr, uid, context):
        res = {}
        line_ids = itertools.chain.from_iterable(
            context['lines_by_partner'].values()
        )
        aml_osv = self.pool['account.move.line']
        reads = aml_osv.read(cr, uid, line_ids, ['credit', 'debit'], context)
        total_credit = reduce(
            lambda x, y: x + y, [read['credit'] for read in reads]
        )
        total_debit = reduce(
            lambda x, y: x + y, [read['debit'] for read in reads]
        )
        res['total_amount'] = total_credit - total_debit
        res['nb_lines'] = len(reads)
        return res

    def __add_del_element(
        self, cr, uid, ids, selector, partner_id, list_ids, context
    ):

        values = {}
        type, diff = self.__check_add_del(uid, list_ids, context)
        if type == -1:
            values = self.__delete_line(diff, uid, context)
        elif type == 1:
            values = self.__add_line(cr, uid, diff, context)
        else:
            return {'value': {}}

        return {
            'domain': self.__calcul_partner_domain(uid, context),
            'value': values
        }

    def __view_changed(self, cr, uid, ids, list_ids, context):
        context['state_line_ids'] = None
        return {'value': {'context_saved': context}}

    def __partner_changed(self, cr, uid, ids, list_ids, context):
        context['state_line_ids'] = None
        return {'value': {'context_saved': context}}

    def onchange_line_ids(
        self, cr, uid, ids, selector, partner_id,
        line_ids, context_saved, context=None
    ):
        """ print the line selected or the line filtered by state
            4 states : 'entering_wizard'
                       'view_changed'
                       'partner_changed
                       'add_del_element' = None
        """

        context_saved = leval(context_saved)

        # We cut the ids from the magic tuple [(6, False, [ids])]
        list_ids = line_ids[0][2]

        res = {}

        # and we store the ids in the many2many
        # depending on the state we are.
        if context_saved['state_line_ids'] == 'entering_wizard':
            res = self.__entering_wizard(cr, uid, ids, list_ids, context_saved)
        elif not context_saved['state_line_ids']:
            res = self.__add_del_element(
                cr, uid, ids, selector, partner_id, list_ids, context_saved
            )
        elif context_saved['state_line_ids'] == 'partner_changed':
            res = self.__partner_changed(cr, uid, ids, list_ids, context_saved)
        elif context_saved['state_line_ids'] == 'view_changed':
            res = self.__view_changed(cr, uid, ids, list_ids, context_saved)
        if context_saved['lines_by_partner']:
            res['value'].update(
                self.__compute_sum_and_nb_lines(cr, uid, context_saved)
            )
        else:
            res['value'].update(
                {'nb_lines': 0, 'total_amount': 0.0}
            )

        res['value']['context_saved'] = str(
            res.get('context_saved', context_saved)
        )

        return res
