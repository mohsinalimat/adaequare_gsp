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
        frm.add_custom_button(
            "GSTR 2A",
            () => {
                reco_tool.dialog_upload_data(frm, "GSTR 2A");
            },
            "Upload"
        )
        frm.add_custom_button(
            "GSTR 2B",
            () => {
                reco_tool.dialog_upload_data(frm, "GSTR 2B");
            },
            "Upload"
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
        fields: reco_tool.get_upload_or_download_dialog_fields(frm, gst_return, "download"),
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
    reco_tool.fetch_download_history(frm, d, "download");
};

reco_tool.dialog_upload_data = function (frm, gst_return) {
    if (frm.doctype != "Purchase Reconciliation Tool") return;
    let d = new frappe.ui.Dialog({
        title: "Upload Data GSTN",
        fields: reco_tool.get_upload_or_download_dialog_fields(frm, gst_return, "upload"),
        primary_action_label: "Upload",
        primary_action() {
            reco_tool.upload_gstr(frm, d, "upload_gstr")
            d.hide();
        }
    });
    d.show();
    reco_tool.fetch_download_history(frm, d, "upload");
};

reco_tool.fetch_download_history = function (frm, d, type) {
    frm.call("fetch_download_history", {
		gstr_name: d.fields_dict.gst_return.value,
		fiscal_year: d.fields_dict.fiscal_year.value,
        process_type: type
	}).then(r => {
		if (!r.message) {
			return;
		}
        d.fields.find(f => f.fieldname == "download_history").options = r.message;
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

reco_tool.upload_gstr = function (frm, d, method) {
	frm.call(method, {
        gst_return: d.fields_dict.gst_return.value,
        period: d.fields_dict.period.value,
		attach_file: d.fields_dict.attach_file.value
	}).then(r => {
        frappe.msgprint(r.message);
	})
}

reco_tool.validate_file_format = function (frm, attached_file) {
    frappe.call({
        method: "adaequare_gsp.api.gstr_2b.validate_file_format", 
        args: {
		attach_file: attached_file
        },
        callback: function(r) {
            if (!r.message) {
                return;
            }
        }
    })    
}

reco_tool.get_uploaded_gstr_ret_period = function (frm, cur_dialog) {
    frm.call("get_uploaded_gstr_ret_period", 
    {
    gst_return: cur_dialog.fields_dict.gst_return.value,
    attach_file: cur_dialog.fields_dict.attach_file.value
    }).then(r => {
        console.log(r.message);
        if (!r.message) {
            frappe.msgprint("Return Period not found");
            cur_dialog.hide();
            return;
        }
        cur_dialog.set_value("period", r.message);
    })
}

reco_tool.get_upload_or_download_dialog_fields = function (frm, gst_return, type) {
    if (type == "download") {
        return [
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
                    reco_tool.fetch_download_history(frm, cur_dialog, "download");
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
        ]
    }
    else if (type == "upload") {
        return [
            {
                label: "GST Return Name",
                fieldname: "gst_return",
                fieldtype: "Data",
                read_only: 1,
                default: gst_return,
            },
            {
                label: "Period",
                fieldname: "period",
                fieldtype: "Data",
                read_only: 1,
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
                    reco_tool.fetch_download_history(frm, cur_dialog, "download");
                },
            },
            {
                label: "Attach File",
                fieldname: "attach_file",
                fieldtype: "Attach",
                onchange() {
                    let attached_file = cur_dialog.fields_dict.attach_file.value;
                    if (attached_file) {
                        reco_tool.validate_file_format(frm, attached_file);
                        reco_tool.get_uploaded_gstr_ret_period(frm, cur_dialog);
                    }
                }
            },
            {
                label: "Upload History",
                fieldtype: "Section Break",
            },
            {
                label: "Upload History",
                fieldname: "download_history",
                fieldtype: "HTML",
            },
        ]
    }
}

var purchase_reco_data_manager = class DataTableManager {
	constructor(opts) {
		Object.assign(this, opts);
		this.make_dt();
	}

	make_dt() {
		var me = this;
        console.log(this.frm);
        if (this.$summary_dt) {
            var args = {
                company_gstin: this.frm.doc.company_gstin,
                purchase_from_date: this.frm.doc.purchase_from_date,
                purchase_to_date: this.frm.doc.purchase_to_date,
                inward_from_date: this.frm.doc.inward_supply_from_date,
                inward_to_date: this.frm.doc.inward_supply_to_date
            }
            this.frm.call({
                method: "get_summary_data",
                args: args,
                callback: function (response) {
                    me.format_data(response.message);
                    me.get_dt_columns();
                    me.get_datatable();
                    me.set_listeners();
                },
            });
        }
        else if (this.$supplier_level_dt) {
            var method_to_call = "get_b2b_purchase"
            var args = {
                company_gstin: this.frm.doc.company_gstin,
                purchase_from_date: this.frm.doc.purchase_from_date,
                purchase_to_date: this.frm.doc.purchase_to_date
            }
        }
        else if (this.$invoice_level_dt) {
            var method_to_call = "get_b2b_purchase"
            var args = {
                company_gstin: this.frm.doc.company_gstin,
                purchase_from_date: this.frm.doc.purchase_from_date,
                purchase_to_date: this.frm.doc.purchase_to_date
            }
        }

        if (!this.$summary_dt) {
            this.frm.call(method_to_call, 
                args).then(r => {
                if (!r.message) {
                    return;
                }
                console.log(r.message);
                me.format_data(r.message);
                me.get_dt_columns();
                me.get_datatable();
                me.set_listeners();
            })
        }
	}


	format_data(res_message) {
		this.transactions = [];
        var res_data = res_message
        if (!Array.isArray(res_message)) {
            res_data = Object.values(res_message);
        }
        res_data.forEach((row) => {
            console.log(row)
			this.transactions.push(this.format_row(row));
		});
	}

    format_row(row) {
        if (this.$summary_dt) {
            return [
                row["match_status"],
                row["no_of_inward_supp"],
                row["no_of_doc_purchase"],
                row["tax_diff"]
            ]
        }
        if (this.$supplier_level_dt) {
            return [
                row[0]["supplier_gstin"],
                row[0]["supplier_name"],
                row[0]["no_of_inward_supp"],
                row.length,
                row[0]["tax_diff"]
            ];
        }
        if (this.$invoice_level_dt) {
            return [
                row[0]["supplier_gstin"],
                row[0]["supplier_name"],
                row[0]["no_of_inward_supp"],
                row[0]["no_of_doc_purchase"],
                row[0]["tax_diff"]
            ];
        }
	}

	get_dt_columns() {
        if (this.$summary_dt) {
            this.columns = [
                {
                    name: "Match Type",
                    editable: false,
                    width: 100,
                },
                {
                    name: "No. of Doc Inward Supply",
                    editable: false,
                    width: 200,
                },
                {
                    name: "No. of Doc Purchase",
                    editable: false,
                    width: 200,
                },
                {
                    name: "Tax Diff",
                    editable: false,
                    width: 100,
                },
            ];
        }
        if (this.$supplier_level_dt) {
            this.columns = [
                {
                    name: "GSTIN",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Supplier Name",
                    editable: false,
                    width: 150,
                },
                {
                    name: "No. of Doc Inward Supply",
                    editable: false,
                    width: 200,
                },
                {
                    name: "No. of Doc Purchase",
                    editable: false,
                    width: 200,
                },
                {
                    name: "Tax Diff",
                    editable: false,
                    width: 100,
                },
            ];
        }
        if (this.$invoice_level_dt) {
            this.columns = [
                {
                    name: "GSTIN",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Supplier Name",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Inv No.",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Date",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Action Status",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Match Status",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Purchase Ref",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Inward Supp Ref",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Tax Diff",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Mismatch",
                    editable: false,
                    width: 100,
                },
                {
                    name: "Action",
                    editable: false,
                    width: 100,
                },
            ];
        }
	}

	get_datatable() {
		const datatable_options = {
			columns: this.columns,
			data: this.transactions,
			dynamicRowHeight: true,
			checkboxColumn: true,
			inlineFilters: true,
			events: {
				onCheckRow: () => {
					const checked_items = this.get_checked_items();
					this.toggle_actions_menu_button(checked_items.length > 0);
				}
			},
		};
        if (this.$summary_dt) {
            this.datatable = new frappe.DataTable(
                this.$summary_dt.fieldobj.$wrapper.get(0),
                datatable_options
            );

            $(`.${this.datatable.style.scopeClass} .dt-scrollable`).css(
                {"max-height":"calc(500vh - 400px)", "overflow":"auto visible"}
            );
    
            if (this.transactions.length > 0) {
                console.log(this.datatable);
                this.$summary_dt.fieldobj.$wrapper.show();
            } else {
                this.$summary_dt.fieldobj.$wrapper.hide();
            }
        }
        else if (this.$supplier_level_dt) {
            this.datatable = new frappe.DataTable(
                this.$supplier_level_dt.fieldobj.$wrapper.get(0),
                datatable_options
            );

            $(`.${this.datatable.style.scopeClass} .dt-scrollable`).css(
                {"max-height":"calc(500vh - 400px)", "overflow":"auto visible"}
            );
    
            if (this.transactions.length > 0) {
                console.log(this.datatable);
                this.$supplier_level_dt.fieldobj.$wrapper.show();
            } else {
                this.$supplier_level_dt.fieldobj.$wrapper.hide();
            }
        }
		else if (this.$invoice_level_dt) {
            this.datatable = new frappe.DataTable(
                this.$invoice_level_dt.fieldobj.$wrapper.get(0),
                datatable_options
            );

            $(`.${this.datatable.style.scopeClass} .dt-scrollable`).css(
                {"max-height":"calc(500vh - 400px)", "overflow":"auto visible"}
            );
    
            if (this.transactions.length > 0) {
                console.log(this.datatable);
                this.$invoice_level_dt.fieldobj.$wrapper.show();
            } else {
                this.$invoice_level_dt.fieldobj.$wrapper.hide();
            }
        }
	}

    get_checked_items(only_docnames) {
        console.log(this.datatable);
		const indexes = this.datatable.rowmanager.getCheckedRows();
        console.log(indexes)
		const items = indexes.map(i => this.transactions[i]).filter(i => i != undefined);

		if (only_docnames) {
			return items.map(d => d.name);
		}
        console.log(items);
		return items;
	}

	set_listeners() {
		var me = this;
		// $(`.${this.datatable.style.scopeClass} .dt-scrollable`).on(
		// 	"click",
		// 	`.btn`,
		// 	function () {
		// 		me.dialog_manager.show_dialog(
		// 			$(this).attr("data-name"),
		// 			(bank_transaction) => me.update_dt_cards(bank_transaction)
		// 		);
		// 		return true;
		// 	}
		// );
	}
}