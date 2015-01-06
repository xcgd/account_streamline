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

from openerp.osv import fields, expression, osv
from openerp.tools.translate import _
from lxml import etree
from openerp.addons.analytic_structure.MetaAnalytic import MetaAnalytic


class res_partner_needaction(osv.Model):
    __metaclass__ = MetaAnalytic
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread', 'ir.needaction_mixin']

    def _check_supplier_account(self, cr, uid, ids, name, args, context=None):
        account_osv = self.pool.get('account.account')
        res = dict()
        partners = self.browse(cr, uid, ids, context=context)

        for partner in partners:

            acc_pay = partner.property_account_payable
            if acc_pay and acc_pay.id:
                account = account_osv.browse(
                    cr, uid, acc_pay.id, context=context
                )

                payable = account.type == 'payable'
                res[partner.id] = partner.supplier and not payable

            else:
                res[partner.id] = False

        return res

    def _check_customer_account(self, cr, uid, ids, name, args, context=None):
        account_osv = self.pool.get('account.account')
        res = dict()
        partners = self.browse(cr, uid, ids, context=context)

        for partner in partners:

            acc_rec = partner.property_account_receivable
            if acc_rec and acc_rec.id:
                account = account_osv.browse(
                    cr, uid, acc_rec.id
                )

                receivable = account.type == 'receivable'
                res[partner.id] = partner.customer and not receivable

            else:
                res[partner.id] = False

        return res

    _track = {
        'property_account_payable': {
            'account_streamline.mt_partner_supplier': (
                lambda self, cr, uid, obj, ctx=None: (
                    not self.pool.get('account.account').browse(
                        cr, uid,
                        obj['property_account_payable'].id,
                        context=ctx
                    ).type == 'payable'
                )
            )
        },
        'property_account_receivable': {
            'account_streamline.mt_partner_customer': (
                lambda self, cr, uid, obj, ctx=None: (
                    not self.pool.get('account.account').browse(
                        cr, uid,
                        obj['property_account_receivable'].id
                    ).type == 'receivable'
                )
            )
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
    )

    _analytic = 'res_partner'

    # To prevent partner duplication
    _sql_constraints = [
        ('name', 'UNIQUE (name)', 'The name of the partner must be unique!')
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

            dom = expression.OR([
                expression.normalize_domain(mydom),
                expression.normalize_domain(dom)
            ])

        return dom
