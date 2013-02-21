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

    def _check_supplier_account(self, cr, uid, obj, context=None):
        print "*"*35
        print obj
        print dir(obj)
        print obj['supplier']
        print obj.property_account_payable.type
        res = obj['supplier'] and not obj.property_account_payable.type == 'payable'
        return res

    def _check_customer_account(self, cr, uid, obj, context=None):
        print "*"*35
        print obj['customer']
        print obj.property_account_receivable.type
        res = obj['customer'] and not obj.property_account_receivable.type == 'receivable'
        return res

    _track = {
        #'property_account_payable': {
        #    'account_streamline.mt_partner_supplier': _check_supplier_account,
        #    },
        #'property_account_receivable': {
        #    'account_streamline.mt_partner_customer': _check_customer_account,
        #    },
        }

    def create(self, cr, uid, values, context=None):
        """ Override to control notifications """
        if context is None:
            context = {}
        context.update(
            {'mail_create_nolog': True, 'mail_create_nosubscribe': True})

        cur_id = super(res_partner_needaction, self).create(
            cr, uid, values, context=context)
        new_partner = self.browse(cr, uid, cur_id, context=context)

        if self._check_supplier_account(cr, uid, new_partner):
            self.message_post(
                cr, uid, cur_id, type='comment',
                subtype='account_streamline.mt_partner_supplier',
                context=context)

        elif self._check_customer_account(cr, uid, new_partner):
            self.message_post(
                cr, uid, cur_id, type='comment',
                subtype='account_streamline.mt_partner_customer',
                context=context)

        return cur_id

    def get_needaction_user_ids(self, cr, uid, ids, context=None):
        result = dict.fromkeys(ids)
        # retrieve users from accounts creators group which
        # comes from related module data
        obj = self.pool.get('ir.model.data')
        followers = obj.get_object(cr, uid, 'mail.message.group',
                                   'group_account_creators').member_ids

        for partner in self.browse(cr, uid, ids, context=context):
        # set the list void by default
            result[partner.id] = []
            # if partner is not correctly set:
            #  manager is required to perform an action
            if self._check_supplier_account(
                    cr, uid, partner, context=context
            ) or self._check_customer_account(
                    cr, uid, partner, context=context):

                result[partner.id] = [followers]

        return result

