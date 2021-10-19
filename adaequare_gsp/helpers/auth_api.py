import frappe, json
import string, random

from frappe.utils import now, add_to_date
from requests import api


class AuthApi:
    BASE_URL = "https://gsp.adaequare.com/"

    def __init__(self):
        self.settings = frappe.get_doc("Adaequare Settings")
        self.gspappid = self.settings.gspappid
        self.gspappsecret = self.settings.get_password("gspappsecret")
        self.test_url = "test/" if self.settings.sandbox else ""
        self.access_token = self.get_access_token()

    def get_access_token(self):
        if not self.settings.access_token or not self.is_valid_access_token():
            self.generate_access_token()
        return self.settings.access_token

    def is_valid_access_token(self):
        return self.settings.expires_at and now() < self.settings.expires_at

    def generate_access_token(self):
        headers = {}
        headers["gspappid"] = self.gspappid
        headers["gspappsecret"] = self.gspappsecret

        params = {}
        params["grant_type"] = "token"

        response = api.post(
            "{}gsp/authenticate?".format(self.BASE_URL), params=params, headers=headers
        ).json()

        if not response.get("access_token"):
            self.log_response(error=response)

        self.settings.access_token = (
            response.get("token_type") + " " + response.get("access_token")
        )
        self.settings.expires_at = add_to_date(
            now(), seconds=response.get("expires_in")
        )
        self.settings.save(ignore_permissions=True, ignore_version=True)
        self.log_response(response)

    def log_response(
        self, response=None, data=None, doctype=None, docname=None, error=None
    ):

        request_log = frappe.get_doc(
            {
                "doctype": "Integration Request",
                "integration_type": "Remote",
                "integration_request_service": "Adaequare",
                "reference_doctype": doctype,
                "reference_docname": docname,
                "data": json.dumps(data, indent=4) if isinstance(data, dict) else data,
                "output": json.dumps(response, indent=4) if response else None,
                "error": json.dumps(error, indent=4) if error else None,
                "status": "Failed" if error else "Completed",
            }
        )
        request_log.insert(ignore_permissions=True)

        if error:
            frappe.db.commit()
            error_des = "{}{}{}".format(
                error.get("error_description", ""),
                error.get("message", ""),
                ". Error Code: " + error.get("errorCode")
                if error.get("errorCode")
                else "",
            )
            frappe.throw(error_des)

    def make_request(
        self, method, action=None, gstin=None, ewbNo=None, fy="", url_suffix="", data=""
    ):
        if method not in ("get", "post"):
            frappe.throw("Invalid method", upper(method))

        headers = {"Authorization": self.access_token}

        params = {
            "action": action,
            "gstin": gstin,
            "fy": fy,
        }

        # additional headers and parms for ewayapi
        if "ewayapi" in url_suffix:
            headers.update(
                {
                    "requestid": self.generate_request_id(),
                    "gstin": self.settings.gstin,
                    "username": self.settings.username,
                    "password": self.settings.get_password("password"),
                }
            )

            params["ewbNo"] = ewbNo

        # api calls
        url = self.BASE_URL + self.test_url + self.api_name + url_suffix
        if method == "get":
            response = api.get(url, params=params, headers=headers).json()
        else:
            response = api.post(url, params=params, headers=headers, data=data).json()

        result = response.get("result")
        self.log_response(**{("response" if result else "error"): response})
        return result

    def generate_request_id(self, length=12):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
