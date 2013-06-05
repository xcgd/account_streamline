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

msg_invalid_line_type = _('Account type %s is not usable in payment vouchers.')
msg_invalid_partner_type = _('Partner %s is not a supplier.')
msg_define_dc_on_journal = _(
    'Please define default credit/debit accounts on the journal "%s".')


class good_to_pay(osv.osv_memory):
    """create vouchers for all invoices that have been selected
    """
    _name = "account.move.line.goodtopay"
    _description = "Payment selection for good to pay"
    _columns = dict(
        sure=fields.boolean(_("Check this box")),
        journal_id=fields.many2one('account.journal',
                                   'Journal',
                                   required=True,
                                   domain=[('type', 'in', ['bank', 'cash'])]
                                   ),
    )

    def good_to_pay(self, cr, uid, ids, context=None):
        aml_osv = self.pool.get('account.move.line')
        avl_osv = self.pool.get('account.voucher.line')
        voucher_osv = self.pool.get('account.voucher')
        journal_osv = self.pool.get('account.journal')

        supplier_to_voucher_map = dict()
        voucher_amounts = dict()

        for form in self.read(cr, uid, ids, context=context):
            if form['sure']:

                for aml in aml_osv.browse(
                        cr, uid, context['active_ids'], context=context):

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

        return {'type': 'ir.actions.act_window_close'}
