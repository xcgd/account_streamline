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
from openerp.tools.translate import _
from collections import defaultdict
import itertools

msg_invalid_line_type = _('Account type %s is not usable in payment vouchers.')
msg_invalid_partner_type = _('Partner %s is not a supplier.')
msg_define_dc_on_journal = _(
    'Please define default credit/debit accounts on the journal "%s".')


class good_to_pay(osv.osv_memory):
    """create vouchers for all invoices that have been selected
    """


    class __container:
        lines = set()
        partner_dict = {}

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
        'journal_id': fields.many2one('account.journal',
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
    }

    _defaults = {
        'generate_report': lambda *a: True,
    }

    __lines_by_partner = {}
    __state_line_ids = {}

    def default_get(self, cr, uid, field_list=None, context=None):
        if not uid in self.__lines_by_partner:
            self.__lines_by_partner[uid] = {}
        self.__state_line_ids[uid] = 'entering_wizard'
        if not 'active_ids' in context:
            return {}
        vals = {}
        move_lines = [(6, 0, context['active_ids'])]
        vals['view_complete'] = 'complete'
        vals['line_ids'] = move_lines
        return vals

    def _generate_report(self, cr, uid, active_ids, context=None):
        ''' Generate a Payment Suggestion report. '''

        # active_ids contains move-line ids; remove them or the payment
        # suggestion object will use them by default.
        if 'active_ids' in context:
            del context['active_ids']

        return (self.pool.get('payment.suggestion')
                .print_payment_suggestion(cr, uid, active_ids,
                                          context=context))

    def __check_no_debit_line(self, cr, uid, context):
        aml_osv = self.pool.get('account.move.line')

        for partner_id, line_ids in self.__lines_by_partner[uid].items():
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

    def good_to_pay(self, cr, uid, ids, context=None):
        test, error = self.__check_no_debit_line(cr, uid, context)
        if not test:
            raise osv.except_osv(
                _('Error'),
                _('The voucher for the partner %s is debit.' % error)
            )

        aml_osv = self.pool.get('account.move.line')
        avl_osv = self.pool.get('account.voucher.line')
        voucher_osv = self.pool.get('account.voucher')
        journal_osv = self.pool.get('account.journal')

        supplier_to_voucher_map = dict()
        voucher_amounts = dict()

        action = {'type': 'ir.actions.act_window_close'}

        for form in self.read(cr, uid, ids, context=context):
            auto = form['generate_report']
            active_ids = list(
                itertools.chain.from_iterable(
                    self.__lines_by_partner[uid].values()
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

                #if aml.reconcile_id:
                #    msg = msg_already_reconciled % aml.partner_id.name
                #    raise osv.except_osv(_('Error!'), msg)
                partner_id = aml.partner_id.id
                partner = aml.partner_id

                if not partner_id in supplier_to_voucher_map:
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

                    if not journal.default_credit_account_id or \
                            not journal.default_debit_account_id:
                        raise osv.except_osv(
                            _('Error!'),
                            msg_define_dc_on_journal % journal.name)

                    account_id = journal.default_credit_account_id.id or \
                        journal.default_debit_account_id.id

                    vals['account_id'] = account_id
                    
                    bank_osv = self.pool.get("res.partner.bank")
                    bank_id =  bank_osv.search(
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
                line_vals['account_id'] = partner.property_account_payable.id
                line_vals['type'] = 'dr'
                line_vals['move_line_id'] = aml.id

                avl_id = avl_osv.create(cr, uid, line_vals, context=context)
                avl = avl_osv.browse(cr, uid, avl_id, context=context)

                line_vals2 = dict()
                line_vals2['reconcile'] = True
                line_vals2['amount'] = avl.amount_unreconciled

                avl_osv.write(cr, uid, [avl_id], line_vals2)
                voucher_amounts[voucher_id] += avl.amount_unreconciled

            # once every voucher is finished we recompute the voucher totals
            # and write them back to the vouchers
            for voucher_id in voucher_amounts.keys():
                voucher_osv.write(
                    cr, uid, [voucher_id],
                    {'amount': voucher_amounts[voucher_id]})
            if auto:
                action = self._generate_report(cr, uid, voucher_amounts.keys(), context)

        return action

    def onchange_view_selector(self, cr, uid, ids, selector, partner_id, context=None):
        if self.__state_line_ids[uid] == 'entering_wizard':
            self.__state_line_ids[uid] = None
            return {'value': {}}
        domain = {}
        value = {}
        if not selector:
            selector = 'complete'
            value['view_selection'] = 'complete'
        list_ids = []
        if selector == 'complete':
            list_ids = list(
                itertools.chain.from_iterable(
                    self.__lines_by_partner[uid].values()
                )
            )
            partner_id = None
        else:
            if self.__lines_by_partner[uid] and partner_id != self.__lines_by_partner[uid].keys()[0]:
                partner_id = self.__lines_by_partner[uid].keys()[0]
            else:
                domain['line_ids'] = [('partner_id', '=', -1)]

        if list_ids:
            value['line_ids'] = [(6, 0, list_ids)]
        value['partner_id'] = partner_id
            
        self.__state_line_ids[uid] = 'view_changed'
        return {
            'value': value,
            'domain': domain
        }

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        domain = [
            '|',
            ('reconcile_id', '=', False),
            ('reconcile_partial_id', '!=', False),
            ('account_id.type', 'in', ['payable','receivable']),
            ('state', '=', 'valid'),
            ('move_id.state', '=', 'posted')
        ]
        if self.__state_line_ids[uid] == 'entering_wizard' or not partner_id:
            return {
                'value': {},
                'domain': { 'line_ids': domain }
            }
        domain.append(('partner_id', '=', partner_id))
        list_ids = self.__lines_by_partner[uid][partner_id]
        self.__state_line_ids[uid] = 'partner_changed'
        return {
            'value': { 'line_ids': [(6, 0, list_ids)] },
            'domain': { 'line_ids': domain }
        }

    def __compile_list_dict(self, list_dict):
        """ This function compile the list of dict into
            a dict of list with an easier format
            i.e: [{'partner_id: (3556, name1), 'id': 20},
                  {'partner_id: (5024, name2), 'id': 53},
                  {'partner_id: (3556, name1), 'id': 59}]
            ->  {3556: [20, 59], 5024: [53]}
        """

        if len(list_dict) == 0:
            return None

        res = defaultdict(list)

        for _dict in list_dict:
            res[_dict['partner_id'][0]].append(_dict['id'])
        
        return res

    def __calcul_partner_domain(self, uid):
        return {
            'partner_id': [('id', 'in', self.__lines_by_partner[uid].keys())]
        }

    def __entering_wizard(self, cr, uid, ids, list_ids, context):
        move_line_osv = self.pool.get('account.move.line')
        reads = move_line_osv.read(
            cr, uid, list_ids, ['partner_id'], context
        )
        reads = [read for read in reads if read['partner_id']]
        self.__lines_by_partner[uid] = self.__compile_list_dict(reads)
        return {
            'value': {
                'view_selection': 'complete',
            },
            'domain': self.__calcul_partner_domain(uid),
        }

    def __substract_wo_dups(self, src, dest):
        return list(set(dest) - set(src))

    def __check_add_del(self, uid, ids):
        """ -1 : del, 0: equal (should not happen), 1: add
        """


        src_set = set(
            itertools.chain.from_iterable(
                self.__lines_by_partner[uid].values()
            )
        )
        dst_set = set(ids)

        if dst_set - src_set:
            return 1, dst_set - src_set
        if src_set - dst_set:
            return -1, src_set - dst_set
        return 0, []
        
    def __delete_line(self, diff, uid):
        res = {}
        line = list(diff)[0]
        for key, value in self.__lines_by_partner[uid].items():
            if line in self.__lines_by_partner[uid][key]:
                self.__lines_by_partner[uid][key] = list(set(value) - diff)
                if not self.__lines_by_partner[uid][key]:
                    del self.__lines_by_partner[uid][key]
                    res['partner_id'] = None
                    res['view_selection'] = 'complete'
        return res

    def __add_line(self, cr, uid, ids, context):
        move_line_osv = self.pool.get('account.move.line')
        reads = move_line_osv.read(
            cr, uid, ids, ['partner_id'], context
        )
        reads = [read for read in reads if read['partner_id']]
        dict_ids = self.__compile_list_dict(reads)
        for partner_id in dict_ids.keys():
            if partner_id in self.__lines_by_partner[uid]:
                self.__lines_by_partner[uid][partner_id].extend(
                    self.__substract_wo_dups(
                        self.__lines_by_partner[uid][partner_id],
                        dict_ids[partner_id]
                    )
                )
            else:
                self.__lines_by_partner[uid][partner_id] = dict_ids[partner_id]
 
    def __compute_sum_and_nb_lines(self, cr, uid, context):
        res = {}
        line_ids = itertools.chain.from_iterable(
            self.__lines_by_partner[uid].values()
        )
        aml_osv = self.pool.get('account.move.line')
        reads = aml_osv.read(cr, uid, line_ids, ['credit', 'debit'], context)
        total_credit = reduce(lambda x, y: x + y, [read['credit'] for read in reads])
        total_debit = reduce(lambda x, y: x + y, [read['debit'] for read in reads])
        res['total_amount'] = total_credit - total_debit
        res['nb_lines'] = len(reads)
        return res


    def __add_del_element(self, cr, uid, ids, selector, partner_id, list_ids, context):

        values = {}
        type, diff = self.__check_add_del(uid, list_ids)
        if type == -1:
            values = self.__delete_line(diff, uid)
        elif type == 1:
            self.__add_line(cr, uid, diff, context)
        else:
            return { 'value': {}}

        return { 'domain': self.__calcul_partner_domain(uid),
                 'value': values}

    def __view_changed(self, cr, uid, ids, list_ids, context):
        return {'value': {}}

    def __partner_changed(self, cr, uid, ids, list_ids, context):
        return {'value': {}}

    def onchange_line_ids(self, cr, uid, ids, selector, partner_id, line_ids, context=None):
        """ print the line selected or the line filtered by state
            4 states : 'entering_wizard'
                       'view_changed'
                       'partner_changed
                       'add_del_element' = None
        """

        # We cut the ids from the magic tuple [(6, False, [ids])]
        list_ids = line_ids[0][2]

        res = {}

        # and we store the ids in the many2many
        # depending on the state we are.
        if self.__state_line_ids[uid] == 'entering_wizard':
            res = self.__entering_wizard(cr, uid, ids, list_ids, context)
        elif not self.__state_line_ids[uid]:
            res = self.__add_del_element(
                cr, uid, ids, selector, partner_id, list_ids, context
            )
        elif self.__state_line_ids[uid] == 'partner_changed':
            self.__state_line_ids[uid] = None
            res = self.__partner_changed(cr, uid, ids, list_ids, context)
        elif self.__state_line_ids[uid] == 'view_changed':
            self.__state_line_ids[uid] = None
            res = self.__view_changed(cr, uid, ids, list_ids, context)
        if self.__lines_by_partner[uid]:
            res['value'].update(self.__compute_sum_and_nb_lines(cr, uid, context))
        else:
            res['value'].update({'nb_lines': 0.0, 'total_amount': 0.0})

        return res
