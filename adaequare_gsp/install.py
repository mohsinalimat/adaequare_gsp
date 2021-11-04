import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    make_custom_fields()
    update_custom_fields()


def update_custom_fields():
    fields = [["Sales Invoice-ewaybill", "read_only", 1]]
    for field in fields:
        frappe.db.set_value("Custom Field", field[0], field[1], field[2])


def make_custom_fields():
    create_custom_fields(custom_fields)
    frappe.db.commit()


gstin_fields = [
    {
        "fieldname": "section_gstin_info",
        "label": _("GSTIN Information"),
        "fieldtype": "Section Break",
        "insert_after": "is_frozen",
    },
    {
        "fieldname": "gstin_info_updated_on",
        "label": _("Updated On"),
        "fieldtype": "Datetime",
        "insert_after": "section_gstin_info",
        "read_only": 1,
        "translatable": 0,
    },
    {
        "fieldname": "default_gstin",
        "label": _("GSTIN"),
        "fieldtype": "Data",
        "insert_after": "gstin_info_updated_on",
        "read_only": 1,
        "translatable": 0,
    },
    {
        "fieldname": "trade_name",
        "label": _("Trade Name"),
        "fieldtype": "Data",
        "insert_after": "default_gstin",
        "read_only": 1,
        "translatable": 0,
    },
    {
        "fieldname": "gstin_info",
        "label": _("GSTIN Info"),
        "fieldtype": "Code",
        "insert_after": "trade_name",
        "hidden": 1,
        "translatable": 0,
    },
    {
        "fieldname": "cb_gstin_info",
        "fieldtype": "Column Break",
        "insert_after": "gstin_info",
    },
    {
        "fieldname": "ctb",
        "label": _("Constitution of Business"),
        "fieldtype": "Data",
        "insert_after": "cb_gstin_info",
        "read_only": 1,
        "translatable": 0,
    },
    {
        "fieldname": "sts",
        "label": _("Status of GSTIN"),
        "fieldtype": "Data",
        "insert_after": "ctb",
        "read_only": 1,
        "translatable": 0,
    },
]

custom_fields = {"Supplier": gstin_fields, "Customer": gstin_fields}
