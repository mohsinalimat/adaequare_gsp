import frappe
from datetime import datetime
from adaequare_gsp.helpers.schema.states import number_state_mapping
from adaequare_gsp.helpers.schema.gstr_2b import (
    GST_CATEGORY,
    NOTE_TYPE,
    YES_NO,
)


def update_period(date):
    date = datetime.strptime(date, "%b-%y").strftime("%m%Y")
    return date


DATE_FORMAT = "%d-%m-%Y"
DATE_FORMAT2 = "%d-%b-%y"
AMEND_TYPE = {
    "R": "Receiver GSTIN Amended",
    "N": "Invoice Number Amended",
    "D": "Other Details Amended",
}
ISD_TYPE = {"ISDCN": "ISD Credit Note", "ISD": "ISD Invoice"}

SUP_DETAIL = {
    "supplier_gstin": "ctin",
    "gstr_1_filing_date": "fldtr1",
    "sup_return_period": "flprdr1",
    "gstr_1_filled": "cfs",
    "gstr_3b_filled": "cfs3b",
    "registration_cancel_date": "dtcancel",
}

MODIFY_SUP_DETAIL = {
    "fldtr1": DATE_FORMAT2,
    "dtcancel": DATE_FORMAT2,
    "cfs": YES_NO,
    "cfs3b": YES_NO,
    "flprdr1": update_period,
}

B2B = frappe._dict(
    {
        "doc_number": "inum",
        "supply_type": "inv_typ",
        "doc_date": "idt",
        "document_value": "val",
        "place_of_supply": "pos",
        "other_return_period": "aspd",
        "amendment_type": "atyp",
        "reverse_charge": "rchrg",
        "diffprcnt": "diff_percent",
        "irn_source": "srctyp",
        "irn_number": "irn",
        "irn_gen_date": "irngendate",
        "doc_type": "doc_type",  # Custom Field
    }
)

MODIFY_B2B = frappe._dict(
    {
        "inv_typ": GST_CATEGORY,
        "pos": number_state_mapping,
        "rchrg": YES_NO,
        "aspd": update_period,
        "atyp": AMEND_TYPE,
        "diff_percent": {1: 1, 0.65: 0.65, None: 1},
        "idt": DATE_FORMAT,
        "irngendate": DATE_FORMAT,
        "doc_type": {None: "Invoice"},
    }
)

ITEM = {
    "item_number": "num",
    "rate": "rt",
    "taxable_value": "txval",
    "igst": "iamt",
    "cgst": "camt",
    "sgst": "samt",
    "cess": "csamt",
}

B2BA = frappe._dict(B2B).update(
    {"original_doc_number": "oinum", "original_doc_date": "oidt"}
)
MODIFY_B2BA = frappe._dict(MODIFY_B2B).update({"oidt": DATE_FORMAT})

CDN = frappe._dict(B2B).update(
    {"doc_number": "nt_num", "doc_date": "nt_dt", "doc_type": "ntty"}
)

MODIFY_CDN = frappe._dict(MODIFY_B2B).update(
    {"doc_type": None, "ntty": NOTE_TYPE, "nt_dt": DATE_FORMAT}
)

CDNA = frappe._dict(CDN).update(
    {
        "original_doc_number": "ont_num",
        "original_doc_date": "ont_dt",
        "original_doc_type": "ntty",
    }
)
MODIFY_CDNA = frappe._dict(MODIFY_CDN).update({"ont_dt": DATE_FORMAT})

ISD = frappe._dict(
    {
        "doc_type": "isd_docty",
        "doc_number": "docnum",
        "doc_date": "docdt",
        "itc_availability": "itc_elg",
        "other_return_period": "aspd",
        "amendment_type": "atyp",
    }
)

MODIFY_ISD = frappe._dict(
    {
        "itc_elg": {"Y": "Yes", "N": "No"},
        "isd_docty": ISD_TYPE,
        "docdt": DATE_FORMAT,
        "aspd": update_period,
        "atyp": AMEND_TYPE,
    }
)

ITEM_ISD = frappe._dict(ITEM).update({"cess": "cess"})

IMPG = frappe._dict(
    {
        "doc_type": "doc_type",  # custom field
        "doc_number": "benum",
        "doc_date": "bedt",
        "is_amended": "amd",
        "port_code": "portcd",
    }
)
MODIFY_IMPG = frappe._dict(
    {
        "doc_type": {None: "Bill of Entry"},
        "bedt": DATE_FORMAT,
        "amd": YES_NO,
    }
)

IMPGSEZ = frappe._dict(IMPG).update(
    {
        "supplier_gstin": "sgstin",
        "supplier_name": "tdname",
    }
)


ACTIONS = ["B2B", "B2BA", "CDN", "CDNA", "ISD", "ISDA", "IMPG", "IMPGSEZ"]
# TODO: ISD and IMPG should be a part of configuration. Only if user deals in such transactions should it be imported.
#        eg: If company or user deals in SEZ imports, only them should IMPGSEZ whould be called.

CLASS_MAP = {
    "B2B": ["inv", "itms", "B2B", B2B, MODIFY_B2B, SUP_DETAIL, ITEM],
    "B2BA": ["inv", "itms", "B2BA", B2BA, MODIFY_B2BA, SUP_DETAIL, ITEM],
    "CDN": ["nt", "itms", "CDNR", CDN, MODIFY_CDN, SUP_DETAIL, ITEM],
    "CDNA": ["nt", "itms", "CDNRA", CDNA, MODIFY_CDNA, SUP_DETAIL, ITEM],
    "ISD": ["doclist", "", "ISD", ISD, MODIFY_ISD, SUP_DETAIL, ITEM_ISD],
    "IMPG": ["boe", "", "IMPG", IMPG, MODIFY_IMPG, {}, ITEM],
    "IMPGSEZ": ["boe", "", "IMPGSEZ", IMPGSEZ, MODIFY_IMPG, {}, ITEM],
}
