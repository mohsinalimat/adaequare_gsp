// Copyright (c) 2021, Resilient Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adaequare Settings', {
	validate: function(frm) {
		frm.doc.expires_at = date.nowdate() + ' ' + date.now_time() + '.0';
	},
	update_party_info: function (frm) {
		if(frm.doc.gstn_pubilc_api == 0)return;
		frappe.confirm('Are you sure you want to proceed?',
    () => {
        frappe.call({
			method: 'adaequare_gsp.adaequare_gsp.doctype.adaequare_settings.adaequare_settings.enqueue_bulk_update_party',
			args: {
				make_urp: frm.doc.mark_unregistered
			}
		})	
    }, () => {
        // action to perform if No is selected
    })
	}
});
