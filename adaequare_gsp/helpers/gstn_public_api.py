import frappe
from adaequare_gsp.helpers.auth_api import AuthApi


class GstnPublicApi(AuthApi):
    def __init__(self):
        super().__init__()
        self.api_name = "enriched/commonapi/"

    def get_gstin_info(self, gstin):
        response = self.make_request(
            method="get", action="TP", gstin=gstin, url_suffix="search?"
        )
        return frappe._dict(response)

    def get_returns_info(self, gstin, fy):
        if len(fy) == 9:
            start, end = fy.split("-")
            fy = f"{start}-{end[-2:]}"
        response = self.make_request(
            method="get", action="RETTRACK", gstin=gstin, fy=fy, url_suffix="returns?"
        )
        return frappe._dict(response)
