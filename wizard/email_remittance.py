# This wizard is shown for posted vouchers; it displays selected partners as
# well as an email template used to send Remittance Letter emails.

from openerp.osv import fields, orm
from openerp.tools.translate import _


class email_remittance(orm.TransientModel):
    _name = 'email.remittance'

    _columns = {
        'email_template': fields.many2one(
            'email.template',
            string=_('Email template'),
            domain=[('id', '=', 'remittance_letter_email_template')]),
        'partners': fields.many2many(
            'res.partner',
            'email_remittance_rel',
            'email_remittance_id',
            'partner_id',
            _('Partners')),
    }

    def default_get(self, cr, uid, fields_list=None, context=None):
        ''' Gather partners from selected vouchers. '''

        if not 'active_ids' in context:
            return {}

        partners = []

        voucher_obj = self.pool.get('account.voucher')
        vouchers = voucher_obj.browse(cr, uid, context['active_ids'],
                                      context=context)

        for voucher in vouchers:
            if voucher.partner_id.id not in partners:
                partners.append(voucher.partner_id.id)

        return {
            'partners': [(6, 0, partners)],
        }

    def send_emails(self, cr, uid, ids, context=None):
        ''' Send one email for each selected voucher; the email template
        should generate attachments automagically. '''

        this = self.browse(cr, uid, ids)[0]

        # Grab the email template.
        email_template_obj = self.pool.get('email.template')
        template_ids = email_template_obj.search(cr, uid,
            [('report_name', '=', 'RemittanceLetter.pdf')], context=context)
        if not template_ids:
            raise osv.except_osv(_('Error'), _('No email template found '
                'which generates RemittanceLetter reports'))

        # Get the correct list of ids...
        if 'active_ids' in context:
            ids = context['active_ids']

        # Send 1 email per voucher. force_send=True to send instantly rather
        # than scheduling for later delivery.
        vouchers = self.browse(cr, uid, ids, context=context)
        for voucher in vouchers:
            if voucher.state != 'posted':
                continue
            email_template_obj.send_mail(cr, uid, template_ids[0],
                voucher.id, force_send=True, context=context)

        view_obj = self.pool.get('ir.ui.view')
        view_id = view_obj.search(cr, uid,
            [('name', '=', 'email.remittance.done')])

        return {
            'res_id': this.id,
            'res_model': 'email.remittance',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'view_type': 'form',
        }
