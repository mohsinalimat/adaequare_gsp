import frappe
from frappe import _
from erpnext.selling.doctype.customer import customer

custom_make_address = customer.make_address

def make_address(args, is_primary_address=1):
    reqd_fields = []
    for field in ['city', 'country']:
        if not args.get(field):
            reqd_fields.append( '<li>' + field.title() + '</li>')

    if reqd_fields:
        msg = _("Following fields are mandatory to create address:")
        frappe.throw("{0} <br><br> <ul>{1}</ul>".format(msg, '\n'.join(reqd_fields)),
        title = _("Missing Values Required"))

    address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': args.get('name'),
        'address_line1': args.get('address_line1'),
        'address_line2': args.get('address_line2'),
        'city': args.get('city'),
        'state': args.get('state'),
        'pincode': args.get('pincode'),
        'country': args.get('country'),
        'gstin': args.get('gstin'),
        'links': [{
            'link_doctype': args.get('doctype'),
            'link_name': args.get('name')
        }]
    }).insert()

    return address

customer.make_address = make_address