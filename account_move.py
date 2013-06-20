from openerp.osv import osv
from openerp.tools.translate import _


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

