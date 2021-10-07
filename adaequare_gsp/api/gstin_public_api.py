import frappe
from adaequare_gsp.api.auth_api import AuthApi
from requests import api

class GstPublicApi(AuthApi):
    SANDBOX = True
    def __init__(self, gstin):
        super().__init__()
        self.access_token = self.get_access_token()
        self.gstin = gstin
        self.test_url = 'test/' if self.SANDBOX else None

    def get_gstin_info(self):
        headers = {}
        headers['Authorization'] = self.access_token

        params = {}
        params['action'] = 'TP'
        params['gstin'] = self.gstin

        response = api.get('{}{}enriched/commonapi/search?'.format(self.BASE_URL, self.test_url), 
            params=params, headers=headers).json()

        if not response.get('success'):
            error_des = '{}. Error Code:{}.'.format(response.get('message'), response.get('errorCode'))
            self.log_response(error=response, error_des=error_des)
        
        self.log_response(response)

        return response.get('result')