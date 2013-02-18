# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Analytic Online, for OpenERP
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

# fields that are considered as forbidden once the move_id has been posted
forbidden_fields = ["move_id"]

msg_invalid_move = _('You cannot add line(s) into an already posted entry')
msg_cannot_remove_line = _(
    'You cannot remove line(s) from an already posted entry')
msg_invalid_journal = _('You cannot move line(s) between journal types')


class account_move_line(osv.osv):
    _name = "account.move.line"
    _inherit = "account.move.line"

    _columns = dict(
        move_state=fields.related("move_id", "state",
                                  type="char", string="status", readonly=True)
    )

    def is_move_posted(self, cr, uid, move_id, context=None):
        """internal helper function
        """
        move_osv = self.pool.get('account.move')

        if move_id:
            move = move_osv.browse(cr, uid, move_id, context=context)
            return move.state == 'posted'

    def write(self, cr, uid, ids, vals, context=None, check=True,
              update_check=True):
        """re-implement the write method to enforce stricter security rules on
        the account.move.line / account.move relationship related to the
        posted status
        """
        target_move_id = vals.get('move_id', False)

        target_journal_id = None
        if target_move_id:
            move_osv = self.pool.get('account.move')
            target_journal_id = move_osv.browse(cr, uid, target_move_id,
                                                context=context).journal_id.id

        for aml in self.browse(cr, uid, ids, context=context):

            current_move = getattr(aml, 'move_id', None)
            if current_move:
                current_move_id = aml.move_id.id
                current_journal_id = aml.move_id.journal_id

            else:
                current_move_id = None
                current_journal_id = None


            # if the user tries to move away a line from an account_move which
            # if already posted
            if current_move_id and self.is_move_posted(
                    cr, uid, current_move_id, context=context) and \
                target_move_id and \
                    not current_move_id == target_move_id:
                raise osv.except_osv(_('Error!'), msg_cannot_remove_line)

            # if the user is trying to move an acm into an account_move
            #  which is posted
            if target_move_id and not target_move_id == current_move_id and \
                    self.is_move_posted(
                        cr, uid, target_move_id, context=context):
                raise osv.except_osv(_('Error!'), msg_invalid_move)

            # we don't allow switching from one journal_id (journal type)
            #  to the other even for draft entries
            if target_journal_id and \
                    not target_journal_id == current_journal_id:
                raise osv.except_osv(_('Error!'), msg_invalid_journal)

        return super(account_move_line, self).write(
            cr, uid, ids, vals,
            context=context, check=check,
            update_check=update_check)

    def create(self, cr, uid, vals, context=None):
        move_id = vals.get('move_id', False)

        if self.is_move_posted(cr, uid, move_id, context=context):
            raise osv.except_osv(_('Error!'), msg_invalid_move)

        return super(account_move_line, self).create(cr, uid, vals,
                                                     context=context)

