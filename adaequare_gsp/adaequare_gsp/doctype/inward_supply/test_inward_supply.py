# Copyright (c) 2022, Resilient Tech and Contributors
# See license.txt

import frappe
import unittest
from datetime import datetime
from adaequare_gsp.api.gstr_2b import create_or_update_transaction, DATE_FORMAT


class TestInwardSupply(unittest.TestCase):
    gstin = "01AABCE2207R1Z5"
    company = ""
    doctype = "Inward Supply"

    def test_aaa(self):
        create_or_update_transaction(frappe._dict(GSTR_2B), self.company, now=True)

    def test_gstr_2b_b2b(self):
        name = frappe.db.get_value(
            self.doctype, filters={"classification": "B2B"}, fieldname="name"
        )
        doc = frappe.get_doc(self.doctype, name)
        out = {
            "company_gstin": "01AABCE2207R1Z5",
            "2b_return_period": "032020",
            "2b_gen_date": datetime.strptime("14-04-2020", DATE_FORMAT).date(),
            "supplier_gstin": "01AABCE2207R1Z5",
            "supplier_name": "GSTN",
            "gstr_1_filing_date": datetime.strptime("18-11-2019", DATE_FORMAT).date(),
            "sup_return_period": "112019",
            "doc_number": "S008400",
            "supply_type": "Regular",
            "doc_date": datetime.strptime("24-11-2016", DATE_FORMAT).date(),
            "document_value": 729248.16,
            "place_of_supply": "06-Haryana",
            "reverse_charge": 0,
            "itc_availability": "No",
            "reason_itc_unavailability": "POS and supplier state are same but recipient state is different",
            "diffprcnt": "1",
            "irn_source": "e-Invoice",
            "irn_number": "897ADG56RTY78956HYUG90BNHHIJK453GFTD99845672FDHHHSHGFH4567FG56TR",
            "irn_gen_date": datetime.strptime("24-12-2019", DATE_FORMAT).date(),
            "doc_type": "Invoice",
        }
        out_item = {
            "item_number": 1,
            "rate": 5,
            "taxable_value": 400,
            "igst": 0,
            "cgst": 200,
            "sgst": 200,
            "cess": 0,
        }
        for k in out:
            self.assertEqual(doc.get(k), out.get(k))

        for k in out_item:
            self.assertEqual(doc.items[0].get(k), out_item.get(k))

    def test_gstr_2b_impg(self):
        name = frappe.db.get_value(
            self.doctype, filters={"classification": "IMPG"}, fieldname="name"
        )
        doc = frappe.get_doc(self.doctype, name)
        out = {
            "doc_type": "Bill of Entry",
            "port_code": "18272A",
            "doc_number": "2566282",
            "doc_date": datetime.strptime("18-11-2019", DATE_FORMAT).date(),
            "is_amended": 0,
        }
        out_item = {
            "taxable_value": 123.02,
            "igst": 123.02,
            "cess": 0.5,
        }
        for k in out:
            self.assertEqual(doc.get(k), out.get(k))

        for k in out_item:
            self.assertEqual(doc.items[0].get(k), out_item.get(k))

    def test_gstr_2b_impgsez(self):
        name = frappe.db.get_value(
            self.doctype, filters={"classification": "IMPGSEZ"}, fieldname="name"
        )
        doc = frappe.get_doc(self.doctype, name)
        out = {
            "supplier_gstin": "01AABCE2207R1Z5",
            "supplier_name": "GSTN",
            "doc_type": "Bill of Entry",
            "port_code": "18272A",
            "doc_number": "2566282",
            "doc_date": datetime.strptime("18-11-2019", DATE_FORMAT).date(),
            "is_amended": 0,
        }
        out_item = {
            "taxable_value": 123.02,
            "igst": 123.02,
            "cess": 0.5,
        }
        for k in out:
            self.assertEqual(doc.get(k), out.get(k))

        for k in out_item:
            self.assertEqual(doc.items[0].get(k), out_item.get(k))

    def test_gstr_2b_isda(self):
        name = frappe.db.get_value(
            self.doctype, filters={"classification": "ISDA"}, fieldname="name"
        )
        doc = frappe.get_doc(self.doctype, name)
        out = {
            "gstr_1_filing_date": datetime.strptime("02-03-2020", DATE_FORMAT).date(),
            "sup_return_period": "022020",
            "supplier_gstin": "16DEFPS8555D1Z7",
            "supplier_name": "GSTN",
            "original_doc_type": "ISD Credit Note",
            "original_doc_number": "1004",
            "original_doc_date": datetime.strptime("02-03-2016", DATE_FORMAT).date(),
            "doc_type": "ISD Invoice",
            "doc_number": "S0080",
            "doc_date": datetime.strptime("03-03-2016", DATE_FORMAT).date(),
            "itc_availability": "Yes",
        }
        out_item = {
            "igst": 0,
            "cgst": 200,
            "sgst": 200,
            "cess": 0,
        }
        for k in out:
            self.assertEqual(doc.get(k), out.get(k))

        for k in out_item:
            self.assertEqual(doc.items[0].get(k), out_item.get(k))

    def test_zzz(self):
        frappe.db.delete(self.doctype)


GSTR_2B = {
    "chksum": "ADFADRGA4GADFADGERER",
    "data": {
        "gstin": "01AABCE2207R1Z5",
        "rtnprd": "032020",
        "version": "1.0",
        "gendt": "14-04-2020",
        "itcsumm": {},
        "cpsumm": {},
        "docdata": {
            "b2b": [
                {
                    "ctin": "01AABCE2207R1Z5",
                    "trdnm": "GSTN",
                    "supfildt": "18-11-2019",
                    "supprd": "112019",
                    "inv": [
                        {
                            "inum": "S008400",
                            "typ": "R",
                            "dt": "24-11-2016",
                            "val": 729248.16,
                            "pos": "06",
                            "rev": "N",
                            "itcavl": "N",
                            "rsn": "P",
                            "diffprcnt": 1,
                            "srctyp": "e-Invoice",
                            "irn": "897ADG56RTY78956HYUG90BNHHIJK453GFTD99845672FDHHHSHGFH4567FG56TR",
                            "irngendate": "24-12-2019",
                            "items": [
                                {
                                    "num": 1,
                                    "rt": 5,
                                    "txval": 400,
                                    "igst": 0,
                                    "cgst": 200,
                                    "sgst": 200,
                                    "cess": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
            "b2ba": [
                {
                    "ctin": "01AABCE2207R1Z5",
                    "trdnm": "GSTN",
                    "supfildt": "18-11-2019",
                    "supprd": "112019",
                    "inv": [
                        {
                            "oinum": "S008400",
                            "oidt": "24-11-2016",
                            "inum": "S008400",
                            "typ": "R",
                            "dt": "24-11-2016",
                            "val": 729248.16,
                            "pos": "06",
                            "rev": "N",
                            "itcavl": "N",
                            "rsn": "P",
                            "diffprcnt": 1,
                            "items": [
                                {
                                    "num": 1,
                                    "rt": 5,
                                    "txval": 400,
                                    "igst": 0,
                                    "cgst": 200,
                                    "sgst": 200,
                                    "cess": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
            "cdnr": [
                {
                    "ctin": "01AAAAP1208Q1ZS",
                    "trdnm": "GSTN",
                    "supfildt": "18-11-2019",
                    "supprd": "112019",
                    "nt": [
                        {
                            "ntnum": "533515",
                            "typ": "C",
                            "suptyp": "R",
                            "dt": "23-09-2016",
                            "val": 729248.16,
                            "pos": "01",
                            "rev": "N",
                            "itcavl": "N",
                            "rsn": "C",
                            "diffprcnt": 1,
                            "srctyp": "e-Invoice",
                            "irn": "897ADG56RTY78956HYUG90BNHHIJK453GFTD99845672FDHHHSHGFH4567FG56TR",
                            "irngendate": "24-12-2019",
                            "items": [
                                {
                                    "num": 1,
                                    "rt": 5,
                                    "txval": 400,
                                    "igst": 400,
                                    "cgst": 0,
                                    "sgst": 0,
                                    "cess": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
            "cdnra": [
                {
                    "ctin": "01AAAAP1208Q1ZS",
                    "trdnm": "GSTN",
                    "supfildt": "18-11-2019",
                    "supprd": "112019",
                    "nt": [
                        {
                            "onttyp": "C",
                            "ontnum": "533515",
                            "ontdt": "23-09-2016",
                            "ntnum": "533515",
                            "typ": "C",
                            "suptyp": "R",
                            "dt": "23-09-2016",
                            "val": 729248.16,
                            "pos": "01",
                            "rev": "N",
                            "itcavl": "N",
                            "rsn": "C",
                            "diffprcnt": 1,
                            "items": [
                                {
                                    "num": 1,
                                    "rt": 5,
                                    "txval": 400,
                                    "igst": 0,
                                    "cgst": 200,
                                    "sgst": 200,
                                    "cess": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
            "isd": [
                {
                    "ctin": "16DEFPS8555D1Z7",
                    "trdnm": "GSTN",
                    "supprd": "022020",
                    "supfildt": "02-03-2020",
                    "doclist": [
                        {
                            "doctyp": "ISDI",
                            "docnum": "S0080",
                            "docdt": "03-03-2016",
                            "oinvnum": "P0079",
                            "oinvdt": "03-03-2016",
                            "igst": 0,
                            "cgst": 200,
                            "sgst": 200,
                            "cess": 0,
                            "itcelg": "Y",
                        }
                    ],
                }
            ],
            "isda": [
                {
                    "ctin": "16DEFPS8555D1Z7",
                    "trdnm": "GSTN",
                    "supprd": "022020",
                    "supfildt": "02-03-2020",
                    "doclist": [
                        {
                            "odoctyp": "ISDC",
                            "odocnum": "1004",
                            "odocdt": "02-03-2016",
                            "doctyp": "ISDI",
                            "docnum": "S0080",
                            "docdt": "03-03-2016",
                            "oinvnum": "P0079",
                            "oinvdt": "03-03-2016",
                            "igst": 0,
                            "cgst": 200,
                            "sgst": 200,
                            "cess": 0,
                            "itcelg": "Y",
                        }
                    ],
                }
            ],
            "impg": [
                {
                    "refdt": "28-11-2019",
                    "recdt": "30-11-2019",
                    "portcode": "18272A",
                    "boenum": "2566282",
                    "boedt": "18-11-2019",
                    "isamd": "N",
                    "txval": 123.02,
                    "igst": 123.02,
                    "cess": 0.5,
                }
            ],
            "impgsez": [
                {
                    "ctin": "01AABCE2207R1Z5",
                    "trdnm": "GSTN",
                    "boe": [
                        {
                            "refdt": "28-11-2019",
                            "recdt": "30-11-2019",
                            "portcode": "18272A",
                            "boenum": "2566282",
                            "boedt": "18-11-2019",
                            "isamd": "N",
                            "txval": 123.02,
                            "igst": 123.02,
                            "cess": 0.5,
                        }
                    ],
                }
            ],
        },
    },
}
