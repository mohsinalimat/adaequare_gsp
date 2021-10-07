import frappe, json
from frappe.utils import now, add_to_date
from requests import api

class AuthApi:
    AUTH_URL = 'https://gsp.adaequare.com/gsp/authenticate?grant_type=token'

    def __init__(self):
        self.settings = frappe.get_doc('Adaequare Settings')
        self.gspappid = self.settings.gspappid
        self.gspappsecret = self.settings.get_password('gspappsecret')

    def get_access_token(self):
        if not self.settings.access_token or self.access_token_invalid():
            self.generate_access_token()
        return self.settings.access_token

    def access_token_invalid(self):
        self.expires_at = self.settings.expires_at
        if self.expires_at and now() < self.expires_at:
            return False
        return True

    def generate_access_token(self):
        headers = {
            "gspappid": self.gspappid,
            "gspappsecret": self.gspappsecret
        }

        response = api.post(self.AUTH_URL , headers=headers).json()
        if response.get('error'):
            self.log_response(error=response, status="Failed")
            frappe.db.commit()
            frappe.throw(response.get("error_description"))
        self.settings.access_token = response.get("access_token")
        self.settings.expires_at = add_to_date(now(), seconds = response.get("expires_in"))
        self.settings.save(ignore_permissions=True, ignore_version=True)
        self.log_response(response)

    def log_response(self, response=None, data=None, doctype=None, docname=None, error=None, status="Completed"):
        request_log = frappe.get_doc({
            "doctype": "Integration Request",
            "integration_type": "Remote",
            "integration_request_service": "Adaequare",
            "reference_doctype": doctype,
            "reference_docname": docname,
            "data": json.dumps(data, indent=4) if isinstance(data, dict) else data,
            "output": json.dumps(response, indent=4) if response else None,
            "error": error,
            "status": status
        })
        request_log.insert(ignore_permissions=True)