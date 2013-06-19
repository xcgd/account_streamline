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

CTL_SELECTION = (
    ('1', 'Mandatory'),
    ('2', 'Optional'),
    ('3', 'Forbidden')
)

class account_analytic_structure(osv.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    _columns = dict(
        a1_id=fields.many2one('analytic.code', "Analysis Code 1",
                              domain=[('nd_id.ns_id.model_name',
                                       '=', 'account_account'),
                                      ('nd_id.ns_id.ordering', '=', '1')]),
        a2_id=fields.many2one('analytic.code', "Analysis Code 2",
                              domain=[('nd_id.ns_id.model_name',
                                       '=', 'account_account'),
                                      ('nd_id.ns_id.ordering', '=', '2')]),
        a3_id=fields.many2one('analytic.code', "Analysis Code 3",
                              domain=[('nd_id.ns_id.model_name',
                                       '=', 'account_account'),
                                      ('nd_id.ns_id.ordering', '=', '3')]),
        a4_id=fields.many2one('analytic.code', "Analysis Code 4",
                              domain=[('nd_id.ns_id.model_name',
                                       '=', 'account_account'),
                                      ('nd_id.ns_id.ordering', '=', '4')]),
        a5_id=fields.many2one('analytic.code', "Analysis Code 5",
                              domain=[('nd_id.ns_id.model_name',
                                       '=', 'account_account'),
                                      ('nd_id.ns_id.ordering', '=', '5')]),
        t1_ctl=fields.selection(CTL_SELECTION, "T1 control", required=True),
        t2_ctl=fields.selection(CTL_SELECTION, "T2 control", required=True),
        t3_ctl=fields.selection(CTL_SELECTION, "T3 control", required=True),
        t4_ctl=fields.selection(CTL_SELECTION, "T4 control", required=True),
        t5_ctl=fields.selection(CTL_SELECTION, "T5 control", required=True),
    )

    _defaults = {
        't1_ctl': 2,
        't2_ctl': 2,
        't3_ctl': 2,
        't4_ctl': 2,
        't5_ctl': 2,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(account_analytic_structure,
                    self).fields_view_get(cr, uid, view_id=view_id,
                                          view_type=view_type,
                                          context=context,
                                          toolbar=toolbar,
                                          submenu=False)
        ans_obj = self.pool.get('analytic.structure')

        #display analysis codes only when present on a related structure,
        #with dimension name as label
        #so the full analysis structure is represented in a dict
        #TODO I chose to read the full structure but it may be limited to required analyzed models
        ans_ids = ans_obj.search(cr, uid,
                                 [(1, '=', 1)],
                                 context=context)
        ans_br = ans_obj.browse(cr, uid, ans_ids, context=context)
        ans_dict = dict()
        for ans in ans_br:
            if not ans.model_name in ans_dict:
                ans_dict[ans.model_name] = {}
            ans_dict[ans.model_name][ans.ordering] = ans.nd_id.name

        doc = etree.XML(res['arch'])

        if 'a1_id' in res['fields']:
            res['fields']['a1_id']['string'] = ans_dict.get('account_account', {}).get('1', 'A1')
            doc.xpath("//field[@name='a1_id']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '1' in ans_dict.get('account_account', {})).lower())
        if 'a2_id' in res['fields']:
            res['fields']['a2_id']['string'] = ans_dict.get('account_account', {}).get('2', 'A2')
            doc.xpath("//field[@name='a2_id']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '2' in ans_dict.get('account_account', {})).lower())
        if 'a3_id' in res['fields']:
            res['fields']['a3_id']['string'] = ans_dict.get('account_account', {}).get('3', 'A3')
            doc.xpath("//field[@name='a3_id']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '3' in ans_dict.get('account_account', {})).lower())
        if 'a4_id' in res['fields']:
            res['fields']['a4_id']['string'] = ans_dict.get('account_account', {}).get('4', 'A4')
            doc.xpath("//field[@name='a4_id']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '4' in ans_dict.get('account_account', {})).lower())
        if 'a5_id' in res['fields']:
            res['fields']['a5_id']['string'] = ans_dict.get('account_account', {}).get('5', 'A5')
            doc.xpath("//field[@name='a5_id']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '5' in ans_dict.get('account_account', {})).lower())
        if 't1_ctl' in res['fields']:
            res['fields']['t1_ctl']['string'] = ans_dict.get('account_move_line', {}).get('1', 'T1 control')
            doc.xpath("//field[@name='t1_ctl']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '1' in ans_dict.get('account_move_line', {})).lower())
        if 't2_ctl' in res['fields']:
            res['fields']['t2_ctl']['string'] = ans_dict.get('account_move_line', {}).get('2', 'T2 control')
            doc.xpath("//field[@name='t2_ctl']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '2' in ans_dict.get('account_move_line', {})).lower())
        if 't3_ctl' in res['fields']:
            res['fields']['t3_ctl']['string'] = ans_dict.get('account_move_line', {}).get('3', 'T3 control')
            doc.xpath("//field[@name='t3_ctl']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '3' in ans_dict.get('account_move_line', {})).lower())
        if 't4_ctl' in res['fields']:
            res['fields']['t4_ctl']['string'] = ans_dict.get('account_move_line', {}).get('4', 'T4 control')
            doc.xpath("//field[@name='t4_ctl']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '4' in ans_dict.get('account_move_line', {})).lower())
        if 't5_ctl' in res['fields']:
            res['fields']['t5_ctl']['string'] = ans_dict.get('account_move_line', {}).get('5', 'T5 control')
            doc.xpath("//field[@name='t5_ctl']")[0].\
                set('modifiers', '{"invisible": %s}' %
                    str(not '5' in ans_dict.get('account_move_line', {})).lower())

        res['arch'] = etree.tostring(doc)

        return res
