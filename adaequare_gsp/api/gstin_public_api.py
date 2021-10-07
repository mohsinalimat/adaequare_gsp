import frappe
from adaequare_gsp.api.auth_api import AuthApi
from requests import api

class GstPublicApi(AuthApi):
    def __init__(self):
        super().__init__()
        self.access_token = self.get_access_token()
        self.api_name = 'enriched/commonapi/'

        #header keys
        self.auth_key = 'Authorization'

        #param keys
        self.action_key = 'action'
        self.gstin_key = 'gstin'
        self.fy_key = 'fy'

        #result keys
        self.result_key = 'result'

    def get_gstin_info(self, gstin):
        headers = {}
        headers[self.auth_key] = self.access_token

        params = {}
        params[self.action_key] = 'TP'
        params[self.gstin_key] = gstin

        response = api.get('{}{}{}search?'.format(self.BASE_URL, self.test_url, self.api_name), 
            params=params, headers=headers).json()

        if not response.get(self.result_key):
            self.log_response(error=response)
        
        self.log_response(response)

        return response.get(self.result_key)

    def get_returns_info(self, gstin, fy):
        headers = {}
        headers[self.auth_key] = self.access_token

        params = {}
        params[self.action_key] = 'RETTRACK'
        params[self.gstin_key] = gstin
        params[self.fy_key] = fy

        response = api.get('{}{}{}returns?'.format(self.BASE_URL, self.test_url, self.api_name), 
            params=params, headers=headers).json()

        if not response.get(self.result_key):
            self.log_response(error=response)
        
        self.log_response(response)

        return response.get(self.result_key)