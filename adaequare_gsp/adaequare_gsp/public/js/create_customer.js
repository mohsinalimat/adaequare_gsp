
frappe.provide("smc_erp")

smc_erp.verify_gstin = function(dia){
	console.log(dia)
	var d = new frappe.ui.Dialog({
		title: __('Verify GSTIN'),
		fields: [
			{
				"label" : "GSTIN",
				"fieldname": "gstin",
				"fieldtype": "Data",
				"reqd": 1,
				"default": dia.doc.gstin
			},
			{
				"label" : "Full Name",
				"fieldname": "customer_name",
				"fieldtype": "Data"
			}

		],
		primary_action: function() {
			var data = d.get_values();
			d.hide();
			dia.doc.customer_name = data.customer_name;
			dia.dialog.refresh()
		},
		primary_action_label: __('Apply')
	});
	d.show();
}

modifyMethod('frappe.ui.form.CustomerQuickEntryForm', 'get_variant_fields', function(old){
	let variant_fields = old;
	for (let i of variant_fields){
		if(i.collapsible == 1){i.collapsible = 0};
		if(i.fieldname == 'state'){i.default = 'Maharashtra'};
		if(i.fieldname != 'country') {continue;}
		i.hidden = 1;
		i.default = 'India';
		break;
	}

	variant_fields.push(
		{
			label: __("Locality"),
			fieldname: "locality",
			fieldtype: "Select"
		},
		{
			label: __("Trial"),
			fieldname: "trial",
			fieldtype: "Button",
			click: () => {
				smc_erp.verify_gstin(this);
			}
		}
	)
	return variant_fields;
})
