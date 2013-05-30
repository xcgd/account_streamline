from openerp.osv import fields, osv

class account_reconcile_filter(osv.TransientModel):
    _name = 'account.streamline.reconcile_filter'
    _columns = {
        'obj_list' : fields.integer('Un entier'),
        'id_from' : fields.many2one('account.move.line', 'From'),
        'id_to' : fields.many2one('account.move.line', 'To'),
    }
    def launch_search(self, cr, uid, ids, context=None):
        filter_ids = self.browse(cr, uid, ids, context=context)
        args = dict()

        for filter_id in filter_ids:
            args['obj_type'] = 'account.move.line'
            args['field_filter'] = filter_id.obj_list
            args['id_filter_from'] = filter_id.id_from.id
            args['id_filter_to'] = filter_id.id_to.id
            self.pool.get("account.streamline.advanced.filter").create_new_filter(cr, uid, ids, args=args, context=context)

    def search_partners_to_reconcile(self, cr, uid, ids, args, context=None):
        print args
        return args

