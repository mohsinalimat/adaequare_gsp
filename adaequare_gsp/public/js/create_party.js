frappe.provide("frappe.ui.form");
frappe.ui.form.SupplierQuickEntryForm = frappe.ui.form.CustomerQuickEntryForm = class CustomerQuickEntryForm extends (
    frappe.ui.form.QuickEntryForm
) {
    constructor(doctype, after_insert, init_callback, doc, force) {
        super(doctype, after_insert, init_callback, doc, force);
        this.skip_redirect_on_error = true;
    }

    render_dialog() {
        let me = this;
        this.mandatory = adaequare_gsp
            .get_gstin_fields(me)
            .concat(this.mandatory);
        this.mandatory = this.mandatory.concat(
            adaequare_gsp.get_variant_fields(me)
        );
        super.render_dialog();
    }
};

frappe.ui.form.AddressQuickEntryForm = class AddressQuickEntryForm extends (
    frappe.ui.form.QuickEntryForm
) {
    constructor(doctype, after_insert, init_callback, doc, force) {
        super(doctype, after_insert, init_callback, doc, force);
        this.skip_redirect_on_error = true;
    }

    render_dialog() {
        let me = this;
        let address_fields = adaequare_gsp.get_address_fields(me);
        this.mandatory = this.mandatory.filter(function (val) {
            for (let f of address_fields) {
                if (val.fieldname == "pincode") return false;
                if (f.fieldname != val.fieldname) continue;
                return false;
            }
            return true;
        });
        this.mandatory = adaequare_gsp
            .get_party_fields(me)
            .concat(this.mandatory);
        this.mandatory = this.mandatory.concat(address_fields);
        super.render_dialog();
    }
};
