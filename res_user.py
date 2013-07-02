# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Fiche Action Budget Management, for OpenERP
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

from openerp.osv import osv, fields

class res_users(osv.Model):
    '''
    This extends the base user to look up for a matching employee
    @returns a dict with k=user.id and v=first matching employee. k is not set if no employee is found
    '''

    _name = 'res.users'
    _inherit = 'res.users'

    def _get_employee_id(self, cr, uid, ids, name, arg, context=None):
        result = dict()

        employee_osv = self.pool.get('hr.employee')
        for user in self.browse(cr, uid, ids, context=context):
            args = [('user_id', '=', user.id), ]
            ids = employee_osv.search(cr, uid, args, context=context)
            if ids:
                result[user.id] = ids[0]

        return result

    _columns = {
        'employee_id': fields.function(_get_employee_id, type='many2one', obj="hr.employee"),
        }

res_users()

