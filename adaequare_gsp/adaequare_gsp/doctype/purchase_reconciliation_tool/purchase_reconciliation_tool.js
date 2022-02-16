// Copyright (c) 2022, Resilient Tech and contributors
// For license information, please see license.txt
frappe.provide("adaequare_gsp");
frappe.provide("reco_tool");

frappe.ui.form.on("Purchase Reconciliation Tool", {
    refresh(frm) {
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
    purchase_period(frm) {
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.purchase_period,
            "purchase_from_date",
            "purchase_to_date"
        );
    },
    inward_supply_period(frm) {
        adaequare_gsp.get_date_range(
            frm,
            frm.doc.inward_supply_period,
            "inward_supply_from_date",
            "inward_supply_to_date"
        );
    },
    setup(frm) {
        frm.trigger("render_data_table");
    },
    render_data_table(frm) {
        const tabs = [
            {
                label: "Summary",
                name: "summary",
            },
            {
                label: "Supplier Level",
                name: "supplier_level",
            },
            {
                label: "Invoice Level",
                name: "invoice_level",
            },
        ];

        const $data_table_wrapper = frm.get_field("data_table").$wrapper;
        $data_table_wrapper.html(
            `${frappe.render_template("data_table_tab_view", {
                tabs,
            })}`
        );

        const $tabs = $data_table_wrapper.find(".form-tabs .tab-item");
        $tabs.click(function () {
            const $this = $(this);
            $tabs.removeClass("active");
            $this.addClass("active");
            frm.trigger(`render_${$this.attr("data-name")}_data`);
        });

        $tabs[0].click();
        frm.$data_table = $data_table_wrapper.find(".tab-content");
    },
    render_summary_data(frm) {
        frm.purchase_reconciliation_data_table_manager =
            new adaequare_gsp.DataTableManager({
                frm: frm,
                $reconciliation_tool_dt: frm.$data_table,
                $no_data: $(
                    '<div class="text-muted text-center">No Matching Data Found</div>'
                ),
                method: "get_summary_data",
                args: {
                    company_gstin: frm.doc.company_gstin,
                    purchase_from_date: frm.doc.purchase_from_date,
                    purchase_to_date: frm.doc.purchase_to_date,
                    inward_from_date: frm.doc.inward_supply_from_date,
                    inward_to_date: frm.doc.inward_supply_to_date,
                },
                columns: [
                    {
                        name: "Match Type",
                    },
                    {
                        name: "No. of Doc Inward Supply",
                        width: 200,
                    },
                    {
                        name: "No. of Doc Purchase",
                        width: 150,
                    },
                    {
                        name: "Tax Diff",
                    },
                ],
                format_row(row) {
                    return [
                        row["match_status"],
                        row["no_of_inward_supp"],
                        row["no_of_doc_purchase"],
                        row["tax_diff"],
                    ];
                },
            });
    },
    render_supplier_level_data(frm) {
        frm.purchase_reconciliation_data_table_manager =
            new adaequare_gsp.DataTableManager({
                frm: frm,
                $reconciliation_tool_dt: frm.$data_table,
                $no_data: $(
                    '<div class="text-muted text-center">No Matching Data Found</div>'
                ),
                method: "get_b2b_purchase",
                args: {
                    company_gstin: frm.doc.company_gstin,
                    purchase_from_date: frm.doc.purchase_from_date,
                    purchase_to_date: frm.doc.purchase_to_date,
                },
                columns: [
                    {
                        name: "GSTIN",
                    },
                    {
                        name: "Supplier Name",
                        width: 200,
                    },
                    {
                        name: "No. of Doc Inward Supply",
                        width: 200,
                    },
                    {
                        name: "No. of Doc Purchase",
                        width: 200,
                    },
                    {
                        name: "Tax Diff",
                    },
                ],
                format_row(row) {
                    return [
                        row[0]["supplier_gstin"],
                        row[0]["supplier_name"],
                        row[0]["no_of_inward_supp"],
                        row.length,
                        row[0]["tax_diff"],
                    ];
                },
            });
    },
    render_invoice_level_data(frm) {
        frm.purchase_reconciliation_data_table_manager =
            new adaequare_gsp.DataTableManager({
                frm: frm,
                $reconciliation_tool_dt: frm.$data_table,
                $no_data: $(
                    '<div class="text-muted text-center">No Matching Data Found</div>'
                ),
                method: "get_b2b_purchase",
                args: {
                    company_gstin: frm.doc.company_gstin,
                    purchase_from_date: frm.doc.purchase_from_date,
                    purchase_to_date: frm.doc.purchase_to_date,
                },
                columns: [
                    {
                        name: "GSTIN",
                        width: 150,
                    },
                    {
                        name: "Supplier Name",
                        width: 200,
                    },
                    {
                        name: "Inv No.",
                        width: 120,
                    },
                    {
                        name: "Date",
                        width: 150,
                    },
                    {
                        name: "Action Status",
                    },
                    {
                        name: "Match Status",
                    },
                    {
                        name: "Purchase Ref",
                    },
                    {
                        name: "Inward Supp Ref",
                    },
                    {
                        name: "Tax Diff",
                    },
                    {
                        name: "Mismatch",
                    },
                    {
                        name: "GSActionTIN",
                    },
                ],
                format_row(row) {
                    return [
                        row[0]["supplier_gstin"],
                        row[0]["supplier_name"],
                        row[0]["bill_no"],
                        row[0]["bill_date"],
                        "",
                        "",
                        row[0]["name"],
                        "",
                        "",
                        "",
                        "",
                    ];
                },
            });
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
        primary_action_label:
            gst_return == "GSTR 2A" ? "Download All" : "Download",
        primary_action() {
            reco_tool.download_gstr(frm, d, "download_all_gstr");
            d.hide();
        },
        secondary_action_label:
            gst_return == "GSTR 2A" ? "Download Missing" : "",
        secondary_action() {
            reco_tool.download_gstr(frm, d, "download_missing_gstr");
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
    }).then((r) => {
        if (!r.message) {
            return;
        }
        d.fields.find((f) => f.fieldname == "download_history").options =
            r.message;
        d.refresh();
    });
};

reco_tool.download_gstr = function (frm, d, method, otp = null) {
    frm.call(method, {
        gstr_name: d.fields_dict.gst_return.value,
        fiscal_year: d.fields_dict.fiscal_year.value,
        otp: otp,
    }).then((r) => {
        if (r.message.errorCode == "RETOTPREQUEST") {
            reco_tool.get_gstin_otp(reco_tool.download_gstr, frm, d, method);
        }
    });
};
