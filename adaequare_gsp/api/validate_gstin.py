import frappe
from erpnext.regional.india.utils import GSTIN_FORMAT, GSTIN_UIN_FORMAT, validate_gstin_check_digit


@frappe.whitelist()
def validate_gstin(gstin):
    if GSTIN_FORMAT.match(gstin) or GSTIN_UIN_FORMAT.match(gstin):
        validate_gstin_check_digit(gstin)
        return True
    else:
        return False