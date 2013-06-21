from openerp.osv import osv
from openerp.tools.translate import _
from lxml import etree


class account_move(osv.Model):
    _name = "account.move"
    _inherit = "account.move"

    def _analysis_control(self, cr, uid, ids, context=None):
        '''
        This controls the account.move.line analysis dimensions settings set on account.account
        It will perform this only when attempting to post a complete move and
        will compile all errors coming from move lines in a single message
        '''
        move_dict = {}

        ans_obj = self.pool.get('analytic.structure')
        ans_ids = ans_obj.search(cr, uid,
                                 [('model_name', '=', 'account_move_line')],
                                 context=context)
        ans_br = ans_obj.browse(cr, uid, ans_ids, context=context)
        ans_dict = dict()
        for ans in ans_br:
             ans_dict[ans.ordering] = ans.nd_id.name

        for move in self.browse(cr, uid, ids, context=context):
            for aml in move.line_id:
                line_dict = {}
                dim_list = []
                if aml.account_id.t1_ctl == '1' and not aml.a1_id:
                    dim_list.append(ans_dict.get('1', 'A1'))
                if aml.account_id.t2_ctl == '1' and not aml.a2_id:
                    dim_list.append(ans_dict.get('2', 'A2'))
                if aml.account_id.t1_ctl == '1' and not aml.a3_id:
                    dim_list.append((ans_dict.get('3', 'A3')))
                if aml.account_id.t1_ctl == '1' and not aml.a4_id:
                    dim_list.append((ans_dict.get('4', 'A4')))
                if aml.account_id.t1_ctl == '1' and not aml.a5_id:
                    dim_list.append((ans_dict.get('5', 'A5')))
                if dim_list:
                    line_dict[aml.name] = dim_list
            if line_dict:
                move_dict[move.name] = line_dict

        if move_dict:
            msg_analysis = _("Unable to post! The following analysis codes are mandatory:")
            msg_analysis += '\n'
            msg_analysis += repr(move_dict)
            raise osv.except_osv(_('Error!'), msg_analysis)

    def post(self, cr, uid, ids, context=None):
        '''
        override the post method so all lines can be check against analysis controls
        '''
        self._analysis_control(cr, uid, ids, context=context)

        return super(account_move, self).post(cr, uid, ids, context=context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        '''
        We display analysis codes on the account.move form inserting
        them in the one2many field containing account move lines
        '''
        if context is None:
            context = {}
        res = super(account_move,
                    self).fields_view_get(cr, uid, view_id=view_id,
                                          view_type=view_type,
                                          context=context,
                                          toolbar=toolbar,
                                          submenu=False)
        ans_obj = self.pool.get('analytic.structure')

        #display analysis codes only when present on a related structure,
        #with dimension name as label
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

