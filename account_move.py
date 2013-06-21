from openerp.osv import osv
from openerp.tools.translate import _
import yaml


class account_move(osv.Model):
    _name = "account.move"
    _inherit = "account.move"

    def _analysis_control(self, cr, uid, ids, context=None):
        '''
        This controls the account.move.line analysis dimensions settings set on account.account
        It will perform this only when attempting to post a complete move and
        will compile all errors coming from move lines in a single message
        '''
        #move_dict = {}
        lines = []

        ans_obj = self.pool.get('analytic.structure')
        ans_ids = ans_obj.search(cr, uid,
                                 [('model_name', '=', 'account_move_line')],
                                 context=context)
        ans_br = ans_obj.browse(cr, uid, ans_ids, context=context)
        ans_dict = dict()
        for ans in ans_br:
             ans_dict[ans.ordering] = ans.nd_id.name

        for move in self.browse(cr, uid, ids, context=context):
            #line_dict = []
            for aml in move.line_id:

                dim_list = []
                if aml.account_id.t1_ctl == '1' and not aml.a1_id:
                    dim_list.append(ans_dict.get('1', 'A1').encode('utf8'))
                if aml.account_id.t2_ctl == '1' and not aml.a2_id:
                    dim_list.append(ans_dict.get('2', 'A2').encode('utf8'))
                if aml.account_id.t3_ctl == '1' and not aml.a3_id:
                    dim_list.append((ans_dict.get('3', 'A3').encode('utf8')))
                if aml.account_id.t4_ctl == '1' and not aml.a4_id:
                    dim_list.append((ans_dict.get('4', 'A4').encode('utf8')))
                if aml.account_id.t5_ctl == '1' and not aml.a5_id:
                    dim_list.append((ans_dict.get('5', 'A5').encode('utf8')))
                if dim_list:
                    #line_dict[aml.name.encode('utf8')] = dim_list
                    tmp = [aml.name.encode('utf8')]
                    tmp.append(dim_list)
                    print tmp
                    lines += tmp
            #if lines:
                #move_dict[move.ref.encode('utf8')] = line_dict

        if lines:
            msg_analysis = _("Unable to post! The following analysis codes are mandatory:")
            msg_analysis += '\n'
            msg_analysis += yaml.dump(lines)
            raise osv.except_osv(_('Error!'), msg_analysis)

    def post(self, cr, uid, ids, context=None):
        '''
        override the post method so all lines can be check against analysis controls
        '''
        self._analysis_control(cr, uid, ids, context=context)

        return super(account_move, self).post(cr, uid, ids, context=context)

