import json
from re import U

from frappe.model.naming import make_autoname
from adaequare_gsp.api.auth_api import AuthApi

class GstnEwbApi(AuthApi):
    FUNCTIONS = {
        'generate_eway_bill': {
            'action': 'GENEWAYBILL'
        },
        'update_vehicle_info':{
            'action': 'VEHEWB'
        },
        'update_transporter':{
            'action': 'UPDATETRANSPORTER'
        },
        'extend_validity':{
            'action': 'EXTENDVALIDITY'
        },
        'cancel_eway_bill':{
            'action': 'CANEWB'
        }
    }

    def __init__(self):
        super().__init__()
        self.api_name = 'enriched/ewb/'
        self.url_suffix = 'ewayapi?'
        self.comp_gstin = self.settings.gstin 
        self.username = self.settings.username 
        self.password = self.settings.get_password('password')
        
        for method_name in self.FUNCTIONS:
            setattr(self, method_name, self.get_method(method_name))

    def get_eway_bill(self, ewbNo):
        response = self.make_request(
            method='get',
            ewbNo=ewbNo,
            url_suffix='ewayapi/GetEwayBill?'
        )
        return response

    # generate post methods with different actions.
    def get_method(self, method_name):
        def execute(data):
            data = json.dumps(data)
            response = self.make_request(
                method='post',
                action= self.FUNCTIONS[method_name]['action'],
                url_suffix=self.url_suffix,
                data=data
            )
            return response
        return execute
