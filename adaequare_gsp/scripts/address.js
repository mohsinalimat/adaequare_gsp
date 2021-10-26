frappe.ui.form.on("Address", {
    gstin(frm) {
        adaequare_gsp.autofill_gstin_fields(frm);
    },
    pincode(frm) {
        adaequare_gsp.autofill_address(frm);
    },
});
