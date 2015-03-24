<style type="text/css">
${css}
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
    font-size: 12px;
}

.line td {
    text-align: center;
    font-size: 12px;
}

.pre_line th {
    font-size: 12px;;
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
    padding-right: 3px;
    padding-left: 3px;
    border-bottom: 1px solid lightGrey;
}

.list_table td.amount,
.list_table th.amount {
    text-align: center;
}


.avoid_page_break {
	page-break-inside: avoid;
}

.payment_suggestion_bottom {
    margin-top: 30px;
    padding: 10px 10px 10px 10px;
}

.payment_suggestion_total_main  {
	clear: both;
    margin-top: 30px;
    margin-right: 70%;
    padding: 10px 10px 10px 10px;
    border: 1px solid lightGrey;
}

.payment_suggestion_total {
    text-align: right;
}

</style>

%for object in objects:
<% setLang(object.voucher_ids[0].partner_id.lang) %>

<% partners = get_partners(object) %>

<div class="address">
    <div class="addressleft">
        <table class="shipping">
            <tr><th class="addresstitle"></th></tr>
            %if object.voucher_ids:
            <tr><td class="name">${object.voucher_ids[0].company_id.name or ''}</td></tr>
            <tr><td class="name">${object.voucher_ids[0].company_id.street or ''}</td></tr>
            <tr><td class="name">${object.voucher_ids[0].company_id.street2 or ''}</td></tr>
            <tr><td class="name">${object.voucher_ids[0].company_id.zip or ''} ${object.voucher_ids[0].company_id.city or ''}</td></tr>
            %endif
        </table>
    </div>
</div>
&nbsp;&nbsp;
<!-- Using h2 as the font-size property doesn't seem to affect divs...-->
<h2 class="payment_suggestion_total_main">
	${ _('Journal: %s') % object.voucher_ids[0].journal_id.name }<br/>
	<% voucher_count, partner_count, total = get_totals(partners) %>
	${ _('Voucher count: %d') % voucher_count }<br/>
	${ _('Partner count: %d') % partner_count }<br/>
	${ _('Total: %s') % formatLang(total, currency_obj=object.voucher_ids[0].currency_id) }
</h2>

%for partner, partner_details in partners.iteritems():
<%
	vouchers = partner_details['vouchers']
	partner_total = partner_details['total']
%>

<!-- Page breaks have not been ideally fixed (tables that are too high still span multiple pages
without their report row being repeated) but this solution is already quite good; see
<https://bitbucket.org/xcg/account_streamline/issue/38>. -->
<div class="avoid_page_break">


<table class="list_table">
    <thead>
        <tr class="pre_line">
            <th>${ _('Transaction reference') }</th>
            <th>${ _('Description') }</th>
            <th>${ _('Invoice date') }</th>
            <th>${ _('Currency') }</th>
            <th>${ _('Debit/Credit') }</th>
            <th class="amount">${ _('Amount') }</th>
        </tr>
    </thead>
    <tbody>
    	%for voucher in vouchers:
	        %for line in voucher.line_ids:
		        <tr class="line">
		            <td>${ line.name }</td>
		            <td>${ line.move_line_id.ref }</td>
		            <td>${ line.date_original }</td>
		            <td>${ line.currency_id.name }</td>
		            <td>${ debit_credit(line) }</td>
		            <td class="amount">${ formatLang(line.amount, currency_obj=voucher.currency_id) }</td>
		        </tr>
	        %endfor
        %endfor
    </tbody>
</table>
&nbsp;&nbsp;
<h2 class="payment_suggestion_total">
	${ _('Total for %s:') % partner.name }
	${ formatLang(partner_total, currency_obj=vouchers[0].currency_id) }
</h2>

</div>

%endfor

<h2 class="payment_suggestion_bottom">
	${ _('Generated on %s') % date() }
</h2>

<h2 class="payment_suggestion_bottom">
	${ _('Signature:') }
</h2>

%endfor
