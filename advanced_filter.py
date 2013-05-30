from openerp.osv import osv, fields

class advanced_filter(osv.Model):
    _name = "account.streamline.advanced_filter"
    _columns = {
        'id_user'           : fields.integer("id_user"),
        'obj_type'          : fields.char("obj_type", size=256),
        'field_filter'      : fields.char("field_filter", size=256),
        'id_filter_from'    : fields.integer("id_filter_from"),
        'id_filter_to'      : fields.integer("id_filter_to"),
        'is_active'         : fields.boolean("is_active"),
    }

    def create_new_filter(self, cr, uid, ids, args=None, context=None):
        if args is None: return
        self.create(cr, uid, {'id_user' : uid,
                              'obj_type' : args['obj_type'],
                              'field_filter' : args['field_filter'],
                              'id_filter_from' : args['id_filter_from'],
                              'id_filter_to' : args['id_filter_to'],
                              'is_active' : self._set_as_active(cr, uid, ids, context=context)},
                              context=context)

    def _set_as_active(self, cr, uid, ids, context=None):
        filter_id = self.search(cr, uid, [('is_active', '=', True)], context=context)
        if filter_id:
            self.write(cr, uid, filter_id, {'is_active': False}, context=context)
        return True

    def get_elements_filtered(self, cr, uid, context=None):
        filter_id = self.search(cr, uid, [('is_active', '=', True)], context=context)
        if not filter_id:
            return {}
        active_filter = self.browse(cr, uid, filter_id, context=context)
        if not active_filter:
            return {}
        obj_osv = self.pool.get(active_filter[0].obj_type)
        if not obj_osv:
            return {}
        print "*" * 35
        print "From : "
        print active_filter[0].id_filter_from
        print "To : "
        print active_filter[0].id_filter_to
        print "*" * 35
        obj_ids = obj_osv.search(cr, uid,
                                 [(active_filter[0].field_filter, '>=',
                                   active_filter[0].id_filter_from),
                                  (active_filter[0].field_filter, '<=',
                                   active_filter[0].id_filter_to)],
                                 order=active_filter[0].field_filter,
                                 context=context)
       # temp = obj_osv.name_get(cr, uid, obj_ids, context=context)
        print "*" * 35
        print obj_ids
        print "*" * 35
        return obj_ids
            

