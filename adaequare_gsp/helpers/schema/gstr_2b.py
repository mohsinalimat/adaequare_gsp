import frappe
from adaequare_gsp.helpers.schema.states import number_state_mapping

DATE_FORMAT = "%d-%m-%Y"
GST_CATEGORY = {
    "R": "Regular",
    "SEZWP": "SEZ supplies with payment of tax",
    "SEZWOP": "SEZ supplies with out payment of tax",
    "DE": "Deemed exports",
    "CBW": "Intra-State Supplies attracting IGST",
}
NOTE_TYPE = {"C": "Credit Note", "D": "Debit Note"}
ISD_TYPE = {"ISDC": "ISD Credit Note", "ISDI": "ISD Invoice"}
YES_NO = {"Y": 1, "N": 0}

DATA_2B = {
    "company_gstin": "gstin",
    "2b_return_period": "rtnprd",
    "2b_gen_date": "gendt",
}

MODIFY_DATA_2B = {
    "gendt": DATE_FORMAT,
}

SUP_DETAIL = {
    "supplier_gstin": "ctin",
    "supplier_name": "trdnm",
    "gstr_1_filing_date": "supfildt",
    "sup_return_period": "supprd",
}

MODIFY_SUP_DETAIL = {
    "supfildt": DATE_FORMAT,
}

B2B = frappe._dict(
    {
        "doc_number": "inum",
        "supply_type": "typ",
        "doc_date": "dt",
        "document_value": "val",
        "place_of_supply": "pos",
        "reverse_charge": "rev",
        "itc_availability": "itcavl",
        "reason_itc_unavailability": "rsn",
        "diffprcnt": "diffprcnt",
        "irn_source": "srctyp",
        "irn_number": "irn",
        "irn_gen_date": "irngendate",
        "doc_type": "doc_type",  # Custom Field
    }
)

MODIFY_B2B = frappe._dict(
    {
        "typ": GST_CATEGORY,
        "pos": number_state_mapping,
        "rev": YES_NO,
        "itcavl": {"Y": "Yes", "N": "No", "T": "Temporary"},
        "rsn": {
            "P": "POS and supplier state are same but recipient state is different",
            "C": "Return filed post annual cut-off",
        },
        "diffprcnt": {1: 1, 0.65: 0.65, None: 1},
        "dt": DATE_FORMAT,
        "irngendate": DATE_FORMAT,
        "doc_type": {None: "Invoice"},
    }
)

ITEM = {
    "item_number": "num",
    "rate": "rt",
    "taxable_value": "txval",
    "igst": "igst",
    "cgst": "cgst",
    "sgst": "sgst",
    "cess": "cess",
}

B2BA = frappe._dict(B2B).update(
    {"original_doc_number": "oinum", "original_doc_date": "oidt"}
)
MODIFY_B2BA = frappe._dict(MODIFY_B2B).update({"oidt": DATE_FORMAT})

CDNR = frappe._dict(B2B).update(
    {"doc_number": "ntnum", "doc_type": "typ", "supply_type": "suptyp"}
)
MODIFY_CDNR = frappe._dict(MODIFY_B2B).update(
    {
        "doc_type": None,
        "typ": NOTE_TYPE,
        "suptyp": GST_CATEGORY,
    }
)

CDNRA = frappe._dict(CDNR).update(
    {
        "original_doc_number": "ontnum",
        "original_doc_date": "ontdt",
        "original_doc_type": "onttyp",
    }
)
MODIFY_CDNRA = frappe._dict(MODIFY_CDNR).update(
    {"ontdt": DATE_FORMAT, "onttyp": NOTE_TYPE}
)

ISD = frappe._dict(
    {
        "doc_type": "doctyp",
        "doc_number": "docnum",
        "doc_date": "docdt",
        "itc_availability": "itcelg",
    }
)

MODIFY_ISD = frappe._dict(
    {
        "itcelg": {"Y": "Yes", "N": "No"},
        "doctyp": ISD_TYPE,
        "docdt": DATE_FORMAT,
    }
)

ISDA = frappe._dict(ISD).update(
    {
        "original_doc_type": "odoctyp",
        "original_doc_number": "odocnum",
        "original_doc_date": "odocdt",
    }
)
MODIFY_ISDA = frappe._dict(MODIFY_ISD).update(
    {"odoctyp": ISD_TYPE, "odocdt": DATE_FORMAT}
)

IMPG = frappe._dict(
    {
        "doc_type": "doc_type",  # custom field
        "doc_number": "boenum",
        "doc_date": "boedt",
        "is_amended": "isamd",
        "port_code": "portcode",
    }
)
MODIFY_IMPG = frappe._dict(
    {
        "doc_type": {None: "Bill of Entry"},
        "boedt": DATE_FORMAT,
        "isamd": YES_NO,
    }
)


CLASS_MAP = (
    {  # within each class 1. inv_list 2. item_list 3. invoice_field_map 4. modification
        "B2B": ["inv", "items", B2B, MODIFY_B2B, SUP_DETAIL, ITEM],
        "B2BA": ["inv", "items", B2BA, MODIFY_B2BA, SUP_DETAIL, ITEM],
        "CDNR": ["nt", "items", CDNR, MODIFY_CDNR, SUP_DETAIL, ITEM],
        "CDNRA": ["nt", "items", CDNRA, MODIFY_CDNRA, SUP_DETAIL, ITEM],
        "ISD": ["doclist", "", ISD, MODIFY_ISD, SUP_DETAIL, ITEM],
        "ISDA": ["doclist", "", ISDA, MODIFY_ISDA, SUP_DETAIL, ITEM],
        "IMPG": ["boe", "", IMPG, MODIFY_IMPG, {}, ITEM],
        "IMPGSEZ": ["boe", "", IMPG, MODIFY_IMPG, SUP_DETAIL, ITEM],
    }
)
