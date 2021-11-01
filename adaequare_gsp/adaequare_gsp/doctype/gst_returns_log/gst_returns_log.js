// Copyright (c) 2021, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('GST Returns Log', {
	setup(frm) {
		frm.set_query("party_type", function () {
			return {
				filters: {
					name: ['in', ['Supplier', 'Customer']]
				},
			};
		});
	},
	refresh(frm) {
		frm.disable_form();
	}
});
