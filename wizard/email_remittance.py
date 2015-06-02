# This wizard is shown for posted vouchers; it displays selected partners as
# well as an email template used to send Remittance Letter emails.

from openerp.osv import fields, orm
from openerp.tools.translate import _


email_template_domain = [('report_template.report_name',
                          '=',
                          'account_streamline.remittance_letter')]


class email_remittance(orm.TransientModel):
    _name = 'email.remittance'

    _columns = {
        'email_template': fields.many2one(
            'email.template',
            string="Email template",
            domain=email_template_domain,
            required=True),

        'partners': fields.many2many(
            'res.partner',
            'email_remittance_partner_rel',
            'email_remittance_id',
            'partner_id',
            "Partners",
            required=True,
            readonly=True),

        'vouchers': fields.many2many(
            'account.voucher',
            'email_remittance_voucher_rel',
            'email_remittance_id',
            'voucher_id',
            "Vouchers",
            required=True,
            readonly=True),
    }

    def default_get(self, cr, uid, fields_list=None, context=None):
        ''' - Ensure posted vouchers have been selected.
        - Gather partners from selected vouchers.
        - Select a default email template. '''

        if 'active_ids' not in context:
            return {}

        voucher_obj = self.pool['account.voucher']
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
        email_template_obj = self.pool['email.template']
        email_template = email_template_obj.search(
            cr, uid,
            email_template_domain, context=context)

        if not email_template:
            return {}

        return {
            'email_template': email_template[0],
            'partners': [(6, 0, partner_ids)],
            'vouchers': [(6, 0, voucher_ids)],
        }

    def send_emails(self, cr, uid, ids, context=None):
        ''' Send one email for each selected voucher; the email template
        should generate attachments automagically. '''

        this = self.browse(cr, uid, ids)[0]

        # Send 1 email per voucher. force_send=True to send instantly rather
        # than scheduling for later delivery.
        email_template_obj = self.pool['email.template']
        for voucher in this.vouchers:
            # Only send mail to partner that have a mail address
            if voucher.partner_id.email:
                email_template_obj.send_mail(
                    cr, uid,
                    this.email_template.id, voucher.id, force_send=True,
                    context=context)

        return True
