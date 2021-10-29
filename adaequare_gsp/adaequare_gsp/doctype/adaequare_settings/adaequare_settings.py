# Copyright (c) 2021, Resilient Tech and contributors
# For license information, please see license.txt

# import frappe
import frappe
import json
from frappe.model.document import Document
from frappe.utils import now_datetime
from adaequare_gsp.helpers.gstn_public_api import GstnPublicApi
from adaequare_gsp.monkey_patches.create_party import gst_category_map

class AdaequareSettings(Document):
	pass

@frappe.whitelist()
def enqueue_bulk_update_party(make_urp):
	doctypes = ['Customer', 'Supplier']
	make_urp = int(make_urp)
	frappe.msgprint('Verify customers and suppliers after some time.', title='Bulk Update started')
	for dt in doctypes:
		parties = get_parties(dt)
		frappe.enqueue(update_party_gstin_details, make_urp=make_urp, dt=dt, parties=parties)

def update_party_gstin_details(make_urp, dt, parties):
	for p in parties:
		address = get_party_address(dt, p.name)
		if address:
			try:
				default_gstin = get_default_gstin(p, address)					
				update_party_and_address(dt, p, address, default_gstin, make_urp)
			except Exception as e:
				frappe.log_error('Could not update {} with name {}.\nTraceback:\n{}'.format(dt, p.name, e),
					title='Error while bulk update from Adaequare Settings')
				continue

def update_party_and_address(doctype, party, address, default_gstin, make_urp):
	gstin_list = []
	for addr in address:
		if addr.gstin not in gstin_list:
			gstin_list.append(addr.gstin)

	for gstin in gstin_list:
		if (not gstin or gstin == 'URP' or gstin == 'NA') and make_urp:
			gstin_info = {"dty": "URP", "gstin": "URP"}
		elif not make_urp and len(gstin) != 15:
			continue
		else:
			api = GstnPublicApi()
			gstin_info = api.get_gstin_info(gstin)

		update_address(address, gstin, gstin_info)
		if gstin == default_gstin:
			update_party(doctype, party, gstin_info)

def update_party(doctype, party, gstin_info):
	pan = party.pan
	if not pan and gstin_info.get("gstin") and len(gstin_info.get("gstin")) == 15:
		pan = gstin_info.get("gstin")[2:12]

	company_list = ["Public Limited Company", "Private Limited Company", "Unlimited Company"]
	party_type = "Company" if gstin_info.get("ctb") in company_list else "Individual"
	pt = "supplier_type" if doctype == "Supplier" else "customer_type"
				
	frappe.db.set_value(doctype, party.name, {
		'pan': pan,
		'gstin_info_updated_on': now_datetime(),
		'ctb': gstin_info.get("ctb"),
		'sts': gstin_info.get("sts"),
		'default_gstin': gstin_info.get("gstin"),
		'trade_name': gstin_info.get("tradeNam"),
		'gstin_info': json.dumps(gstin_info),
		pt: party_type 
	})
	if party.get("is_transporter"):
		frappe.db.set_value(doctype, party.name, {
			'gst_transporter_id': gstin_info.get("gstin"),
		})

def update_address(address, gstin, gstin_info):
	for addr in address:
		if addr.gstin != gstin: continue
		gst_category = gst_category_map[gstin_info.get("dty")]
		if gst_category == "Unregistered" and addr.country != "India":
			gst_category = "Overseas"
		
		frappe.db.set_value('Address', addr.name, {
			'gst_category': gst_category,
			'gstin': gstin_info.get("gstin")
		})

def get_party_address(dt, party):
	address = frappe.db.sql(""" 
		SELECT
			addr.name, addr.is_primary_address, addr.gstin, addr.country
		FROM
			`tabAddress` addr, `tabDynamic Link` dl
		WHERE
			dl.parent = addr.name and dl.link_doctype = %s and
			dl.link_name = %s and ifnull(addr.disabled, 0) = 0
		ORDER BY
			addr.is_primary_address
		""" %('%s', '%s'), (dt, party), as_dict=1)
	return address

def get_default_gstin(p, address):
	if p.pan:
		if p.default_gstin:
			default_gstin = p.default_gstin if p.default_gstin[2:12] == p.pan else None
		if not p.default_gstin or not default_gstin:
			for addr in address:
				default_gstin = addr.gstin if addr.gstin[2:12] == p.pan else None
				if default_gstin: break
	else:
		default_gstin = address[0].gstin
	return default_gstin

def get_parties(dt, filters=None):
	if dt == "Supplier":
		parties = frappe.db.get_all(dt, fields=['name', 'default_gstin', 'pan', 'is_transporter'], filters=filters)
	else:
		parties = frappe.db.get_all(dt, fields=['name', 'default_gstin', 'pan'], filters=filters)
	return parties