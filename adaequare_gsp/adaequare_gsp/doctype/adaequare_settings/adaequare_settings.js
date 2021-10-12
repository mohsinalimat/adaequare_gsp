// Copyright (c) 2021, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adaequare Settings', {
	validate: function(frm) {
		frm.doc.expires_at = date.nowdate() + ' ' + date.now_time() + '.0';
	}
});
