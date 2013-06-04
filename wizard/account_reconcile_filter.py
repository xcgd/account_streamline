from openerp.osv import fields, osv

class account_reconcile_filter(osv.TransientModel):
    _name = 'account.numergy.reconcile_filter'

    _columns = {
        'id_from'           : fields.char('From', size=256),
        'id_to'             : fields.char('To', size=256),
        'field_filter'      : fields.many2one('ir.model.fields',
                                              'Search Field'),
        'dateField_from'    : fields.date('Date From'),
        'dateField_to'      : fields.date('Date To'),
    }

    def launch_search(self, cr, uid, ids, context=None):
        filter_ids = self.browse(cr, uid, ids, context=context)
        args = dict()
        args['obj_type'] = 'account.move.line'
        args['field_filter'] = filter_ids[0].field_filter.id
        args['id_filter_from'] = filter_ids[0].id_from
        args['id_filter_to'] = filter_ids[0].id_to
        adv_filter_osv = self.pool.get("account.numergy.advanced_filter")
        if adv_filter_osv:
            adv_filter_osv.create_new_filter(cr, uid,
                                             ids, args=args,
                                             context=context)
        return {'type': 'ir.actions.act_window_close'}

    def fields_view_get(self, cr, uid, view_id=None,
                        view_type='form', context=None,
                        toolbar=False):
        result = super(account_reconcile_filter,
                       self).fields_view_get(cr, uid, view_id, view_type,
                                             context=context, toolbar=toolbar)
        return result


