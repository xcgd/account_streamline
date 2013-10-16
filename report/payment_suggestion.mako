<style type="text/css">
${css}

.line td {
    text-align: center;
}

.payment_suggestion_header_sep {
    clear: both;
    margin-top: 50px;
}

.payment_suggestion_partner {
	clear: both;
    margin-top: 40px;
    margin-bottom: 40px;
}

.payment_suggestion_total {
    margin-top: 30px;
    padding: 10px 10px 10px 10px;
    border: 1px #000000 solid;
    text-align: right;
}

</style>

%for object in objects:
<% setLang(object.voucher_ids[0].partner_id.lang) %>

<div class="payment_suggestion_header_sep">&nbsp;</div>

<% partners = get_partners(object) %>
%for partner, partner_details in partners.iteritems():
<%
	vouchers = partner_details['vouchers']
	partner_total = partner_details['total']
%>

<!-- Using h2 as the font-size property doesn't seem to affect divs... -->
<h2 class="payment_suggestion_partner">${ partner.name }</h2>

<table class="list_table">
    <thead>
        <tr>
            <th>${ _('Transaction reference') }</th>
            <th>${ _('Description') }</th>
            <th>${ _('Invoice date') }</th>
            <th>${ _('Debit/Credit') }</th>
            <th>${ _('Currency') }</th>
            <th class="amount">${ _('Amount') }</th>
        </tr>
    </thead>
    <tbody>
    	%for voucher in vouchers:
        %for line in voucher.line_dr_ids:
        <tr class="line">
            <td>${ line.name }</td>
            <td>${ line.move_line_id.ref }</td>
            <td>${ line.date_original }</td>
            <td>${ debit_credit(line) }</td>
            <td>${ line.currency_id.name }</td>
            <td class="amount">${ format_amount(line.amount, voucher) }</td>
        </tr>
        %endfor
        %endfor
    </tbody>
</table>

<h2 class="payment_suggestion_total">${ _('Total for %s:') % partner.name } ${ format_amount(partner_total, vouchers[0]) }</h2>

%endfor

%endfor
