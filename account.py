# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 XCG Consulting (www.xcg-consulting.fr)
#                  2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import tools
from openerp.osv import fields, osv
from lxml import etree
from openerp.addons.analytic_structure.MetaAnalytic import MetaAnalytic

CTL_SELECTION = (
    ('1', 'Mandatory'),
    ('2', 'Optional'),
    ('3', 'Forbidden')
)

class account_account(osv.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    _columns = {

    'is_limited':fields.boolean(
        u"Limited access",
        help="When selected, only the financial manager can read and write",),
    }

    # Cherry pick of http://bazaar.launchpad.net/~openerp-dev/openobject-addons/7.0-opw-591897-acl/revision/9115#account/account.py
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        old_ctx = context
        context = old_ctx.copy() if old_ctx else {}
        split_args = []
        pos = 0
        while pos < len(args):

            if args[pos][0] == 'code' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('code', '=like', tools.ustr(args[pos][2].replace('%', ''))+'%')
            if args[pos][0] == 'journal_id':
                if not args[pos][2]:
                    del args[pos]
                    continue
                jour = self.pool.get('account.journal').browse(cr, uid, args[pos][2], context=context)
                if (not (jour.account_control_ids or jour.type_control_ids)) or not args[pos][2]:
                    args[pos] = ('type','not in',('consolidation','view'))
                    continue
                ids3 = map(lambda x: x.id, jour.type_control_ids)
                ids1 = super(account_account, self).search(cr, uid, [('user_type', 'in', ids3)])
                ids1 += map(lambda x: x.id, jour.account_control_ids)
                args[pos] = ('id', 'in', ids1)

            # needed to ligthen request sent to postgres in chart of accounts : when requesting child ofg
            # large amount of accounts, the request is too long for being processed by postgres. 
            # this mainly happens with leafs account
            if args[pos][0] == 'parent_id' and args[pos][1] == 'child_of' and args[pos][2] and isinstance(args[pos][2], list):
                split_size = 1000
                ids = args[pos][2][:]
                for i in range(len(ids)/split_size+1):
                    split_args.append(args[:])
                    split_args[i][pos] = (args[pos][0],args[pos][1],ids[split_size*i:split_size*(i+1)])

            pos += 1

        if split_args:
            results = []
            for arg in split_args:
                results.extend(super(account_account, self).search(cr, uid, arg,
                                                                   offset, limit, order, context=context, count=count))
            ids = list(results)
        else:
            ids = super(account_account, self).search(cr, uid, args, offset, limit,
                                                      order, context=context, count=count)

        if context and context.has_key('consolidate_children'): #add consolidated children of accounts
            for consolidate_child in self.browse(cr, uid, context['account_id'], context=context).child_consol_ids:
                ids.append(consolidate_child.id)

        return ids

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

    'is_limited':fields.boolean(
        u"Limited access",
        help="When selected, only the financial manager can read and write",),
    }
