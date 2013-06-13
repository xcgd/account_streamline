from openerp.osv import osv
from lxml import etree


class account_move(osv.osv):
    _name = "account.move"
    _inherit = "account.move"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(account_move,
                    self).fields_view_get(cr, uid, view_id=view_id,
                                          view_type=view_type,
                                          context=context,
                                          toolbar=toolbar,
                                          submenu=False)
        ans_obj = self.pool.get('analytic.structure')

        # display analysis codes only when present on a
        # related structure, with dimension name as label
        ans_ids = ans_obj.search(cr, uid,
                                 [('model_name', '=', 'account_move_line')],
                                 context=context)
        ans_br = ans_obj.browse(cr, uid, ans_ids, context=context)
        ans_dict = dict()
        for ans in ans_br:
            ans_dict[ans.ordering] = ans.nd_id.name
        doc = etree.XML(res['arch'])
        if 'fields' in res and 'line_id' in res['fields']:
            line_fields = res['fields']['line_id']['views']['tree']['fields']
            if 'a1_id' in line_fields:
                line_fields['a1_id']['string'] = ans_dict.get('1', 'A1')
            if 'a2_id' in line_fields:
                line_fields['a2_id']['string'] = ans_dict.get('2', 'A2')
            if 'a3_id' in line_fields:
                line_fields['a3_id']['string'] = ans_dict.get('3', 'A3')
            if 'a4_id' in line_fields:
                line_fields['a4_id']['string'] = ans_dict.get('4', 'A4')
            if 'a5_id' in line_fields:
                line_fields['a5_id']['string'] = ans_dict.get('5', 'A5')
        res['arch'] = etree.tostring(doc)
        return res
