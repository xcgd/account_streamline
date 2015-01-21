##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2015 XCG Consulting (http://www.xcg-consulting.fr/)
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
from openerp.osv import fields, expression, osv
from openerp.tools.translate import _
import yaml
from lxml import etree
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

# account.move.line fields that don't become read-only when the account.move
# object is posted.
list_readonly_loose = [
    'date_maturity'
]
list_noreadonly = [
    'a1_id', 'a2_id', 'a3_id', 'a4_id', 'a5_id'
]

list_readonly_condition = (
    '[["move_state", "=", "posted"]]'
)
list_readonly_condition_loose = (
    '[["move_state", "=", "posted"], '
    '["reconcile_id", "!=", false]]'
)


class account_move(osv.Model):
    _name = 'account.move'

    _inherit = [
        'account.move',
        'mail.thread',
    ]

    def _links_get(self, cr, uid, context=None):
        """Gets links value for reference field"""
        obj = self.pool.get('res.request.link')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['object', 'name'], context)
        return [(r['object'], r['name']) for r in res]

    _columns = {
        # Redefine this field to remove the read-only constraint; it is however
        # carefully propagated to line fields via attributes inserted from the
        # fields_view_get function (except for fields we want to keep
        # modifiable).
        'line_id': fields.one2many(
            'account.move.line',
            'move_id',
            'Entries'
        ),
        'object_reference': fields.reference(
            u"Linked Object",
            selection=_links_get,
            size=128,
        )
    }

    def _analysis_control(self, cr, uid, ids, context=None):
        """This controls the account.move.line analysis dimensions settings
        set on account.account It will perform this only when attempting to
        post a complete move and will compile all errors coming from move
        lines in a single message
        """
        # move_dict = {}

        ans_obj = self.pool['analytic.structure']
        ans_dict = ans_obj.get_dimensions_names(
            cr, uid, 'account_move_line', context=context
        )
        required_lines = {}
        clear_lines = {key: [] for key in ans_dict.iterkeys()}
        for move in self.browse(cr, uid, ids, context=context):
            for aml in move.line_id:
                required_field_list = []
                for ordering, name in ans_dict.iteritems():
                    control_field = aml.account_id['t{0}_ctl'.format(ordering)]
                    analytic_field = aml['a{0}_id'.format(ordering)]
                    if control_field == '1' and not analytic_field:
                        required_field_list.append(name)
                    elif control_field == '3' and analytic_field:
                        clear_lines[ordering].append(aml.id)
                if required_field_list:
                    required_lines[aml.name] = required_field_list

        if required_lines:
            msg_analysis = _(
                "Unable to post! The following analysis codes are mandatory:"
            )
            msg_analysis += '\n'
            msg_analysis += yaml.safe_dump(required_lines)
            raise osv.except_osv(_('Error!'), msg_analysis)

        if clear_lines:
            aml_obj = self.pool['account.move.line']
            for ordering, lines in clear_lines.iteritems():
                if lines:
                    vals = {'a{0}_id'.format(ordering): False}
                    aml_obj.write(cr, uid, lines, vals, context=context)

    def post(self, cr, uid, ids, context=None):
        """override the post method so all lines can be check against analysis
        controls
        """
        self._analysis_control(cr, uid, ids, context=context)

        return super(account_move, self).post(cr, uid, ids, context=context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """We display analysis codes on the account.move form inserting them
        in the one2many field containing account move lines
        """
        if context is None:
            context = {}
        res = super(account_move,
                    self).fields_view_get(cr, uid, view_id=view_id,
                                          view_type=view_type,
                                          context=context,
                                          toolbar=toolbar,
                                          submenu=False)

        ans_obj = self.pool['analytic.structure']
        line_id_field = res['fields'].get('line_id')
        ans_obj.analytic_fields_subview_get(
            cr, uid, 'account_move_line', line_id_field, context=context
        )

        return res

    def _check_duplicate_ref_on_account_move_same_account(
        self, cr, uid, ids, context=None
    ):
        """ Check that if the company does not allow duplicate ref/account.
        That it is not 
        """
        am_brl = self.browse(cr, uid, ids, context)
        for am_br in am_brl:
            if (
                not am_br.company_id.
                    allow_duplicate_ref_on_account_move_same_account
            ):
                # check that there is no other line with same
                # partner but different ref on the move
                # Use SUPERUSER_ID to be sure to find all
                am_same_ref_ids = self.search(
                    cr, SUPERUSER_ID,
                    [('ref', '=', am_br.ref), ('id', '!=', am_br.id)],
                    context=context)
                if am_same_ref_ids:
                    _logger.debug("Found ref %s in other account move"
                        % am_br.ref)
                    # make a set of the values for easy comparison
                    partners = {line.partner_id.id for line in am_br.line_id}
                    _logger.debug(partners)
                    am_same_ref_brl = self.browse(
                        cr, SUPERUSER_ID, am_same_ref_ids, context)
                    # check that partner is not the same if ref are
                    for am_same_ref_br in am_same_ref_brl:
                        for aml_br in am_same_ref_br.line_id:
                            if aml_br.partner_id.id in partners:
                                _logger.debug(
                                    "Found same partner in move %(move)d line "
                                    "%(line)d" % {
                                        'move': am_br.id, 'line': aml_br.id})
                                return False
                            else:
                                _logger.debug("Found different partner "
                                    "%(partner)s in move %(move)d line "
                                    "%(line)d" % {
                                        'move': am_br.id,
                                        'line': aml_br.id,
                                        'partner':aml_br.partner_id.id})
                else:
                    _logger.debug("Ref %s unique in account move"
                        % am_br.ref)
        return True

    _constraints = [
        (
            _check_duplicate_ref_on_account_move_same_account,
            "Duplicate reference on same partner with that account on this journal",
            ['ref']
        ),
    ]

class mail_message(osv.Model):
    _inherit = 'mail.message'

    def message_read(
        self, cr, uid, ids=None, domain=None, message_unload_ids=None,
        thread_level=0, context=None, parent_id=False, limit=None
    ):
        """Override this function to include account.move.line notifications
        within account.move notification lists.

        :todo This applies to every mail.message object; maybe find a better
        solution that doesn't involve modifying objects globally.
        """

        # Example domain: [['model', '=', 'account.move'], ['res_id', '=', 7]]

        # Avoid recursion...
        if domain and ['model', '=', 'account.move.line'] not in domain:

            am_obj = self.pool['account.move']

            line_domain = []

            # Look for a "res_id = X" domain part.
            for domain_index, domain_part in enumerate(domain):
                if (domain_index < len(domain) - 1 and
                    domain_part == ['model', '=', 'account.move']
                ):
                    next_part = domain[domain_index + 1]
                    if next_part[0] == 'res_id' and next_part[1] == '=':

                        move_id = next_part[2]
                        line_ids = am_obj.read(
                            cr, uid,
                            move_id,
                            ['line_id'],
                            context=context
                        )['line_id']

                        line_domain = [
                            ('model', '=', 'account.move.line'),
                            ('res_id', 'in', line_ids)
                        ]

            if line_domain:
                domain = expression.OR([
                    expression.normalize_domain(line_domain),
                    expression.normalize_domain(domain)
                ])

                # Make sure our domain is applied. When "ids" is set, the
                # domain is ignored.
                ids = None

        return super(mail_message, self).message_read(
            cr, uid, ids=ids, domain=domain,
            message_unload_ids=message_unload_ids, thread_level=thread_level,
            context=context, parent_id=parent_id, limit=limit
        )
