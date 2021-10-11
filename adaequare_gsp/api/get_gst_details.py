import frappe
from adaequare_gsp.api.gstn_public_api import GstnPublicApi
from adaequare_gsp.api.gstn_ewb_api import GstnEwbApi

@frappe.whitelist()
def get_gstin_details():
    gsp_authentication = get_gsp_authentication()
    return gsp_authentication

def get_gsp_authentication():
    api = GstnEwbApi()
    return api.cancel_eway_bill(cancel)
