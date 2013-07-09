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
from openerp.tools.translate import _
from lxml import etree


class res_partner_needaction(osv.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread', 'ir.needaction_mixin']

    def _check_supplier_account(self, cr, uid, ids, name, args, context=None):
        account_osv = self.pool.get('account.account')
        res = dict()
        for partner in self.browse(cr, uid, ids, context=context):
            account = account_osv.browse(
                cr, uid, partner.property_account_payable.id)

            payable = account.type == 'payable'
            res[partner.id] = partner.supplier and not payable

        return res

    def _check_customer_account(self, cr, uid, ids, name, args, context=None):
        account_osv = self.pool.get('account.account')
        res = dict()
        for partner in self.browse(cr, uid, ids, context=context):
            account = account_osv.browse(
                cr, uid,
                partner.property_account_receivable.id
            )

            receivable = account.type == 'receivable'
            res[partner.id] = partner.customer and not receivable

        return res

    _track = {
        'property_account_payable': {
            'account_streamline.mt_partner_supplier': lambda self,
            cr, uid, obj, ctx=None:
            not self.pool.get(
                'account.account').browse(
                    cr, uid,
                    obj['property_account_payable']
                ).type == 'payable',
        },
        'property_account_receivable': {
            'account_streamline.mt_partner_customer': lambda self,
            cr, uid, obj, ctx=None:
            not self.pool.get(
                'account.account').browse(
                    cr, uid,
                    obj['property_account_receivable']
                ).type == 'receivable',
        },
    }

    _columns = dict(
        supplier_account_check=fields.function(_check_supplier_account,
                                               string='Check Supplier Account',
                                               type='boolean',
                                               store=True),
        customer_account_check=fields.function(_check_customer_account,
                                               string='Check Customer Account',
                                               type='boolean',
                                               store=True),
        siret=fields.char('SIRET', size=14),
        siren=fields.char('SIREN', size=9),

        a1_id=fields.many2one(
            'analytic.code', "Analysis Code 1",
            domain=[
                ('nd_id.ns_id.model_name', '=', 'res_partner'),
                ('nd_id.ns_id.ordering', '=', '1'),
            ]
        ),
        a2_id=fields.many2one(
            'analytic.code', "Analysis Code 1",
            domain=[
                ('nd_id.ns_id.model_name', '=', 'res_partner'),
                ('nd_id.ns_id.ordering', '=', '2'),
            ]
        ),
        a3_id=fields.many2one(
            'analytic.code', "Analysis Code 1",
            domain=[
                ('nd_id.ns_id.model_name', '=', 'res_partner'),
                ('nd_id.ns_id.ordering', '=', '3'),
            ]
        ),
        a4_id=fields.many2one(
            'analytic.code', "Analysis Code 1",
            domain=[
                ('nd_id.ns_id.model_name', '=', 'res_partner'),
                ('nd_id.ns_id.ordering', '=', '4'),
            ]
        ),
        a5_id=fields.many2one(
            'analytic.code', "Analysis Code 1",
            domain=[
                ('nd_id.ns_id.model_name', '=', 'res_partner'),
                ('nd_id.ns_id.ordering', '=', '5'),
            ]
        ),
    )
    
    #To prevent partner duplication
    _sql_constraints = [ 
        ('name', 'UNIQUE (name)', 'The name of the partner must be unique !') 
    ] 

    ##################################################
    # -------------------Override------------------- #
    ##################################################
    
    # Needaction mechanism stuff

    def create(self, cr, uid, values, context=None):
        """ Override to control notifications """
        if context is None:
            context = {}
        context.update(
            {'mail_create_nolog': True, 'mail_create_nosubscribe': True})

        cur_id = super(res_partner_needaction, self).create(
            cr, uid, values, context=context)

        obj = self.pool.get('ir.model.data')
        followers = [
            follower.id for follower in obj.get_object(
                cr, uid, 'account_streamline', 'group_account_creators'
            ).message_follower_ids
        ]
        msg_cust = obj.get_object(
            cr, uid,
            'account_streamline', 'mt_partner_customer'
        ).id

        msg_supp = obj.get_object(
            cr, uid,
            'account_streamline', 'mt_partner_supplier'
        ).id

        subtypes = [msg_cust, msg_supp]

        self.message_subscribe(cr, uid, [cur_id], followers, subtypes,
                               context=context)

        account_osv = self.pool.get('account.account')
        supplier = values.get('supplier', None)
        customer = values.get('customer', None)
        p_accnt_receivable = values.get('property_account_receivable', False)
        p_accnt_payable = values.get('property_account_payable', False)

        if supplier and p_accnt_payable and not account_osv.browse(
            cr, uid, p_accnt_payable
        ).type == 'payable':

            self.message_post(
                cr, uid, cur_id,
                subtype='account_streamline.mt_partner_supplier',
                body=_("Supplier created, please check related account."),
                context=context)

        if customer and p_accnt_receivable and not account_osv.browse(
            cr, uid, p_accnt_receivable
        ).type == 'receivable':

            self.message_post(
                cr, uid, cur_id,
                subtype='account_streamline.mt_partner_customer',
                body=_("Customer created, please check related account."),
                context=context)

        return cur_id

    def _needaction_domain_get(self, cr, uid, context=None):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        # get domain from parent object if exists
        dom = super(res_partner_needaction, self)._needaction_domain_get(
            cr, uid, context=context)
        obj = self.pool.get('ir.model.data')
        followers = obj.get_object(
            cr, uid,
            'account_streamline',
            'group_account_creators'
        ).message_follower_ids

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        if user.partner_id in followers:
            mydom = [
                '|', ('supplier_account_check', '=', True),
                ('customer_account_check', '=', True),
            ]

            dom = ['|'] + mydom + dom

        return dom
    
    # View stuff

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
        Override filds_view_get to display analytic dimensions using
        analytic structure on res_partner
        """

        if context is None:
            context = {}

        res = super(
            res_partner_needaction, self
        ).fields_view_get(
            cr, uid, view_id=view_id,
            view_type=view_type, context=context,
            toolbar=toolbar, submenu=False
        )

        ans_obj = self.pool.get('analytic.structure')

        #display analysis codes only when present on a related structure,
        # with dimension name as label
        ans_ids = ans_obj.search(
            cr, uid,
            [
                ('model_name', '=', 'res_partner'),
            ],
            context=context
        )

        ans_br = ans_obj.browse(cr, uid, ans_ids, context=context)
        ans_dict = dict()
        for ans in ans_br:
            ans_dict[ans.ordering] = ans.nd_id.name

        doc = etree.XML(res['arch'])

        pattern = '{"invisible": %(invisible)s,' \
                  ' "tree_invisible": %(invisible)s}'

        if 'a1_id' in res['fields']:
            res['fields']['a1_id']['string'] = ans_dict.get('1', 'A1')
            doc.xpath("//field[@name='a1_id']")[0].set(
                'modifiers',
                pattern % {
                    'invisible': str(not '1' in ans_dict).lower()
                }
            )

        if 'a2_id' in res['fields']:
            res['fields']['a2_id']['string'] = ans_dict.get('2', 'A2')
            doc.xpath("//field[@name='a2_id']")[0].set(
                'modifiers',
                pattern % {
                    'invisible': str(not '2' in ans_dict).lower()
                }
            )

        if 'a3_id' in res['fields']:
            res['fields']['a3_id']['string'] = ans_dict.get('3', 'A3')
            doc.xpath("//field[@name='a3_id']")[0].set(
                'modifiers',
                pattern % {
                    'invisible': str(not '3' in ans_dict).lower()
                }
            )

        if 'a4_id' in res['fields']:
            res['fields']['a4_id']['string'] = ans_dict.get('4', 'A4')
            doc.xpath("//field[@name='a4_id']")[0].set(
                'modifiers',
                pattern % {
                    'invisible': str(not '4' in ans_dict).lower()
                }
            )

        if 'a5_id' in res['fields']:
            res['fields']['a5_id']['string'] = ans_dict.get('5', 'A5')
            doc.xpath("//field[@name='a5_id']")[0].set(
                'modifiers',
                pattern % {
                    'invisible': str(not '5' in ans_dict).lower()
                }
            )

        res['arch'] = etree.tostring(doc)

        return res

