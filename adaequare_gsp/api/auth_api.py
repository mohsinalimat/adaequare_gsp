from time import time
import frappe
from frappe.utils import now, add_to_date
from frappe.integrations.utils import make_get_request, make_post_request
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
        response = make_post_request(self.AUTH_URL , headers={
            "gspappid": self.gspappid,
            "gspappsecret": self.gspappsecret
        })

        self.settings.access_token = response.get("access_token")
        self.settings.expires_at = add_to_date(now(), seconds = response.get("expires_in"))
        self.settings.save(ignore_permissions=True, ignore_version=True)

        self.log_response()

    def log_response():
        pass