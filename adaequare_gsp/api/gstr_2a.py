import json
import frappe
from adaequare_gsp.api.gstr_2b import transaction_exists, modify_dict, update_doc
from adaequare_gsp.helpers.gstn_returns_api import Gstr2aApi
from adaequare_gsp.helpers.schema.gstr_2a import (
    ACTIONS,
    MODIFY_SUP_DETAIL,
    CLASS_MAP,
)


@frappe.whitelist()
def get_gstr_2a(gstin, ret_periods, otp=None):
    gst_return = "GSTR 2A"
    if type(ret_periods) != list:
        ret_periods = json.loads(ret_periods)

    for ret_period in ret_periods:
        api = Gstr2aApi(gstin)
        for act in ACTIONS:
            response = api.get_gstr_2a(act, ret_period, otp)
            classification = CLASS_MAP[act][2]
            if api.otp_required(response):
                return response
            elif api.no_docs_found(response):
                api.create_or_update_download_log(
                    gst_return, classification, ret_period, no_data_found=1
                )
            else:
                validate_response(response, act)
                api.create_or_update_download_log(
                    gst_return, classification, ret_period
                )
                create_or_update_transaction(
                    response, act, [gstin, api.company], now=True
                )
    return "Success"


def validate_response(response, action):
    if not response.get(action.lower()):
        frappe.throw(
            "Data received seems to be invalid from the GST Portal. Please try again or raise support ticket.",
            title="Invalid Response Received.",
        )


def create_or_update_transaction(response, action, company_info, now):
    frappe.enqueue(
        create_or_update_b2b,
        now=now,
        enqueue_after_commit=True,
        response=response,
        company_info=company_info,
        action=action,
    )


def create_or_update_b2b(response, company_info, action):
    doctype = "Inward Supply"
    (
        typ,
        items,
        classification,
        class_field,
        modify_class_field,
        sup_field,
        item_field,
    ) = CLASS_MAP[action]

    b2b_data = response.get(action.lower())
    if not b2b_data:
        return
    if not b2b_data[0].get(typ):
        b2b_data = [{typ: b2b_data}]
    for sup_dict in b2b_data:
        modify_dict(sup_dict, MODIFY_SUP_DETAIL)
        for inv_dict in sup_dict.get(typ):
            field_data_map = ((sup_field, sup_dict), (class_field, inv_dict))
            modify_dict(inv_dict, modify_class_field)
            trans = transaction_exists(
                sup_dict, sup_field, class_field, inv_dict, classification
            )
            # TODO Deal with cases where registration is cancelled.
            # TODO Update logs with few details to ensure that we do not download data in 2A where its not required.
            # Basis: GSTR1 Period of Supplier from 2B. Type of Transactions of Customer where there are no imports.
            doc = frappe.get_doc(doctype, trans) if trans else frappe.new_doc(doctype)
            update_doc(
                doc,
                field_data_map,
                item_field,
                company_info,
                items,
                classification,
                inv_dict,
                itm_det=True,
            )
            doc.save(ignore_permissions=True)
