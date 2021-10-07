from adaequare_gsp.api.auth_api import AuthApi

class GstPublicApi(AuthApi):
    def __init__(self):
        super().__init__()
        self.api_name = 'enriched/commonapi/'

    def get_gstin_info(self, gstin):
        response = self.get_request('TP', gstin, url_suffix='search?')
        return response

    def get_returns_info(self, gstin, fy):
        response = self.get_request('RETTRACK', gstin, fy=fy, url_suffix='returns?')
        return response