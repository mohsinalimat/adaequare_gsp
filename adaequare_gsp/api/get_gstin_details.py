import frappe
from adaequare_gsp.helpers.gstn_public_api import GstnPublicApi

@frappe.whitelist()
def get_gstin_details(gstin):
    api = GstnPublicApi()
    gstin_details = api.get_gstin_info(gstin)
    return gstin_details
