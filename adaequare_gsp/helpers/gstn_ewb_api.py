import json
import frappe

from adaequare_gsp.helpers.auth_api import AuthApi


class GstnEwbApi(AuthApi):
    def __init__(self):
        super().__init__()
        self.api_name = "enriched/ewb/"
        self.url_suffix = "ewayapi?"
        self.comp_gstin = self.settings.gstin
        self.username = self.settings.username
        self.password = self.settings.get_password("password")

    def get_ewaybill(self, ewbNo):
        response = self.make_request(
            method="get", ewbNo=ewbNo, url_suffix="ewayapi/GetEwayBill?"
        )
        return frappe._dict(response)

    # generate post methods with different actions.
    def make_post_request(self, action, data):
        data = json.dumps(data)
        response = self.make_request(
            method="post", action=action, url_suffix=self.url_suffix, data=data
        )
        return frappe._dict(response)

    def generate_ewaybill(self, data):
        return self.make_post_request("GENEWAYBILL", data)

    def update_vehicle_info(self, data):
        return self.make_post_request("VEHEWB", data)

    def update_transporter(self, data):
        return self.make_post_request("UPDATETRANSPORTER", data)

    def extend_validity(self, data):
        return self.make_post_request("EXTENDVALIDITY", data)

    def cancel_ewaybill(self, data):
        return self.make_post_request("CANEWB", data)
