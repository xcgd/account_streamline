from openerp.osv import fields, osv

class account_reconcile_filter(osv.TransientModel):
    _name = 'account.streamline.reconcile_filter'
    _columns = {
        'obj_list' : fields.integer('Un entier'),
        'id_from' : fields.integer('From'),
        'id_to' : fields.integer('To'),
	'filter_type' : fields.many2one('account.streamline.filter', 'Search by'),
        'search_type' : fields.char('search by', name="Search", method=True),
        'account_from' : fields.char('account_from'),
        'account_to' : fields.date('account_to'),

    }
    def launch_search(self, cr, uid, ids, context=None):
        filter_ids = self.browse(cr, uid, ids, context=context)
        args = dict()
        print self

        for filter_id in filter_ids:
            args['obj_type'] = self._name
            args['field_filter'] = filter_id.obj_list
            args['id_filter_from'] = filter_id.id_from
            args['id_filter_to'] = filter_id.id_to
            self.pool.get("account.streamline.advanced.filter").create_new_filter(cr, uid, ids, args=args, context=context)

    def search_partners_to_reconcile(self, cr, uid, ids, args, context=None):
        print args
        res = {}
        return res

class account_filter(osv.TransientModel):
    _name = 'account.streamline.filter'
    _columns = {
	'name' : fields.char('Filtre', size=250),
     }

