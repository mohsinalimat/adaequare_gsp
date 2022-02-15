import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from erpnext.selling.doctype.customer import customer
from erpnext.regional.india.utils import PAN_NUMBER_FORMAT

custom_make_address = customer.make_address

gst_category_map = {
    "Regular": "Registered Regular",
    "Input Service Distributor (ISD)": "Registered Regular",
    "Composition": "Registered Composition",
    "Tax Deductor": "Tax Deductor",
    "SEZ Unit": "SEZ",
    "SEZ Developer": "SEZ",
    "United Nation Body": "UIN Holders",
    "Consulate or Embassy of Foreign Country": "UIN Holders",
    "URP": "Unregistered",
}
# ####### SAMPLE DATA ########
# "Composition" - 36AASFP8573D2ZN
# "Input Service Distributor (ISD)" - 29AABCF8078M2ZW - Flipkart
# "Tax Deductor" - 06DELI09652G1DA, 09ALDN00287A1DD, 27AAFT56212B1DO, 19AAACI1681G1DV
# "SEZ Developer" - 27AAJCS5738D1Z6 -
# "United Nation Body" - 0717UNO00157UNO, 0717UNO00211UN2, 2117UNO00002UNF
# "Consulate or Embassy of Foreign Country" - 0717UNO00154UNU

# "Tax Collector (Electronic Commerce Operator)" - 29AABCF8078M1C8, 27AAECG3736E1C2 - Cannot be a part of GSTR1
# "Non Resident Online Services Provider" - 9917SGP29001OST - Google - Cannot be a part of GSTR1

# "Non Resident Taxable Person" -
# "Government Department ID" -


def make_address(args, is_primary_address=1):
    reqd_fields = []
    for field in ["city", "country"]:
        if not args.get(field):
            reqd_fields.append("<li>" + field.title() + "</li>")

    if reqd_fields:
        msg = _("Following fields are mandatory to create address:")
        frappe.throw(
            "{0} <br><br> <ul>{1}</ul>".format(msg, "\n".join(reqd_fields)),
            title=_("Missing Values Required"),
        )

    gst_category = get_gst_category(args)

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": args.get("name"),
            "address_line1": args.get("address_line1"),
            "address_line2": args.get("address_line2"),
            "city": args.get("city"),
            "state": args.get("state"),
            "pincode": args.get("pincode_custom"),
            "country": args.get("country"),
            "gstin": args.get("gstin_custom"),
            "gst_category": gst_category,
            "links": [
                {"link_doctype": args.get("doctype"), "link_name": args.get("name")}
            ],
        }
    ).insert()

    return address


customer.make_address = make_address


def validate_party(self, method=None):
    if self.get("gstin_info"):
        self.gstin_info = json.loads(self.get("gstin_info"))
        self.gstin_info_updated_on = now_datetime()
        self.ctb = self.gstin_info.get("ctb")
        self.sts = self.gstin_info.get("sts")
        self.default_gstin = self.gstin_info.get("gstin")
        self.trade_name = self.gstin_info.get("tradeNam")
        self.gstin_info = json.dumps(self.get("gstin_info"))

    if self.get("gstin_custom") and (
        self.get("gstin_custom") != "URP" or self.get("gstin_custom") != "NA"
    ):
        pan = self.get("gstin_custom")[2:12]
        if PAN_NUMBER_FORMAT.match(pan):
            self.pan = pan


def validate_address(self, method=None):
    if self.get("gstin_custom"):
        self.gstin = self.gstin_custom
        gst_category = get_gst_category(self)
        if gst_category:
            self.gst_category = gst_category
            del self.gstin_info

    if self.get("pincode_custom"):
        self.pincode = self.pincode_custom

    if self.get("customer"):
        self.address_title = self.get("customer")
        self.append(
            "links", {"link_doctype": "Customer", "link_name": self.get("customer")}
        )

    if self.get("supplier"):
        self.address_title = self.get("supplier")
        self.append(
            "links", {"link_doctype": "Supplier", "link_name": self.get("supplier")}
        )


def get_gst_category(self):
    if self.get("gstin_info"):
        self.gstin_info = json.loads(self.get("gstin_info"))
    if self.get("gstin_custom") == "URP" or self.get("gstin_custom") == "NA":
        gst_category = gst_category_map["URP"]
    else:
        gst_category = gst_category_map[self.get("gstin_info").get("dty")]

    self.gstin_info = json.dumps(self.get("gstin_info"))
    return gst_category
