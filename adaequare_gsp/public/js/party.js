let party_doctype_list = ['Customer', 'Supplier']
for (let dt of party_doctype_list) {
    frappe.ui.form.on(dt, {
        refresh: function (frm) {
            frm.add_custom_button('Update Party GSTIN Information', () => {
                frappe.call({
                    method: 'adaequare_gsp.api.get_gstin_details.update_party',
                    args: {
                        dt: frm.doc.doctype,
                        dn: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc()
                            frappe.msgprint(__('GST Information Updated Successfully.'))

                        }
                    }
                })
            }, 'Actions');  
        }
    })
}