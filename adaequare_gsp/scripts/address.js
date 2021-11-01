frappe.model.get_value('Adaequare Settings', 'Adaequare Settings', 'gstn_public_api',
    function (d) {
        if (d.gstn_public_api == 0) return;
        frappe.ui.form.on("Address", {
            gstin(frm) {
                adaequare_gsp.autofill_gstin_fields(frm);
            },
            pincode(frm) {
                adaequare_gsp.autofill_address(frm);
            },
        });
    }
)
