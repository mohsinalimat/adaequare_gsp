import frappe, json
import string, random

from frappe.utils import now, add_to_date
from requests import api

class AuthApi:
    BASE_URL = 'https://gsp.adaequare.com/'

    def __init__(self):
        self.settings = frappe.get_doc('Adaequare Settings')
        self.gspappid = self.settings.gspappid
        self.gspappsecret = self.settings.get_password('gspappsecret')
        self.test_url = 'test/' if self.settings.sandbox else ''
        self.access_token = self.get_access_token()

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
        headers = {}
        headers['gspappid'] = self.gspappid
        headers['gspappsecret'] = self.gspappsecret

        params = {}
        params['grant_type'] = 'token'

        response = api.post('{}gsp/authenticate?'.format(self.BASE_URL), params=params, headers=headers).json()

        if not response.get('access_token'):
            self.log_response(error=response)

        self.settings.access_token = response.get('token_type') + ' ' + response.get('access_token')
        self.settings.expires_at = add_to_date(now(), seconds = response.get('expires_in'))
        self.settings.save(ignore_permissions=True, ignore_version=True)
        self.log_response(response)

    def log_response(self, response=None, data=None, doctype=None, docname=None, 
        error=None):

        request_log = frappe.get_doc({
            'doctype': 'Integration Request',
            'integration_type': 'Remote',
            'integration_request_service': 'Adaequare',
            'reference_doctype': doctype,
            'reference_docname': docname,
            'data': json.dumps(data, indent=4) if isinstance(data, dict) else data,
            'output': json.dumps(response, indent=4) if response else None,
            'error': json.dumps(error, indent=4) if error else None,
            'status': 'Failed' if error else 'Completed'
        })
        request_log.insert(ignore_permissions=True)

        if error:
            frappe.db.commit()
            error_des = '{}{}{}'.format(
                error.get('error_description', ''),
                error.get('message', ''),
                '. Error Code: ' + error.get('errorCode') if error.get('errorCode') else ''
            )
            frappe.throw(error_des)

    def make_request(self, method, action=None, gstin=None, ewbNo=None, fy='', url_suffix = '', data=''):
        headers = {}
        headers['Authorization'] = self.access_token

        params = {}
        params['action'] = action
        params['gstin'] = gstin
        params['fy'] = fy

        #additional headers and parms for ewayapi
        if 'ewayapi' in url_suffix:
            headers['requestid'] = self.generate_request_id()
            headers['gstin'] = self.settings.gstin
            headers['username'] = self.settings.username 
            headers['password'] = self.settings.get_password('password')

            params['ewbNo'] = ewbNo

        #api calls
        if method=='get':
            response = api.get('{}{}{}{}'.format(self.BASE_URL, self.test_url, self.api_name, url_suffix), 
                params=params, headers=headers).json()
        elif method=='post':
            response = api.post('{}{}{}{}'.format(self.BASE_URL, self.test_url, self.api_name, url_suffix), 
                params=params, headers=headers, data=data).json()

        result = response.get('result')
        if not result:
            self.log_response(error=response)
        
        self.log_response(response)
        return result 

    def generate_request_id(self):
        N = 12
        rand = ''.join(random.choices(string.ascii_uppercase +
            string.digits, k = N))
        return rand