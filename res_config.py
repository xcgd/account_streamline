# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2015 XCG Consulting (http://www.xcg-consulting.fr/)
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

import logging

from openerp.osv import fields, osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class account_streamline_configuration(osv.TransientModel):
    #_name = 'account_streamline.config.settings'
    _inherit = 'account.config.settings'

    _columns = {
        'allow_duplicate_ref_on_account_move_same_account': fields.boolean(
            "Allow duplicate (reference, account) on journals",
        ),
    }

    def get_default_allow_duplicate_ref_on_account_move_same_account(
        self, cr, uid, fields, context=None
    ):
        res = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        res['allow_duplicate_ref_on_account_move_same_account'] = \
            user.company_id.allow_duplicate_ref_on_account_move_same_account
        return res

    def set_allow_duplicate_ref_on_account_move_same_account(
        self, cr, uid, ids, context=None
    ):
        """Set this on the company of the user
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        company_id = user.company_id.id
        company_osv = self.pool['res.company']
        config_brl = self.browse(cr, uid, ids, context)
        for config_br in config_brl:
            val = {
                'allow_duplicate_ref_on_account_move_same_account':
                    config_br.allow_duplicate_ref_on_account_move_same_account,
            }
            company_osv.write(cr, uid, company_id, val, context=context)
