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


class res_partner_needaction(osv.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread', 'ir.needaction_mixin']

    def _check_supplier_account(self, cr, uid, ids, name, args, context=None):
        res = dict()
        for partner in self.browse(cr, uid, ids, context=context):
            account = self.pool.get('account.account').browse(cr, uid,
                                            partner.property_account_payable)
            res[partner.id] = partner.supplier and\
                not account.type == 'payable'
        return res

    def _check_customer_account(self, cr, uid, ids, name, args, context=None):
        res = dict()
        for partner in self.browse(cr, uid, ids, context=context):
            account = self.pool.get('account.account').browse(cr, uid,
                                            partner.property_account_payable)
            res[partner.id] = partner.customer and\
                not account.type == 'receivable'
        return res

    _track = {
        'property_account_payable': {
            'account_streamline.mt_partner_supplier': lambda self,
                        cr, uid, obj, ctx=None:
            self.pool.get('account.account').browse(cr, uid,
                        obj['property_account_payable']).type == 'payable',
            },
        'customer_account_check': {
            'account_streamline.mt_partner_customer': lambda self,
                        cr, uid, obj, ctx=None:
            self.pool.get('account.account').browse(cr, uid,
                        obj['property_account_receivable']).type == 'receivable',
            },
        }

    _columns = dict(
        supplier_account_check = fields.function(_check_supplier_account,
                                                 type='boolean'),
        customer_account_check = fields.function(_check_customer_account,
                                                 type='boolean'),
    )

    def create(self, cr, uid, values, context=None):
        """ Override to control notifications """
        if context is None:
            context = {}
        context.update(
            {'mail_create_nolog': True, 'mail_create_nosubscribe': True})

        cur_id = super(res_partner_needaction, self).create(
            cr, uid, values, context=context)

    #     if values['supplier_account_check']:
    #         self.message_post(
    #             cr, uid, cur_id,
    #             subtype='account_streamline.mt_partner_supplier',
    #             body=_("Supplier created, please check related account."),
    #             context=context)
    #
    #     if values['customer_account_check']:
    #         self.message_post(
    #             cr, uid, cur_id,
    #             subtype='account_streamline.mt_partner_customer',
    #             body=_("Customer created, please check related account."),
    #             context=context)
    #
        return cur_id

    def _needaction_domain_get(self, cr, uid, context=None):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        # get domain from parent object if exists
        dom = super(res_partner_needaction, self)._needaction_domain_get(
            cr, uid, context=context)
        obj = self.pool.get('ir.model.data')
        followers = obj.get_object(cr, uid, 'account_streamline',
                                   'group_account_creators').message_follower_ids
        if uid in followers:
            dom = ['|'] + dom + [
                ('|', 'supplier_account_check', '=', 1),
                ('customer_account_check', '=', 1),
            ]

        print '*'*35
        print dom

        return dom

