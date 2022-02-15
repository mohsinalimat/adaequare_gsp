// Copyright (c) 2022, Resilient Tech and contributors
// For license information, please see license.txt
frappe.provide("adaequare_gsp");
frappe.provide("reco_tool");

frappe.ui.form.on("Purchase Reconciliation Tool", {
    refresh: function (frm) {
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.purchase_period,
            "purchase_from_date",
            "purchase_to_date"
        );
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.inward_supply_period,
            "inward_supply_from_date",
            "inward_supply_to_date"
        );
        frm.add_custom_button(
            "GSTR 2A",
            () => {
                reco_tool.dialog_download_data(frm, "GSTR 2A");
            },
            "Download"
        );
        frm.add_custom_button(
            "GSTR 2B",
            () => {
                reco_tool.dialog_download_data(frm, "GSTR 2B");
            },
            "Download"
        );
    },
    purchase_period: function (frm) {
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.purchase_period,
            "purchase_from_date",
            "purchase_to_date"
        );
    },
    inward_supply_period: function (frm) {
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.inward_supply_period,
            "inward_supply_from_date",
            "inward_supply_to_date"
        );
    },
});

adaequare_gsp.get_date_range = function (frm, period, from_date, to_date) {
    if (period == "Custom") return;
    frappe.call({
        method: "adaequare_gsp.api.reco_tool.get_date_range",
        args: {
            period: period,
        },
        callback: function (r) {
            frm.set_value(from_date, r.message[0]);
            frm.set_value(to_date, r.message[1]);
        },
    });
};

reco_tool.dialog_download_data = function (frm, gst_return) {
    if (frm.doctype != "Purchase Reconciliation Tool") return;
    let d = new frappe.ui.Dialog({
        title: "Download Data from GSTN",
        fields: [
            {
                label: "GST Return Name",
                fieldname: "gst_return",
                fieldtype: "Data",
                read_only: 1,
                default: gst_return,
            },
            {
                fieldtype: "Column Break",
            },
            {
                label: "Fiscal Year",
                fieldname: "fiscal_year",
                fieldtype: "Link",
                options: "Fiscal Year",
                default: frappe.defaults.get_default("fiscal_year"),
                get_query: () => {
                    return {
                        filters: {
                            year_end_date: [">", "2017-06-30"],
                        },
                    };
                },
                onchange() {
                    reco_tool.fetch_download_history(frm, d);
                },
            },
            {
                label: "Download History",
                fieldtype: "Section Break",
            },
            {
                label: "Download History",
                fieldname: "download_history",
                fieldtype: "HTML",
            },
        ],
        primary_action_label: gst_return == "GSTR 2A" ? "Download All" : "Download",
		primary_action() {
			reco_tool.download_gstr(frm, d, "download_all_gstr")
            d.hide();
        },
        secondary_action_label: gst_return == "GSTR 2A" ? "Download Missing" : "",
        secondary_action() {
			reco_tool.download_gstr(frm, d, "download_missing_gstr")
            d.hide();
        },
    });
    d.show();
    reco_tool.fetch_download_history(frm, d);
};

reco_tool.fetch_download_history = function (frm, d) {
    frm.call("fetch_download_history", {
		gstr_name: d.fields_dict.gst_return.value,
		fiscal_year: d.fields_dict.fiscal_year.value,
	}).then(r => {
		if (!r.message) {
			return;
		}
		d.fields[4].options = r.message;
		d.refresh();
	})
};

reco_tool.download_gstr = function (frm, d, method, otp=null) {
	frm.call(method, {
		gstr_name: d.fields_dict.gst_return.value,
		fiscal_year: d.fields_dict.fiscal_year.value,
		otp: otp
	}).then(r => {
		if (r.message.errorCode == 'RETOTPREQUEST') {
			reco_tool.get_gstin_otp(reco_tool.download_gstr, frm, d, method)
		}
	})
}