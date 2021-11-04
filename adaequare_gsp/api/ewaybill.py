import json
import frappe
from datetime import datetime
from frappe.utils import today, random_string
from erpnext.regional.india.utils import get_ewb_data, validate_state_code
from frappe.utils.data import DATE_FORMAT
from adaequare_gsp.api.get_gstin_details import validate_gstin
from adaequare_gsp.helpers.gstn_ewb_api import GstnEwbApi

DATE_FORMAT = "%d/%m/%Y %I:%M:%S %p"


def get_ewaybill_data(dt, dn):
    data = get_ewb_data(dt, [dn])
    data = data["billLists"][0]

    # sandbox data
    settings = frappe.get_single("Adaequare Settings")
    if settings.sandbox:
        data.update(
            {
                "userGstin": "05AAACG2115R1ZN",
                "fromGstin": "05AAACG2115R1ZN",
                "toGstin": "05AAACG2140A1ZL",
                "docNo": random_string(6),
            }
        )

    # different attributes for adaequare json
    data.update(
        {
            "transactionType": data.transType,
            "actFromStateCode": data.actualFromStateCode,
            "actToStateCode": data.actualToStateCode,
        }
    )
    validate_state_tax(data)
    return data


def update_invoice(dt, dn, dia):
    transporter_name = (
        frappe.db.get_value("Supplier", dia.get("transporter"), "supplier_name")
        if dia.get("transporter")
        else None
    )
    if dia.get("gst_transporter_id") and not validate_gstin(
        dia.get("gst_transporter_id")
    ):
        dia.gst_transporter_id = ""
    frappe.db.set_value(
        dt,
        dn,
        {
            "transporter": dia.get("transporter"),
            "transporter_name": transporter_name,
            "gst_transporter_id": dia.get("gst_transporter_id"),
            "vehicle_no": dia.get("vehicle_no"),
            "distance": dia.get("distance"),
            "lr_no": dia.get("lr_no"),
            "lr_date": dia.get("lr_date"),
            "mode_of_transport": dia.get("mode_of_transport"),
            "gst_vehicle_type": dia.get("gst_vehicle_type"),
            "gst_category": dia.get("gst_category"),
            "export_type": dia.get("export_type"),
        },
    )
    frappe.db.commit()


def validate_invoice_for_ewaybill(doc, method=None):
    if doc.get("posting_date") > today():
        frappe.throw("Invoice date cannot be a future date.")

    if doc.get("lr_date") and doc.get("lr_date") < doc.get("posting_date"):
        doc.lr_date = doc.posting_date

    if doc.get("distance") and doc.get("distance") > 4000:
        doc.distance = 4000


def validate_state_tax(data):
    if data.get("fromStateCode") == data.get("toStateCode"):
        attribute = ["igstValue", "igstRate"]
        supply = "intra-state"
    else:
        attribute = ["cgstValue", "sgstValue", "cgstRate", "sgstRate"]
        supply = "inter-state"

    for attr in attribute:
        if data.get(attr) == 0 or data.get("itemList")[0].get(attr) == 0:
            continue
        frappe.throw(
            "Please check the GST Accounts. {} should be zero for {} transaction.".format(
                attr, supply
            )
        )


@frappe.whitelist()
def generate_ewaybill(dt, dn, dia):
    dia = json.loads(dia)
    update_invoice(dt, dn, dia)
    data = get_ewaybill_data(dt, dn)

    api = GstnEwbApi()
    result = api.generate_ewaybill(data)

    def log_ewaybill():
        frappe.db.set_value(
            dt,
            dn,
            {
                "ewaybill": result.get("ewayBillNo"),
                "eway_bill_validity": result.get("validUpto"),
            },
        )
        log = frappe.get_doc(
            {
                "doctype": "Ewaybill Log",
                "ewaybill": result.get("ewayBillNo"),
                "ewaybill_date": datetime.strptime(
                    result.get("ewayBillDate"), DATE_FORMAT
                ),
                "valid_upto": datetime.strptime(result.get("validUpto"), DATE_FORMAT),
                "linked_with": dn,
                "result": json.dumps(result, indent=4),
            }
        )
        log.insert()

    log_ewaybill()
    return result.alert


# print ewaybill
# validations for cancel of invoice


@frappe.whitelist()
def cancel_ewaybill(dt, dn, dia):
    dia = json.loads(dia)
    data = {
        "ewbNo": dia.get("ewaybill"),
        "cancelRsnCode": dia.get("reason").split("-")[0],
        "cancelRmrk": dia.get("remark"),
    }
    api = GstnEwbApi()
    result = api.cancel_ewaybill(data)

    def log_ewaybill():
        frappe.db.set_value(
            dt,
            dn,
            {
                "ewaybill": None,
                "eway_bill_validity": None,
            },
        )
        frappe.db.set_value(
            "Ewaybill Log",
            dia.get("ewaybill"),
            {
                "is_cancelled": 1,
                "cancel_reason_code": dia.get("reason"),
                "cancel_remark": dia.get("remark"),
                "cancel_date": datetime.strptime(result.get("cancelDate"), DATE_FORMAT),
                "cancel_result": json.dumps(result, indent=4),
            },
        )

    log_ewaybill()


@frappe.whitelist()
def update_vehicle_info(dt, dn, dia):
    dia = json.loads(dia)

    transport_modes = {"Road": 1, "Rail": 2, "Air": 3, "Ship": 4}
    vehicle_types = {"Regular": "R", "Over Dimensional Cargo (ODC)": "O"}

    inv_doc = frappe.get_doc(dt, dn)
    dispatch_address = (
        inv_doc.dispatch_address_name
        if inv_doc.dispatch_address_name
        else inv_doc.company_address
    )
    dispatch_address = frappe.get_doc("Address", dispatch_address)

    data = {
        "ewbNo": dia.get("ewaybill"),
        "vehicleNo": dia.get("vehicle_no").replace(" ", ""),
        "fromPlace": dispatch_address.city,
        "fromState": validate_state_code(
            dispatch_address.gst_state_number, "Dispatch Address"
        ),
        "reasonCode": dia.get("reason").split("-")[0],
        "reasonRem": dia.get("remark"),
        "transDocNo": dia.get("lr_no"),
        "transDocDate": frappe.utils.formatdate(dia.get("lr_date"), "dd/mm/yyyy"),
        "transMode": transport_modes.get(dia.get("mode_of_transport")),
        "vehicleType": vehicle_types.get(dia.get("gst_vehicle_type")),
    }

    api = GstnEwbApi()
    result = api.update_vehicle_info(data)

    def log_ewaybill():
        frappe.db.set_value(
            dt,
            dn,
            {
                "eway_bill_validity": result.get("validUpto"),
                "vehicle_no": dia.get("vehicle_no").replace(" ", ""),
                "lr_no": dia.get("lr_no"),
                "lr_date": dia.get("lr_date"),
                "mode_of_transport": dia.get("mode_of_transport"),
                "gst_vehicle_type": dia.get("gst_vehicle_type"),
            },
        )
        frappe.db.set_value(
            "Ewaybill Log",
            dia.get("ewaybill"),
            {
                "vehicle_no": data.get("vehicleNo"),
                "from_place": data.get("fromPlace"),
                "from_state": data.get("fromState"),
                "vech_reason": dia.get("reason"),
                "vech_remark": dia.get("remark"),
                "lr_no": dia.get("lr_no"),
                "lr_date": dia.get("lr_date"),
                "valid_upto": datetime.strptime(result.get("validUpto"), DATE_FORMAT),
                "vech_date": datetime.strptime(result.get("vehUpdDate"), DATE_FORMAT),
                "vech_result": json.dumps(result, indent=4),
            },
        )

    log_ewaybill()


@frappe.whitelist()
def update_transporter(dt, dn, dia):
    dia = json.loads(dia)
    data = {
        "ewbNo": dia.get("ewaybill"),
        "transporterId": dia.get("gst_transporter_id"),
    }
    api = GstnEwbApi()
    result = api.update_transporter(data)

    def log_ewaybill():
        transporter_name = (
            frappe.db.get_value("Supplier", dia.get("transporter"), "supplier_name")
            if dia.get("transporter")
            else None
        )
        frappe.db.set_value(
            dt,
            dn,
            {
                "transporter": dia.get("transporter"),
                "transporter_name": transporter_name,
                "gst_transporter_id": dia.get("gst_transporter_id"),
            },
        )
        frappe.db.set_value(
            "Ewaybill Log",
            dia.get("ewaybill"),
            {
                "gst_transporter_id": result.get("transporterId"),
                "trans_update_date": datetime.strptime(
                    result.get("transUpdateDate"), DATE_FORMAT
                ),
                "trans_result": json.dumps(result, indent=4),
            },
        )

    log_ewaybill()


# Update Print Format

# extend validity
# check if not cancelled
# create dialog
# extend ewaybill validity
# update invoice
# update log

# Pending Things
# - Download Ewaybill data and generate print format
# - Extend ewaybill validity
# - Save QR text in log
# - for sales return and purchase return

# - Validate GST account / tax rates / with states / reverse charge.
# - Add Round-off to Other Value - Pull Request
# - Add Bill-From and Ship from along with Both, based on Dispatch Address
# additional validations in erpnext PR
