frappe.provide('frappe.ui.form');

frappe.ui.form.SupplierQuickEntryForm = frappe.ui.form.CustomerQuickEntryForm = frappe.ui.form.QuickEntryForm.extend({
	init: function (doctype, after_insert, init_callback, doc, force) {
		this._super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	},

	render_dialog: function () {
		let me = this;
		this.mandatory = adaequare_gsp.get_gstin_fields(me).concat(this.mandatory);
		this.mandatory = this.mandatory.concat(adaequare_gsp.get_variant_fields(me));
		this._super();
	}
});