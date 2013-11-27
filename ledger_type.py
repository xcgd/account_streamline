from openerp.osv import fields, osv


class ledger_type(osv.Model):
    """Define a type of accounting ledger; utility class to be used by other
    modules.
    """

    _name = 'account_streamline.ledger_type'

    _columns = {
        'name': fields.char(
            'Name',
            size=256,
            required=True
        ),
    }

    _order = 'name'

    _sql_constraint = [
        ('name', "UNIQUE('name')", 'Name has to be unique!'),
    ]
