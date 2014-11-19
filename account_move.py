from openerp.osv import fields, expression, osv
from openerp.tools.translate import _
import yaml
from lxml import etree

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
