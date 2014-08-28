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
from lxml import etree
from openerp.addons.analytic_structure.MetaAnalytic import MetaAnalytic

CTL_SELECTION = (
    ('1', 'Mandatory'),
    ('2', 'Optional'),
    ('3', 'Forbidden')
)


class account_analytic_structure(osv.Model):
    __metaclass__ = MetaAnalytic
    _name = 'account.account'
    _inherit = 'account.account'

    _analytic = 'account_account'

    _para_analytic = {('t', 'ctl'): {
        'model': 'account_move_line',
        'type': fields.selection,
        'default': '2',
        'args': (CTL_SELECTION, "Move Line Analytic Control"),
        'kwargs': dict(required=True),
    }}
  
class account_journal(osv.Model):
	_name = 'account.journal'
	_inherit = 'account.journal'
	
	_columns = {
	
	'is_active':fields.boolean(
		u"Active in Reporting",
				),
				
	'account_id_is_limited':fields.boolean(
		u"Account limited",
				),
	}
