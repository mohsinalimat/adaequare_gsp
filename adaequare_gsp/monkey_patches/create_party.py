import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from erpnext.selling.doctype.customer import customer
from erpnext.regional.india.utils import PAN_NUMBER_FORMAT

custom_make_address = customer.make_address

gst_category_map = {
    'Regular': 'Registered Regular',
    'Composition': 'Registered Composition',
    'SEZ Unit': 'SEZ',
    'Non Resident Online Services Provider': 'UIN Holders',
    'URP': 'Unregistered'
}

def make_address(args, is_primary_address=1):
    if args.get('gstin_info'):
        args.gstin_info = json.loads(args.get('gstin_info'))
    reqd_fields = []
    for field in ['city', 'country']:
        if not args.get(field):
            reqd_fields.append( '<li>' + field.title() + '</li>')

    if reqd_fields:
        msg = _("Following fields are mandatory to create address:")
        frappe.throw("{0} <br><br> <ul>{1}</ul>".format(msg, '\n'.join(reqd_fields)),
        title = _("Missing Values Required"))

    if args.get('gstin') == 'URP' or args.get('gstin') == 'NA':
        gst_category = gst_category_map['URP']
    else:
        gst_category = gst_category_map[args.get('gstin_info').get('dty')]

    address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': args.get('name'),
        'address_line1': args.get('address_line1'),
        'address_line2': args.get('address_line2'),
        'city': args.get('city'),
        'state': args.get('state'),
        'pincode': args.get('pincode'),
        'country': args.get('country'),
        'gstin': args.get('gstin'),
        'gst_category': gst_category,
        'links': [{
            'link_doctype': args.get('doctype'),
            'link_name': args.get('name')
        }]
    }).insert()

    return address

customer.make_address = make_address

def validate (self, method=None):
    if self.get('gstin_info'):
        self.gstin_info = json.loads(self.get('gstin_info'))
        self.gstin_info_updated_on = now_datetime()
        self.ctb = self.gstin_info.get('ctb')
        self.sts = self.gstin_info.get('sts')
        self.gstin_info = json.dumps(self.get('gstin_info'))
    
    if self.get('gstin') and (self.get('gstin') != 'URP' or self.get('gstin') != 'NA'):
        pan = self.get('gstin')[2:13]
        if PAN_NUMBER_FORMAT.match(pan):
            self.pan = pan