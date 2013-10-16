<style type="text/css">
${css}
</style>

%for object in objects[0].voucher_ids:
<% setLang(object.partner_id.lang) %>

<div class="payment_suggestion_header_sep">&nbsp;</div>

<!-- Using h2 as the font-size property doesn't seem to affect divs... -->
<h2 class="payment_suggestion_voucher_name">${ object.name }</h2>

<table class="list_table">
    <thead>
        <tr>
            <th>${ _('Transaction reference') }</th>
            <th>${ _('Invoice date') }</th>
            <th>${ _('Debit/Credit') }</th>
            <th>${ _('Currency') }</th>
            <th class="amount">${ _('Amount') }</th>
        </tr>
    </thead>
    <tbody>
        %for line in object.line_dr_ids:
        <tr class="line">
            <td>${ line.name }</td>
            <td>${ line.date_original }</td>
            <td>${ debit_credit(line) }</td>
            <td>${ line.currency_id.name }</td>
            <td class="amount">${ format_amount(line.amount, object) }</td>
        </tr>
        %endfor
    </tbody>
</table>

<h2 class="payment_suggestion_total">${ _('Total:') } ${ format_amount(object.amount, object) }</h2>

${ object.remittance_letter_bottom }

%endfor
