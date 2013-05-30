from openerp.osv import osv, fields

class advanced_filter(osv.Model):
    _name = "account.streamline.advanced.filter"
    _columns = {
        'id_user' : fields.integer("id_user"),
        'obj_type' : fields.char("obj_type", size=256),
        'field_filter' : fields.char("field_filter", size=256),
        'id_filter_from' : fields.integer("id_filter_from"),
        'id_filter_to' : fields.integer("id_filter_to"),
        'is_active' : fields.boolean("is_active"),
    }

    def create_new_filter(self, cr, uid, ids, args=None, context=None):
        if args is None: return
        self.create(cr, uid, {'id_user' : uid,
                              'obj_type' : args['obj_type'],
                              'field_filter' : args['field_filter'],
                              'id_filter_from' : args['id_filter_from'],
                              'id_filter_to' : args['id_filter_to'],
                              'is_active' : True} , context=context)


