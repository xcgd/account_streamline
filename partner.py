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

from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit =  ['res.partner','mail.thread', 'ir.needaction_mixin']

    def _check_supplier_account(self, cr, uid, obj, ctx=None):
        print "*"*35
        print obj['supplier']
        print obj.property_account_payable.type
        res = obj['supplier'] and not obj.property_account_payable.type == 'payable'
        return res

    def _check_customer_account(self, cr, uid, obj, ctx=None):
        print "*"*35
        print obj['customer']
        print obj.property_account_receivable.type
        res = obj['customer'] and not obj.property_account_receivable.type == 'receivable'
        return res

    _track = {
        'property_account_payable': {
            'partner.mt_partner_supplier': _check_supplier_account,
            },
        'property_account_receivable': {
            'partner.mt_partner_customer': _check_customer_account,
            },
        }