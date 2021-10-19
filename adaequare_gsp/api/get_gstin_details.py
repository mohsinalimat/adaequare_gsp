import frappe
from adaequare_gsp.helpers.gstn_public_api import GstnPublicApi

@frappe.whitelist()
def get_gstin_details(gstin):
    api = GstnPublicApi()
    return api.get_gstin_info(gstin)
