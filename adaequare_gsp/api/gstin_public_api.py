from adaequare_gsp.api.auth_api import AuthApi

class GstPublicApi(AuthApi):
    def __init__(self):
        super().__init__()
        self.access_token = self.get_access_token()