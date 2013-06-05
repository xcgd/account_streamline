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


class account_voucher_line(osv.osv):
    """override the store=True on amount_original and amount_unreconciled
    to make sure that even if a line if changed or the invoice partially paid
    the voucher calculation is up to date (this makes the supplier payment
    process work as expected even if another voucher partially or totally paid
    the invoice before a voucher tries to pay the same invoice.
    """
    _name = "account.voucher.line"
    _inherit = "account.voucher.line"

    def _compute_balance(self, *args, **kwargs):
        return super(account_voucher_line, self)._compute_balance(
            *args, **kwargs)

    _columns = {
        'amount_original': fields.function(
            _compute_balance,
            multi='dc',
            type='float',
            string='Original Amount',
            store=False,
            digits_compute=dp.get_precision('Account')
        ),
        'amount_unreconciled': fields.function(
            _compute_balance,
            multi='dc',
            type='float',
            string='Open Balance',
            store=False,
            digits_compute=dp.get_precision('Account')
        ),
    }
