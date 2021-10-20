import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_install():
    make_custom_fields()

def make_custom_fields():
    create_custom_fields(custom_fields)
    frappe.db.commit()

gstin_fields = [
    {
        'fieldname': 'section_gstin_info',
        'label': 'GSTIN Information',
        'fieldtype': 'Section Break',
        'insert_after': 'is_frozen',
    },
    {
        'fieldname': 'gstin_info_updated_on',
        'label': 'Updated On',
        'fieldtype': 'Datetime',
        'insert_after': 'section_gstin_info',
        'read_only': 1
    },
    {
        'fieldname': 'gstin_info',
        'label': 'GSTIN Info',
        'fieldtype': 'Code',
        'insert_after': 'gstin_info_updated_on',
        'hidden': 1
    },
    {
        'fieldname': 'cb_gstin_info',
        'fieldtype': 'Column Break',
        'insert_after': 'gstin_info',
    },
    {
        'fieldname': 'ctb',
        'label': 'Constitution of Business',
        'fieldtype': 'Data',
        'insert_after': 'cb_gstin_info',
        'read_only': 1
    },
    {
        'fieldname': 'sts',
        'label': 'Status of GSTIN',
        'fieldtype': 'Data',
        'insert_after': 'ctb',
        'read_only': 1
    },
]

custom_fields = {
    'Supplier': gstin_fields,
    'Customer': gstin_fields
}