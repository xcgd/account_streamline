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
            domain=[('report_name', '=', 'RemittanceLetter.pdf')],
            required=True),

        'partners': fields.many2many(
            'res.partner',
            'email_remittance_partner_rel',
            'email_remittance_id',
            'partner_id',
            _('Partners'),
            required=True,
            readonly=True),

        'vouchers': fields.many2many(
            'account.voucher',
            'email_remittance_voucher_rel',
            'email_remittance_id',
            'voucher_id',
            _('Vouchers'),
            required=True,
            readonly=True),
    }

    def default_get(self, cr, uid, fields_list=None, context=None):
        ''' - Ensure posted vouchers have been selected.
        - Gather partners from selected vouchers.
        - Select a default email template. '''

        if 'active_ids' not in context:
            return {}

        voucher_obj = self.pool.get('account.voucher')
        vouchers = voucher_obj.browse(cr, uid, context['active_ids'],
                                      context=context)

        voucher_ids = []
        partner_ids = []

        for voucher in vouchers:
            if voucher.state == 'posted':
                voucher_ids.append(voucher.id)

                if voucher.partner_id.id not in partner_ids:
                    partner_ids.append(voucher.partner_id.id)

        if not voucher_ids:
            return {}

        # Grab the default email template.
        email_template_obj = self.pool.get('email.template')
        default_email_template = email_template_obj.search(cr, uid,
            [('report_name', '=', 'RemittanceLetter.pdf')],
            context=context)

        return {
            'email_template': default_email_template,
            'partners': [(6, 0, partner_ids)],
            'vouchers': [(6, 0, voucher_ids)],
        }

    def send_emails(self, cr, uid, ids, context=None):
        ''' Send one email for each selected voucher; the email template
        should generate attachments automagically. '''

        this = self.browse(cr, uid, ids)[0]

        # Send 1 email per voucher. force_send=True to send instantly rather
        # than scheduling for later delivery.
        email_template_obj = self.pool.get('email.template')
        for voucher in this.vouchers:
            email_template_obj.send_mail(cr, uid, this.email_template.id,
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
