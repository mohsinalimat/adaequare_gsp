import json
import frappe

from adaequare_gsp.helpers.auth_api import AuthApi


class GstnReturnsApi(AuthApi):
    def __init__(self, company_gstin):
        super().__init__()
        self.uid = frappe.utils.random_string(7)
        self.api_name = "enriched/returns"
        self.comp_gstin = company_gstin
        for creds in self.settings.gst_credentials:
            if creds.gstin == company_gstin and creds.service == "Returns":
                self.username = creds.username
                self.company = creds.company
                break

        # sandbox
        if self.settings.sandbox:
            self.comp_gstin = "33ANSPV5075F1ZH"
            self.username = "TN_NT2.1186"

        if not self.username:
            frappe.throw(
                "You have not set credentials in Adequare Settings. Kindly set your GST credentials to use API service.",
                title="Credentials unavailable",
            )

    def get_params(self, action, ret_period):
        return {
            "action": action,
            "gstin": self.comp_gstin,
            "rtnprd": ret_period,
            "ret_period": ret_period,
        }

    def get_headers(self, ret_period, otp):
        return {
            "username": self.username,
            "state-cd": self.comp_gstin[:2],
            "requestid": self.generate_request_id(),
            "gstin": self.comp_gstin,
            "ret_period": ret_period,
            "otp": otp,
            "Authorization": self.settings.access_token,
        }

    def make_get_request(self, action, ret_period, otp):
        response = self.make_request(
            method="get",
            url_suffix=self.url_suffix,
            params=self.get_params(action, ret_period),
            headers=self.get_headers(ret_period, otp),
        )
        return frappe._dict(response)


class Gstr2bApi(GstnReturnsApi):
    def __init__(self, company_gstin):
        super().__init__(company_gstin)
        self.url_suffix = "/gstr2b?"

    def get_gstr_2b(self, ret_period, otp):
        return self.make_get_request("GET2B", ret_period, otp)
