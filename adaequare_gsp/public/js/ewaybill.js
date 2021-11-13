frappe.provide("adaequare_gsp");
let ewaybill_doctype_list = ['Sales Invoice']
for (let dt of ewaybill_doctype_list) {
    frappe.ui.form.on(dt, {
        refresh: function (frm) {
            frappe.model.get_value('Adaequare Settings', 'Adaequare Settings', 'gstn_ewb_api',
            function (d) {
                if (d.gstn_ewb_api == 0) return;
                if (!frm.doc.ewaybill && frm.doc.docstatus == 1) {
                    frm.add_custom_button('Generate Ewaybill', () => {
                        adaequare_gsp.dialog_generate_ewaybill(frm)
                    }, 'Ewaybill');
                }
                let now = new Date()
                if (frm.doc.docstatus == 1 &&
                frm.doc.ewaybill &&
                frm.doc.eway_bill_validity &&
                adaequare_gsp.get_date(frm.doc.eway_bill_validity) > now) {
                    frm.add_custom_button('Update Vehicle Info', () => {
                        adaequare_gsp.dialog_update_vehicle_info(frm)
                    }, 'Ewaybill');
                    frm.add_custom_button('Update Transporter', () => {
                        adaequare_gsp.dialog_update_transporter(frm)
                    }, 'Ewaybill');
                    frm.add_custom_button('Cancel Ewaybill', () => {
                        adaequare_gsp.dialog_cancel_ewaybill(frm)
                    }, 'Ewaybill');
                    // add other buttons
                }
                if (frm.doc.docstatus == 1 && frm.doc.ewaybill) {
                    frm.add_custom_button('Reprint Ewaybill', () => {
                        adaequare_gsp.reprint_ewaybill(frm)
                    }, 'Ewaybill');
                }
                if (frm.doc.docstatus == 1 &&
                    frm.doc.ewaybill &&
                    frm.doc.eway_bill_validity &&
                    !frm.doc.gst_transporter_id &&
                    (adaequare_gsp.get_date(frm.doc.eway_bill_validity) < now.addHours(8) ||
                    adaequare_gsp.get_date(frm.doc.eway_bill_validity).addHours(8) > now)) {
                    // frm.add_custom_button('Extend Validity', () => {
                    //     adaequare_gsp.dialog_extend_validity(frm)
                    // }, 'Ewaybill');
                }
            }) 
        }
    })
}

adaequare_gsp.reprint_ewaybill = function (frm) {
    if (!ewaybill_doctype_list.includes(frm.doc.doctype)) return;
    frappe.call({
        method: 'adaequare_gsp.api.ewaybill.print_ewaybill',
        args: {
            dt: frm.doc.doctype,
            dn: frm.doc.name,
            ewaybill: frm.doc.ewaybill,
        },
        callback: function (r) {
            frm.reload_doc()
            frappe.msgprint(__('Ewaybill Print Generated Successfully.'))
        }
    })
}
adaequare_gsp.dialog_generate_ewaybill = function (frm) {
    if (!ewaybill_doctype_list.includes(frm.doc.doctype)) return;
     let d = new frappe.ui.Dialog({
        title: 'Verify Details',
        fields: [
            {
                label: 'Transporter',
                fieldname: 'transporter',
                fieldtype: 'Link',
                options: 'Supplier',
                default: frm.doc.transporter,
                get_query: () => {
					return {
						filters: {
							is_transporter: 1,
						},
					};
                },
                onchange: function (e) {
                    adaequare_gsp.get_gst_tranporter_id(cur_dialog.fields_dict.transporter.value)
                },
            },
            {
                label: 'GST Transporter ID',
                fieldname: 'gst_transporter_id',
                fieldtype: 'Data',
                fetch_from: 'transporter.gst_transporter_id',
                default: (frm.doc.gst_transporter_id &&
                    frm.doc.gst_transporter_id.length == 15) ?
                    frm.doc.gst_transporter_id : ''
            },
            {
                label: 'Vehicle No',
                fieldname: 'vehicle_no',
                fieldtype: 'Data',
                default: frm.doc.vehicle_no
            },
            {
                label: 'Distance (in km)',
                fieldname: 'distance',
                fieldtype: 'Float',
                default: frm.doc.distance
            },
            {
                fieldtype: 'Column Break'
            },
            {
                label: 'Transport Receipt No',
                fieldname: 'lr_no',
                fieldtype: 'Data',
			    default: frm.doc.lr_no
            },
            {
                label: 'Transport Receipt Date',
                fieldname: 'lr_date',
                fieldtype: 'Date',
                default: frm.doc.lr_date
            },
            {
                label: 'Mode Of Transport',
                fieldname: 'mode_of_transport',
                fieldtype: 'Select',
                options: `\nRoad\nAir\nRail\nShip`,
                default: frm.doc.mode_of_transport
            },
            {
                label: 'GST Vehicle Type',
                fieldname: 'gst_vehicle_type',
                fieldtype: 'Select',
                options: `Regular\nOver Dimensional Cargo (ODC)`,
			    depends_on: 'eval:(doc.mode_of_transport === "Road")',
                default: frm.doc.gst_vehicle_type
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'gst_category',
                label: 'GST Category',
                fieldtype: 'Select',
			    options: '\nRegistered Regular\nRegistered Composition\nUnregistered\nSEZ\nOverseas\nConsumer\nDeemed Export\nUIN Holders',
                fetch_from: 'customer_address.gst_category',
                fetch_if_empty: 1,
                default: frm.doc.gst_category
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'export_type',
                label: 'Export Type',
                fieldtype: 'Select',
			    depends_on: 'eval:in_list(["SEZ", "Overseas", "Deemed Export"], doc.gst_category)',
                options: '\nWith Payment of Tax\nWithout Payment of Tax',
                fetch_from: 'customer_address.export_type',
                fetch_if_empty: 1,
                default: frm.doc.export_type
            }
        ],
        primary_action_label: 'Generate',
        primary_action(values) {
            frappe.call({
                method: 'adaequare_gsp.api.ewaybill.generate_ewaybill',
                args: {
                    dt: frm.doc.doctype,
                    dn: frm.doc.name,
                    dia: values
                },
                callback: function (r) {
                    frm.reload_doc()
                    if (!r.message) return;
                    frappe.msgprint(__(r.message))
                }
            })
            d.hide();
        }
    });

    d.show();
}

adaequare_gsp.dialog_cancel_ewaybill = function (frm) {
    if (!ewaybill_doctype_list.includes(frm.doc.doctype)) return;
     let d = new frappe.ui.Dialog({
        title: 'Are you sure you would like to cancel Ewaybill',
        fields: [
            {
                label: 'Ewaybill',
                fieldname: 'ewaybill',
                fieldtype: 'Data',
                read_only: 1,
                default: frm.doc.ewaybill
            },
            {
                label: "Reason",
                fieldname: "reason",
                fieldtype: "Select",
                reqd: 1,
                default: "3-Data Entry Error",
                options: ["1-Duplicate", "2-Order Cancelled", "3-Data Entry Error", "4-Others"]
            },
            {
                label: "Remark",
                fieldname: "remark",
                fieldtype: "Data",
                mandatory_depends_on: "eval: doc.reason == '4-Others'"
            }
        ],
        primary_action_label: 'Cancel Ewaybill',
        primary_action(values) {
            frappe.call({
                method: 'adaequare_gsp.api.ewaybill.cancel_ewaybill',
                args: {
                    dt: frm.doc.doctype,
                    dn: frm.doc.name,
                    dia: values
                },
                callback: function (r) {
                    frm.reload_doc()
                    frappe.msgprint(__("E-waybill Cancelled Successfully."))
                }
            })
            d.hide();
        }
    });

    d.show();
}

adaequare_gsp.dialog_update_vehicle_info = function (frm) {
    if (!ewaybill_doctype_list.includes(frm.doc.doctype)) return;
     let d = new frappe.ui.Dialog({
        title: 'Update Vehicle Information',
        fields: [
            {
                label: 'Ewaybill',
                fieldname: 'ewaybill',
                fieldtype: 'Data',
                read_only: 1,
			    default: frm.doc.ewaybill
            },
            {
                label: 'Vehicle No',
                fieldname: 'vehicle_no',
                fieldtype: 'Data',
                reqd: 1,
                default: frm.doc.vehicle_no
            },
            {
                label: 'Transport Receipt No',
                fieldname: 'lr_no',
                fieldtype: 'Data',
			    default: frm.doc.lr_no
            },
            {
                fieldtype: 'Column Break'
            },
            {
                label: 'Mode Of Transport',
                fieldname: 'mode_of_transport',
                fieldtype: 'Select',
                options: `\nRoad\nAir\nRail\nShip`,
                default: frm.doc.mode_of_transport
            },
            {
                label: 'GST Vehicle Type',
                fieldname: 'gst_vehicle_type',
                fieldtype: 'Select',
                options: `Regular\nOver Dimensional Cargo (ODC)`,
			    depends_on: 'eval:(doc.mode_of_transport === "Road")',
                default: frm.doc.gst_vehicle_type
            },
            {
                label: 'Transport Receipt Date',
                fieldname: 'lr_date',
                fieldtype: 'Date',
                default: frm.doc.lr_date
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'reason',
                label: 'Reason',
                fieldtype: 'Select',
			    options: ['1-Due to Break Down', '2-Due to Trans Shipment', '3-Others', '4-First Time'],
                reqd: 1 
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'remark',
                label: 'Remark',
                fieldtype: 'Data',
			    mandatory_depends_on: 'eval: doc.reason == "3-Others"',
            }
        ],
        primary_action_label: 'Update Vehicle Info',
        primary_action(values) {
            frappe.call({
                method: 'adaequare_gsp.api.ewaybill.update_vehicle_info',
                args: {
                    dt: frm.doc.doctype,
                    dn: frm.doc.name,
                    dia: values
                },
                callback: function (r) {
                    frm.reload_doc()
                    frappe.msgprint(__('Vehicle Information Updated Successfully.'))
                }
            })
            d.hide();
        }
    });

    d.show();
}

adaequare_gsp.dialog_update_transporter = function (frm) {
    if (!ewaybill_doctype_list.includes(frm.doc.doctype)) return;
     let d = new frappe.ui.Dialog({
        title: 'Update Transporter',
        fields: [
            {
                label: 'Ewaybill',
                fieldname: 'ewaybill',
                fieldtype: 'Data',
                read_only: 1,
                default: frm.doc.ewaybill
            },
            {
                label: 'Transporter',
                fieldname: 'transporter',
                fieldtype: 'Link',
                options: 'Supplier',
                default: frm.doc.transporter,
                get_query: () => {
					return {
						filters: {
							is_transporter: 1,
						},
					};
                },
                onchange: function () {
                    adaequare_gsp.get_gst_tranporter_id(cur_dialog.fields_dict.transporter.value)
                },
            },
            {
                label: 'GST Transporter ID',
                fieldname: 'gst_transporter_id',
                fieldtype: 'Data',
                reqd: 1,
                default: (frm.doc.gst_transporter_id && frm.doc.gst_transporter_id.length == 15) ? frm.doc.gst_transporter_id : ''
            }
        ],
        primary_action_label: 'Update Transporter',
        primary_action(values) {
            frappe.call({
                method: 'adaequare_gsp.api.ewaybill.update_transporter',
                args: {
                    dt: frm.doc.doctype,
                    dn: frm.doc.name,
                    dia: values
                },
                callback: function (r) {
                    frm.reload_doc()
                    frappe.msgprint(__("Transporter Updated Successfully."))
                }
            })
            d.hide();
        }
    });

    d.show();
}

adaequare_gsp.get_gst_tranporter_id = function (transporter) {
    frappe.model.get_value('Supplier', transporter, 'gst_transporter_id',
        function (r) {
            cur_dialog.fields_dict.gst_transporter_id.value = r.gst_transporter_id
            cur_dialog.refresh()
        }
    );
}

adaequare_gsp.get_date = function (text) {
    text = text.split(/[\s:\/]+/)
    let add_hours = text[6] == 'PM' ? 12 : 0
    return new Date(text[2],
        parseInt(text[1]) - 1,
        text[0],
        parseInt(text[3]) + add_hours,
        text[4],
        text[5])
}

Date.prototype.addHours = function(h) {
  this.setTime(this.getTime() + (h*60*60*1000));
  return this;
}