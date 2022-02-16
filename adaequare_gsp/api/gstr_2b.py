import json
import frappe
import urllib
from datetime import datetime
from adaequare_gsp.helpers.gstn_returns_api import Gstr2bApi
from adaequare_gsp.helpers.schema.gstr_2b import (
    DATA_2B,
    MODIFY_DATA_2B,
    MODIFY_SUP_DETAIL,
    CLASS_MAP,
    FILE_FORMATS
)


@frappe.whitelist()
def get_gstr_2b(gstin, ret_periods, otp=None):
    gst_return = "GSTR 2B"
    if type(ret_periods) != list:
        ret_periods = json.loads(ret_periods)

    for ret_period in ret_periods:
        api = Gstr2bApi(gstin)
        response = api.get_gstr_2b(ret_period, otp)

        if api.otp_required(response):
            return response
        elif api.no_docs_found(response):
            api.create_or_update_download_log(
                gst_return, "", ret_period, no_data_found=1
            )
        else:
            validate_response(response, gstin, ret_period)
            api.create_or_update_download_log(gst_return, "", ret_period)
            create_or_update_transaction(response, [gstin, api.company], ret_period)
    return "Success"

@frappe.whitelist()
def upload_gstr_2b(gstin, period, attach_file):
    gstr_2b_json = get_json_from_url(attach_file)
    
    api = Gstr2bApi(gstin)
    validate_response(gstr_2b_json, gstin, period)
    api.create_or_update_download_log("GSTR 2B", "", period)
    create_or_update_transaction(gstr_2b_json, [gstin, api.company], period, now=False)
    return "Success"

@frappe.whitelist()
def get_uploaded_gstr_ret_period(attach_file):
    if attach_file:
        gstr_2b_json = get_json_from_url(attach_file) 
        ret_period = gstr_2b_json.get('data').get('rtnprd')
        return ret_period

def get_json_from_url(attach_file):
    json_url = frappe.utils.get_url(attach_file)
    file = urllib.request.urlopen(json_url)
    read_file = file.read()
    gstr_2b_json = json.loads(read_file)
    return gstr_2b_json

@frappe.whitelist()
def validate_file_format(attach_file):
    if attach_file:
        file = frappe.get_doc("File", {'file_url': attach_file})
        extension = file.get_extension()[1].lstrip('.')
        if extension not in FILE_FORMATS:
            frappe.delete_doc(file.name)
            frappe.throw(
                "Please upload a Json File",
                title="Invalid File Format",
            )

def validate_response(response, gstin, ret_period):
    if (
        response.get("data").get("gstin") != gstin
        or response.get("data").get("rtnprd") != ret_period
    ):
        frappe.throw(
            "Data received seems to be invalid from the GST Portal. Please try again or raise support ticket.",
            title="Invalid Response Received.",
        )


def create_or_update_transaction(response, company_info, ret_period, now=False):
    modify_dict(response.get("data"), MODIFY_DATA_2B)
    for subtyp in CLASS_MAP:
        frappe.enqueue(
            create_or_update_b2b,
            now=now,
            enqueue_after_commit=True,
            response=response,
            company_info=company_info,
            classification=subtyp,
        )
        frappe.enqueue(
            update_download_history,
            now=now,
            enqueue_after_commit=True,
            ret_period=ret_period,
        )


def create_or_update_b2b(response, company_info, classification):
    doctype = "Inward Supply"
    typ, items, class_field, modify_class_field, sup_field, item_field = CLASS_MAP[
        classification
    ]
    b2b_data = response.get("data").get("docdata").get(classification.lower())
    if not b2b_data:
        return
    if not b2b_data[0].get(typ):
        b2b_data = [{typ: b2b_data}]
    for sup_dict in b2b_data:
        modify_dict(sup_dict, MODIFY_SUP_DETAIL)
        for inv_dict in sup_dict.get(typ):
            field_data_map = (
                (DATA_2B, response.data),
                (sup_field, sup_dict),
                (class_field, inv_dict),
            )
            modify_dict(inv_dict, modify_class_field)
            trans = transaction_exists(
                sup_dict, sup_field, class_field, inv_dict, classification
            )

            doc = frappe.get_doc(doctype, trans) if trans else frappe.new_doc(doctype)
            update_doc(
                doc,
                field_data_map,
                item_field,
                company_info,
                items,
                classification,
                inv_dict,
            )
            doc.save(ignore_permissions=True)


def update_doc(
    doc,
    field_data_map,
    item_field,
    company_info,
    items,
    classification,
    inv_dict,
    itm_det=None,
):
    for field_map in field_data_map:
        if field_map[0]:
            doc.update(get_mapped_dict(doc, field_map[0], field_map[1]))

    if not items:
        doc.update({"items": [get_mapped_dict(doc, item_field, inv_dict)]})
    else:
        doc.update(
            {
                "items": [
                    get_mapped_dict(doc, item_field, item_dict, itm_det)
                    for item_dict in inv_dict.get(items)
                ]
            }
        )
    if classification[-1] == "A":
        doc.is_amended = 1
    if doc.gstr_1_filing_date:
        doc.gstr_1_filled = 1
    doc.classification = classification
    doc.company_gstin, doc.company = company_info


def get_mapped_dict(doc, field_map, data_dict, itm_det=False):
    if itm_det:
        return {
            field: data_dict.get("itm_det").get(field_map[field])
            or data_dict.get(field_map[field])
            or doc.get(field)
            for field in field_map
        }
    else:
        return {
            field: data_dict.get(field_map[field]) or doc.get(field)
            for field in field_map
        }


def modify_dict(inv, modify_dict):
    for detail in modify_dict:
        if type(modify_dict[detail]) == dict:
            inv[detail] = modify_dict[detail].get(inv.get(detail))
        elif not inv.get(detail):
            continue
        elif callable(modify_dict[detail]):
            inv[detail] = modify_dict[detail](inv.get(detail))
        elif "%" in modify_dict[detail]:
            if not isinstance(inv.get(detail), datetime):
                inv[detail] = datetime.strptime(inv.get(detail), modify_dict[detail])
            else:
                inv[detail] = inv.get(detail)


def transaction_exists(sup_dict, sup_detail, b2b_dict, inv_dict, classification):
    filters = {
        "supplier_gstin": sup_dict.get(sup_detail.get("supplier_gstin"))
        or inv_dict.get(b2b_dict.get("supplier_gstin"), ""),
        "doc_date": inv_dict.get(b2b_dict.get("doc_date")),
        "doc_number": inv_dict.get(b2b_dict.get("doc_number")),
        "classification": classification,
    }
    if not sup_dict.get(sup_detail.get("supplier_gstin")) and not inv_dict.get(
        b2b_dict.get("supplier_gstin")
    ):
        filters.pop("supplier_gstin")

    name = frappe.db.get_value(
        "Inward Supply",
        filters,
        fieldname="name",
    )
    return name


def update_download_history(ret_period):
    # update 2A data availability from 2B download
    dt = frappe.qb.DocType("Inward Supply")
    docs = (
        frappe.qb.from_(dt)
        .select("sup_return_period", "classification")
        .where(dt.return_period_2b == ret_period)
        .groupby("sup_return_period", "classification")
        .run(as_dict=True)
    )
    if not docs:
        return

    dt_log = frappe.qb.DocType("GSTR Download Log")
    for doc in docs:
        logs = (
            frappe.qb.from_(dt_log)
            .select("name")
            .where(dt_log.return_period == doc.get("sup_return_period"))
            .where(dt_log.classification == doc.get("classification"))
            .where(dt_log.no_data_found == 1)
            .run(as_list=True)
        )
        for log in logs:
            doc = frappe.get_doc("GSTR Download Log", log[0])
            doc.no_data_found = 0
            doc.save(ignore_permissions=True)
