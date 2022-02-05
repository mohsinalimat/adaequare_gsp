// Copyright (c) 2022, Resilient Tech and contributors
// For license information, please see license.txt
frappe.provide("adaequare_gsp")

frappe.ui.form.on('Purchase Reconciliation Tool', {
	refresh: function (frm) {
		adaequare_gsp.get_date_range(frm, frm.doc.purchase_period, "purchase_from_date", "purchase_to_date")
		adaequare_gsp.get_date_range(frm, frm.doc.inward_supply_period, "inward_supply_from_date", "inward_supply_to_date")

	},
	purchase_period: function (frm) {
		adaequare_gsp.get_date_range(frm, frm.doc.purchase_period, "purchase_from_date", "purchase_to_date")
	 },
	inward_supply_period: function (frm) {
		adaequare_gsp.get_date_range(frm, frm.doc.inward_supply_period, "inward_supply_from_date", "inward_supply_to_date")
	}
});

adaequare_gsp.get_date_range = function (frm, period, from_date, to_date) {
	if (period == "Custom") return;
	frappe.call({
		method: "adaequare_gsp.api.reco_tool.get_date_range",
		args: {
			"period": period,
		},
		callback: function (r) {
			frm.set_value(from_date, r.message[0])
			frm.set_value(to_date, r.message[1])
		}
	})
}