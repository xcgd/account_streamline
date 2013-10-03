<style type="text/css">
${css}

thead {
    text-align: left;
}

.payment_notice_header_sep {
    clear: both;
    margin-top: 50px;
}

.payment_notice_message {
}

.payment_notice_total {
    margin-top: 30px;
    font-weight: bold;
    font-size 50em;
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
            <td>${ line.type }</td>
            <td>${ line.currency_id.name }</td>
            <td>${ format_amount(line.untax_amount, object) }</td>
        </tr>
        %endfor
    </tbody>
</table>

<div class="payment_notice_total">${ format_amount(object.amount, object) }</div>

%endfor
