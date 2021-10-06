import frappe, requests
from adaequare_gsp.api.gstin_public_api import GstPublicApi
from requests.api import get

@frappe.whitelist()
def get_gstin_details():
    gsp_authentication = get_gsp_authentication()
    return gsp_authentication

def get_gsp_authentication():
    api = GstPublicApi()
    return api.access_token
