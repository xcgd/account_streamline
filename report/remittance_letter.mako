<style type="text/css">
${css}

.line td {
    text-align: center;
}

.remittance_letter_bottom, .remittance_letter_company_bottom {
	margin-top: 30px;
}

.remittance_letter_bottom {
    padding: 10px 10px 10px 10px;
}

.remittance_letter_message {
    clear: both;
    margin-top: 80px;
    margin-bottom: 60px;
}

.remittance_letter_total {
    margin-top: 30px;
    padding: 10px 10px 10px 10px;
    text-align: right;
}

.remittance_letter_voucher_name {
	clear: both;
    margin-top: 40px;
    margin-bottom: 40px;
}

/* Header is define in data/voucher_report_header */

/* Overide address here to redefine specially address stylesheet */

.addressleft,
.addressright {
    width: 50%;
    margin: 10px 0;
    font-size: 16px;
}

.addressleft {
    float: left;
    margin-top: 30px;
}

.addressright {
    float: right;
    margin-top: 30px;
}

.address .shipping{
    margin-top:10px;
    margin-left:0px;
    font-size: 12px;
    font-weight: bold;
    }

.address .recipient {
    margin-top: 15px;
    font-size: 12px;
    font-weight: bold;
}

.address td.addresstitle {
    font-weight: bold;
}

/* table */

.basic_table {
    font-size: 12px;
    width:100%;
}

.basic_table th,
.basic_table td {
    border: 1px solid lightGrey;
    text-align:center;
}

.list_table {
    font-size:12px;
    border: 1px solid lightGrey;
    text-align: center;
    width: 100%;
    margin-top: 30px;
}

.list_table td {
    border-top: 1px solid lightGrey;
    border: 1px solid lightGrey;
    font-size: 12px;
    padding-right: 3px;
    padding-left: 3px;
    padding-top: 3px;
    padding-bottom:3px;
    text-align: center;
    border-bottom: 1px solid lightGrey;
}

.list_table th {
    border: 1px solid lightGrey;
    text-align: center;
    font-size: 12px;
    font-weight: bold;
    padding-right: 3px
    padding-left: 3px
    border-bottom: 1px solid lightGrey;
}

.list_table thead {
    display: table-header-group;
    text-align: center;
}

.list_table td.amount,
.list_table th.amount {
    text-align: center;
}

.list_table tr.line {
    margin-bottom: 10px;
    text-align:center;
}

.list_table th.date {
    text-align: center;
}

.list_table tfoot {
    font-size: 12px;
}
.totals td{
    font-size:12px;
    width:80%;
    padding-right: 5px;
    padding-left: 5px;
}
.list_table tfoot th {
    padding-top: 10px;
}

.list_table tfoot td,
.list_table tfoot th {
    text-align: right;
}

</style>

%for object in objects:
<% setLang(object.partner_id.lang) %>

<div class="address">
    <div class="addressright">
        <table class="recipient">
            %if object.partner_id:
            <tr><td class="name">${object.partner_id.parent_id.name or ''}</td></tr>
            <tr><td class="name">${object.partner_id.title and object.partner_id.title.name or ''} ${object.partner_id.name }</td></tr>
            <tr><td> ${object.partner_id.street or ''} </td></tr>
            <tr><td> ${object.partner_id.street2 or ''} </td></tr>
            <tr><td> ${object.partner_id.zip or ''} ${object.partner_id.city or ''}</td></tr>
            %endif
        </table>
    </div>

    <div class="addressleft">
        <table class="shipping">
            <tr><th class="addresstitle"></th></tr>
            %if object.company_id.partner_id.parent_id:
            <tr><td class="name">${object.company_id.partner_id.parent_id.name or ''}</td></tr>
            <% address_lines = object.company_id.partner_id.contact_address.split("\n")[1:] %>
            %else:
            <% address_lines = object.company_id.partner_id.contact_address.split("\n") %>
            %endif
            <tr><td class="name">${object.company_id.partner_id.title and object.company_id.partner_id.title.name or ''} ${object.company_id.partner_id.name }</td></tr>
            %for part in address_lines:
                %if part:
                <tr><td>${ part }</td></tr>
                %endif
            %endfor
       </table>
    </div>
</div>

<!-- Using h2 as the font-size property doesn't seem to affect divs... -->
<h2 class="remittance_letter_voucher_name">${ object.name or ''}</h2>

<h2 class="remittance_letter_message">${ top_message(object) }</h2>

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
        %for line in object.line_ids:
        <tr class="line">
            <td>${ line.move_line_id.move_id.name}  / ( ${ line.move_line_id.move_id.ref } )</td>
            <td>${ line.date_original }</td>
            <td>${ debit_credit(line) }</td>
            <td>${ line.currency_id.name }</td>
            <td class="amount">${ formatLang(line.amount, currency_obj=object.currency_id) }</td>
        </tr>
        %endfor
    </tbody>
    <tfoot class="totals">
        <tr>
            <td colspan="3"/>
            <td><b>${_(u"Total TTC")} :</b></td>
            <td class="amount" style="white-space:nowrap">${ formatLang(object.amount, currency_obj=object.currency_id) }</td>
        </tr>
    </tfoot>
    </table>
    </br></br>
    <br/><br/>


<!-- Voucher-specific bottom information. -->
${ object.remittance_letter_bottom }

<!-- Company-specific bottom information. -->
<h2 class="remittance_letter_company_bottom">${ bottom_message(object) }</h2>

%endfor

