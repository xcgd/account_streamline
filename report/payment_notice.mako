<style type="text/css">
${css}

.line td {
    text-align: center;
}

.payment_notice_header_sep {
    clear: both;
    margin-top: 50px;
}

.payment_notice_message {
}

.payment_notice_total {
    margin-top: 30px;
    text-align: right;
}

</style>

<div class="payment_notice_header_sep">&nbsp;</div>

%for object in objects:

<div class="payment_notice_message">${ message(object) }</div>

<table class="list_table">
    <thead>
        <tr>
            <th>${ _('Transaction reference') }</th>
            <th>${ _('Invoice date') }</th>
            <th>${ _('Amount') }</th>
            <th>${ _('Debit/Credit') }</th>
            <th>${ _('Currency') }</th>
            <th>${ _('Untax Amount') }</th>
        </tr>
    </thead>
    <tbody>
        %for line in object.line_dr_ids:
        <tr class="line">
            <td>${ line.name }</td>
            <td>${ line.date_original }</td>
            <td>${ format_amount(line.amount, object) }</td>
            <td>${ debit_credit(line) }</td>
            <td>${ line.currency_id.name }</td>
            <td>${ format_amount(line.untax_amount, object) }</td>
        </tr>
        %endfor
    </tbody>
</table>

<!-- Using h2 as the font-size property doesn't seem to affect divs... -->
<h2 class="payment_notice_total">${ _('Total:') } ${ format_amount(object.amount, object) }</h2>

%endfor
