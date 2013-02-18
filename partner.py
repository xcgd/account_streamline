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

    _track = {
        'property_account_payable': {
            'purchase.mt_partner_supplier': lambda self, cr, uid, obj, ctx=None:
            obj['supplier'] and not obj.property_account_payable.type == 'payable',
            },
        'property_account_receivable': {
            'purchase.mt_partner_customer': lambda self, cr, uid, obj, ctx=None:
            obj['customer'] and not obj.property_account_receivable.type == 'receivable',
            },
        }