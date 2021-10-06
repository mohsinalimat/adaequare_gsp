import frappe, requests
from requests.api import get

@frappe.whitelist()
def get_gstin_details():
    gsp_authentication = get_gsp_authentication()
    print(gsp_authentication)
    return gsp_authentication
    # response = requests.get("https://api.postalpincode.in/pincode/{}".format(pincode))
    # pincode_details = response.json()[0]

    # if pincode_details["Status"] == "Success" :
    #     pincode_district = pincode_details["PostOffice"][0]["District"]
    #     pincode_state = pincode_details["PostOffice"][0]["State"]
    #     pincode_area = []

    #     for name in pincode_details["PostOffice"]:
    #         pincode_area.append(name["Name"])

    #     return pincode_district, pincode_state, pincode_area
    # else:
    #     return []

def get_gsp_authentication():
    response = requests.post("https://gsp.adaequare.com/gsp/authenticate?grant_type=token", headers={
        "gspappid": "837CE61BB8054A9186D64754F9089D80",
        "gspappsecret": "ABB36C3AGF8A8G4D03G9ABBG7437CB17A798"
    })
    gsp_authentication = response.json()
    return gsp_authentication
