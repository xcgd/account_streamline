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
    border: 1px #000000 solid;
}

.remittance_letter_message {
    clear: both;
    margin-top: 40px;
    margin-bottom: 40px;
}

.remittance_letter_total {
    margin-top: 30px;
    padding: 10px 10px 10px 10px;
    border: 1px #000000 solid;
    text-align: right;
}

.remittance_letter_voucher_name {
	clear: both;
    margin-top: 40px;
    margin-bottom: 40px;
}
body {
    font-family: helvetica;
    font-size: 7px;
}

table {
    border-collapse: collapse;
    margin: 0px;
    padding: 0px;
}

/* header */

.header {
    height: 80px;
    border-bottom: 1px solid grey;
    padding-bottom: 10px;
}

.header .logo,
.header .title {
    float: left;
    width: 33%;
}

.header .logo img {
    padding: 0px 20px;
    height: 80px;
}

.header .title {
    font-size: 14px;
    /* font-weight: bold; */
    padding-top: 68px;
    text-align: center;
    text-transform: uppercase;
    font-weight: bold;
    text-align: center;
}

.header_sep {
    clear: both;
    height: 20px;
}

.pagenum {
    font-size: 8px;
    padding-top: 72px;
    padding-right: 10px;
    text-align: right;
}

.page span.text {
    padding: 10px;
}

/* address */


.address {
    clear: both;
    float: left;
    width: 100%;
}

.address table {
    margin-left: 100px;
    text-align: left;
}

.address table th {
    font-size: 12px;
    padding-bottom: 4px;
}

.address table td {
    font-size: 12px;
}

.addressleft,
.addressright {
    width: 50%;
    margin: 20px 0;
}

.addressleft {
    float: left;
    margin-top: 50px;
}

.addressright {
    float: right;
    margin-top: 50px;
}

.address .shipping{
    margin-top:10px;
    margin-left:40px;
    }

.address .recipient {
    margin-top: 15px;
}

.address td.addresstitle {
    font-weight: bold;
}

/* table */

.basic_table {
    border-collapse: collapse;
    clear: both;
    font-size: 8px;
    margin: auto;
    padding: 20px;
    text-align: center;
}

.basic_table th,
.basic_table td {
    border: 1px solid lightGrey;
    padding: 5px;
}

.list_table {
    border-collapse: collapse;
    margin: auto;
    text-align: center;
    width: 100%;
    margin-top: 30px;
}

.list_table td {
    border-top: 1px solid lightGrey;
    font-size: 9px;
    padding-right: 3px;
    padding-left: 3px;
    padding-top: 3px;
    padding-bottom:3px;
    text-align: left;
}

.list_table th {
    border-bottom: 1px solid black;
    text-align: center;
    font-size: 8px;
    font-weight: bold;
    padding-right: 3px
    padding-left: 3px
}

.list_table thead {
    display: table-header-group;
}

.list_table td.amount,
.list_table th.amount {
    text-align: right;
}

.list_table tr.line {
    margin-bottom: 10px;
}

.list_table th.date {
    text-align: center;
}

.list_table tfoot {
    font-size: 10px;
}

.list_table tfoot th {
    padding-top: 10px;
}

.list_table tfoot td,
.list_table tfoot th {
    border: none;
    text-align: right;
}

.list_table td.signature {
    padding-top: 30px;
    text-align: center;
}

.list_table td.signature title,
.list_table td.signature name {
    font-size: 10px;
}

.list_table td.signature img {
    margin-bottom: 14px;
    margin-top: 14px;
    width: 140px;
}

.note,
.footer {
    margin: 20px auto;
    text-align: center;
}

.note {
    font-size: 9px;
    font-weight: bold;
    text-decoration: underline;
}

.footer {
    border-top: 1px solid grey;
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
            <td>${ line.move_line_id.move_id.ref }</td>
            <td>${ line.date_original }</td>
            <td>${ debit_credit(line) }</td>
            <td>${ line.currency_id.name }</td>
            <td class="amount">${ formatLang(line.amount, currency_obj=object.currency_id) }</td>
        </tr>
        %endfor
    </tbody>
</table>

<h2 class="remittance_letter_total">
	${ _('Total:') }
	${ formatLang(object.amount, currency_obj=object.currency_id) }
</h2>

<!-- Voucher-specific bottom information. -->
${ object.remittance_letter_bottom }

<!-- Company-specific bottom information. -->
<h2 class="remittance_letter_company_bottom">${ bottom_message(object) }</h2>

%endfor

