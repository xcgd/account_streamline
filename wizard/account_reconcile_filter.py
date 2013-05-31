from openerp.osv import fields, osv

class account_reconcile_filter(osv.TransientModel):
    _name = 'account.streamline.reconcile_filter'
    _columns = {
        'id_from'       : fields.many2one('account.account', 'From'),
        'id_to'         : fields.many2one('account.account', 'To'),
	'filter_type'   : fields.many2one('account.streamline.filter', 'Search by'),
        'search_type'   : fields.char('search by', name="Search", method=True),
	'account_from' : fields.many2one('account.account', 'Account From'),
        'account_to' : fields.many2one('account.account', 'Account To'),
        'journal_from' : fields.many2one('account.journal', 'Journal From'),
        'journal_to' : fields.many2one('account.journal', 'Journal To'),
        'dateField_from' : fields.date('Date From'),
        'dateField_to' : fields.date('Date To'),

    }

    def launch_search(self, cr, uid, ids, context=None):
        filter_ids = self.browse(cr, uid, ids, context=context)
        args = dict()

        for filter_id in filter_ids:
            args['obj_type'] = 'account.move.line'
            args['field_filter'] = filter_id.search_type
            args['id_filter_from'] = filter_id.id_from.id
            args['id_filter_to'] = filter_id.id_to.id
            adv_filter_osv = self.pool.get("account.streamline.advanced_filter")
            if adv_filter_osv:
                adv_filter_osv.create_new_filter(cr, uid,
                                                 ids, args=args,
                                                 context=context)
        return {'type': 'ir.actions.act_window_close'}

    def onchange_filter(self, cr, uid, ids, value):
	if value:
	    filter_curr = self.pool.get('account.streamline.filter').browse(cr, uid, value)
	    return {'value': {'search_type': filter_curr.move_line_column_name}}
	return {'value':{'search_type': "empty"}}


class account_filter(osv.TransientModel):
    _name = 'account.streamline.filter'
    _columns = {
        'name' : fields.char('Filtre', size=250),
	'move_line_column_name' : fields.char('Move Line Column Name'),

     }

