import json
import frappe
from frappe.utils import now
from datetime import datetime
from adaequare_gsp.helpers.gstn_returns_api import Gstr2bApi
from adaequare_gsp.helpers.schema.gstr_2b import (
    DATA_2B,
    MODIFY_DATA_2B,
    SUP_DETAIL,
    MODIFY_SUP_DETAIL,
    ITEM,
    B2B,
    MODIFY_B2B,
    B2BA,
    MODIFY_B2BA,
    CDNR,
    MODIFY_CDNR,
    CDNRA,
    MODIFY_CDNRA,
    ISD,
    MODIFY_ISD,
    ISDA,
    MODIFY_ISDA,
    IMPG,
    MODIFY_IMPG,
)

DATE_FORMAT = "%d-%m-%Y"


@frappe.whitelist()
def get_gstr_2b(gstin, ret_periods, otp=None):
    gst_return = "GSTR 2B"
    ret_periods = json.loads(ret_periods)
    for ret_period in ret_periods:
        api = Gstr2bApi(gstin)
        response = api.get_gstr_2b(ret_period, otp)

        if api.otp_required(response):
            return response
        elif api.no_docs_found(response):
            create_or_update_download_log(gstin, gst_return, "", ret_period)
            # TODO: Create further calls if more than one file to download
        else:
            validate_response(response, gstin, ret_period)
            create_or_update_download_log(gstin, gst_return, "", ret_period)
            create_or_update_transaction(response, api.company, now=False)


def validate_response(response, gstin, ret_period):
    if (
        response.get("data").get("gstin") != gstin
        or response.get("data").get("rtnprd") != ret_period
    ):
        frappe.throw(
            "Data received seems to be invalid from the GST Portal. Please try again or raise support ticket.",
            title="Invalid Response Received.",
        )


def create_or_update_download_log(gstin, gst_return, classification, return_period):
    doctype = "GSTR Download Log"
    name = frappe.db.get_value(
        doctype,
        {
            "gstin": gstin,
            "gst_return": gst_return,
            "classification": classification,
            "return_period": return_period,
        },
        fieldname="name",
    )
    if name:
        frappe.db.set_value(doctype, name, "last_updated_on", now())
    else:
        doc = frappe.get_doc(
            {
                "doctype": doctype,
                "gstin": gstin,
                "gst_return": gst_return,
                "classification": classification,
                "return_period": return_period,
            }
        )
        doc.last_updated_on = now()
        doc.save(ignore_permissions=True)


def create_or_update_transaction(response, gstin_info, now):
    docdata = response.get("data").get("docdata")
    modify_trans(response.get("data"), MODIFY_DATA_2B)
    subtyps = {
        "B2B": ["inv", B2B, MODIFY_B2B],
        "B2BA": ["inv", B2BA, MODIFY_B2BA],
        "CDNR": ["nt", CDNR, MODIFY_CDNR],
        "CDNRA": ["nt", CDNRA, MODIFY_CDNRA],
        "ISD": ["doclist", ISD, MODIFY_ISD],
        "ISDA": ["doclist", ISDA, MODIFY_ISDA],
        "IMPG": ["boe", IMPG, MODIFY_IMPG],
        "IMPGSEZ": ["boe", IMPG, MODIFY_IMPG],
    }

    for subtyp in subtyps:
        frappe.enqueue(
            create_or_update_b2b,
            now=now,
            enqueue_after_commit=True,
            response=response,
            gstin_info=gstin_info,
            classification=subtyp,
            class_details=subtyps[subtyp],
            docdata=docdata,
        )


def create_or_update_b2b(response, gstin_info, classification, class_details, docdata):
    doctype = "Inward Supply"
    typ, b2b, modify_b2b = class_details
    b2b_data = docdata.get(classification.lower())
    if not b2b_data:
        return
    if classification == "IMPG":
        b2b_data = [{typ: b2b_data}]
    for sup in b2b_data:
        modify_trans(sup, MODIFY_SUP_DETAIL)
        for inv in sup.get(typ):
            modify_trans(inv, modify_b2b)
            trans = transaction_exists(
                sup.get(SUP_DETAIL.get("supplier_gstin")),
                sup.get(SUP_DETAIL.get("sup_return_period"), ""),
                inv.get(b2b.get("doc_number")),
                classification,
            )

            doc = frappe.get_doc(doctype, trans) if trans else frappe.new_doc(doctype)
            doc.update({field: response.data[DATA_2B[field]] for field in DATA_2B})
            doc.update({field: sup.get(SUP_DETAIL[field]) for field in SUP_DETAIL})
            doc.update({field: inv.get(b2b[field]) for field in b2b})

            if "ISD" in classification or "IMPG" in classification:
                doc.update({"items": [{field: inv.get(ITEM[field]) for field in ITEM}]})
            else:
                doc.update(
                    {
                        "items": [
                            {field: item.get(ITEM[field]) for field in ITEM}
                            for item in inv.get("items")
                        ]
                    }
                )

            if classification[-1] == "A":
                doc.is_amended = 1
            if doc.gstr_1_filing_date:
                doc.gstr_1_filled = 1

            doc.classification = classification
            doc.company = gstin_info
            doc.save(ignore_permissions=True)


def modify_trans(inv, modify_dict):
    for detail in modify_dict:
        if modify_dict[detail] == "DATE" and inv.get(detail):
            inv[detail] = datetime.strptime(inv.get(detail), DATE_FORMAT)
        elif type(modify_dict[detail]) == dict:
            inv[detail] = modify_dict[detail].get(inv.get(detail))


def transaction_exists(supplier_gstin, sup_return_period, doc_number, classification):
    name = frappe.db.get_value(
        "Inward Supply",
        {
            "supplier_gstin": supplier_gstin,
            "sup_return_period": sup_return_period,
            "doc_number": doc_number,
            "classification": classification,
        },
        fieldname="name",
    )
    return name
