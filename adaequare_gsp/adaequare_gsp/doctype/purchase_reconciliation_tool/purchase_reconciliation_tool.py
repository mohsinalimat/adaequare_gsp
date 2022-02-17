# Copyright (c) 2022, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
import pandas as pd

from datetime import datetime
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from adaequare_gsp.helpers.schema.gstr_2a import CLASSIFICATION
from adaequare_gsp.api.gstr_2a import get_gstr_2a, upload_gstr_2a
from adaequare_gsp.api.gstr_2b import get_gstr_2b, upload_gstr_2b, get_json_from_url
from fuzzywuzzy import process, fuzz


class PurchaseReconciliationTool(Document):
    FIELDS_TO_MATCH = ["fy", "bill_no", "place_of_supply", "reverse_charge", "tax"]

    def validate(self):
        self.reconcilier()

    def reconcilier(self):
        purchases = self.get_b2b_purchase()
        inward_supplies = self.get_b2b_inward_supply()

        rules_list = [
            {"Exact Match": ["E", "E", "E", "E", 0]},
            {"Exact Match": ["E", "F", "E", "E", 0]},
            {"Partial Match": ["E", "E", "E", "E", 4]},
            {"Partial Match": ["E", "F", "E", "E", 4]},
            {"Mismatch": ["E", "E", "N", "N", "N"]},
            {"Mismatch": ["E", "F", "N", "N", "N"]},
            {"Residual Match": ["E", "N", "E", "E", 4]},
        ]
        for rules in rules_list:
            for k, v in rules.items():
                print(k, "\n")
                self.find_match(purchases, inward_supplies, k, v)

        # print("Inward Supplies")
        # for gstin in inward_supplies:
        #     for isup in inward_supplies.get(gstin):
        #         print(isup.supplier_name, isup.bill_no, isup.name)
        # print("\n", "Purchases")
        # for gstin in purchases:
        #     for isup in purchases.get(gstin):
        #         print(isup.supplier_name, isup.bill_no, isup.name)

    def find_match(self, purchases, inward_supplies, status, rules):
        for gstin in purchases:
            if not inward_supplies.get(gstin):
                continue

            monthly_pur = {}
            if status == "Residual Match":
                monthly_pur = self.get_monthly_pur(purchases[gstin])
                monthly_isup = self.get_monthly_pur(inward_supplies[gstin])
                status = "Mismatch"

            for pur in purchases[gstin][:]:
                for isup in inward_supplies.get(gstin)[:]:
                    if monthly_pur and not (
                        -4
                        < monthly_pur[pur.bill_date.month]
                        - monthly_isup[isup.bill_date.month]
                        < 4
                    ):
                        continue

                    if not self.rules_match(pur, isup, rules):
                        continue
                    print(pur.bill_no, isup.bill_no, pur.name, isup.name)
                    # frappe.db.set_value(
                    #     "Inward Supply",
                    #     isup.name,
                    #     {
                    #         "match_status": status,
                    #         "link_doctype": "Purchase Invoice",
                    #         "link_name": pur.name,
                    #     },
                    # )
                    purchases[gstin].remove(pur)
                    inward_supplies[gstin].remove(isup)
                    break

    def rules_match(self, pur, isup, rules):
        for field in self.FIELDS_TO_MATCH:
            i = self.FIELDS_TO_MATCH.index(field)
            if not self.get_field_match(pur, isup, field, rules[i]):
                return False
        return True

    def get_field_match(self, pur, isup, field, rule):
        # **** Just for Reference ****
        #  "E": "Exact Match"
        #  "F": "Fuzzy Match for Bill No"
        #  "N": "No Match"
        #    0: "No Tax Difference"
        #    4: "Rounding Tax Difference"
        if rule == "E":
            return pur[field] == isup[field]
        elif rule == "N":
            return True
        elif rule == "F":
            return self.fuzzy_match(pur, isup)
        elif rule == 0:
            return self.get_tax_differece(pur, isup) == 0
        elif rule == 4:
            return -4 < self.get_tax_differece(pur, isup) < 4

    def get_monthly_pur(self, gstin_data):
        monthly_pur = {}
        for pur in gstin_data:
            if monthly_pur.get(pur.bill_date.month):
                monthly_pur[pur.bill_date.month] += self.get_pur_tax(pur)
            else:
                monthly_pur[pur.bill_date.month] = self.get_pur_tax(pur)
        return monthly_pur

    def get_tax_differece(self, pur, isup):
        pur_tax = self.get_pur_tax(pur)
        isup_tax = self.get_pur_tax(isup)
        return pur_tax - isup_tax

    def get_pur_tax(self, pur):
        return pur.igst + pur.cgst + pur.sgst + pur.cess

    def fuzzy_match(self, pur, isup):
        if pur.bill_date.month != isup.bill_date.month:
            return False

        partial_ratio = fuzz.partial_ratio(pur._bill_no, isup._bill_no)
        if float(partial_ratio) == 100:
            return True
        return float(process.extractOne(pur._bill_no, [isup._bill_no])[1]) >= 90.0

    def get_b2b_purchase(self):
        purchase = frappe.qb.DocType("Purchase Invoice")
        taxes = frappe.qb.DocType("Purchase Taxes and Charges")
        purchase_data = (
            frappe.qb.from_(purchase)
            .join(taxes)
            .on(taxes.parent == purchase.name)
            .where(
                purchase.posting_date[self.purchase_from_date : self.purchase_to_date]
            )  # TODO instead all purchases not matched yet but gst accounts affected, should come up here after a specific date.
            .where(self.company_gstin == purchase.company_gstin)
            .where(purchase.is_return == 0)
            .where(purchase.gst_category == "Registered Regular")
            # .where(purchase.bill_no.like("GST/%"))
            .groupby(taxes.parent)
            .select(
                "name",
                "posting_date",
                "supplier_name",
                "supplier_gstin",
                "bill_no",
                "bill_date",
                "reverse_charge",
                "place_of_supply",  # TODO get tax accounts to match
                purchase.itc_integrated_tax.as_("igst"),
                purchase.itc_central_tax.as_("cgst"),
                purchase.itc_state_tax.as_("sgst"),
                purchase.itc_cess_amount.as_("cess"),
            )
            .run(as_dict=True, debug=True)
        )

        inward_supply = frappe.qb.DocType("Inward Supply")
        purchase_list = (
            frappe.qb.from_(inward_supply)
            .select("link_name")
            .where(inward_supply.link_doctype == "Purchase Invoice")
            .run(as_list=True)
        )

        for pur in purchase_data:
            if [pur.name] in purchase_list:
                del pur
                continue
            pur["fy"] = self.get_fy(pur.bill_date or pur.posting_date)
            pur["reverse_charge"] = 1 if pur["reverse_charge"] == "Y" else 0
            pur["_bill_no"] = self.get_comparable_bill_no(pur.bill_no, pur.fy)

        purchase_data = self.get_dict_for_key("supplier_gstin", purchase_data)
        return purchase_data

    def get_b2b_inward_supply(self):
        inward_supply = frappe.qb.DocType("Inward Supply")
        inward_supply_item = frappe.qb.DocType("Inward Supply Item")
        inward_supply_data = (
            frappe.qb.from_(inward_supply)
            .join(inward_supply_item)
            .on(inward_supply_item.parent == inward_supply.name)
            .where(self.company_gstin == inward_supply.company_gstin)
            .where(inward_supply.action.isin(["No Action", "Pending"]))
            .where(inward_supply.link_name.isnull())
            .where(inward_supply.classification.isin(["B2B", "B2BA"]))
            .where(inward_supply.doc_date < "2021-08-01")
            .groupby(inward_supply_item.parent)
            .select(
                "name",
                "supplier_name",
                "supplier_gstin",
                inward_supply.doc_number.as_("bill_no"),
                inward_supply.doc_date.as_("bill_date"),
                "reverse_charge",
                "place_of_supply",
                "classification",
                Sum(inward_supply_item.taxable_value).as_("taxable_value"),
                Sum(inward_supply_item.igst).as_("igst"),
                Sum(inward_supply_item.cgst).as_("cgst"),
                Sum(inward_supply_item.sgst).as_("sgst"),
                Sum(inward_supply_item.cess).as_("cess"),
            )
            .run(as_dict=True, debug=True)
        )
        # TODO process inward_supply_data
        for i_s in inward_supply_data:
            i_s["fy"] = self.get_fy(i_s.bill_date)
            i_s["_bill_no"] = self.get_comparable_bill_no(i_s.bill_no, i_s.fy)
            if i_s.classification == "B2BA":
                # find B2B
                # change action
                # unmatch with purchase and add match with current B2BA and same status
                # remove it from the list and remove B2B from the list if action in where filters above
                pass

        inward_supply_data = self.get_dict_for_key("supplier_gstin", inward_supply_data)
        return inward_supply_data

    def get_fy(self, date):
        if not date:
            return
        # Standard for India. Presuming 99.99% suppliers would use this.
        if date.month < 4:
            return f"{date.year - 1}-{date.year}"
        return f"{date.year}-{date.year + 1}"

    def get_dict_for_key(self, key, list):
        new_dict = frappe._dict()
        for data in list:
            if data[key] in new_dict:
                new_dict[data[key]].append(data)
            else:
                new_dict[data[key]] = [data]
        return new_dict

    def get_comparable_bill_no(self, bill_no, fy):
        fy = fy.split("-")
        replace_list = [
            f"{fy[0]}-{fy[1]}",
            f"{fy[0]}/{fy[1]}",
            f"{fy[0]}-{fy[1][2:]}",
            f"{fy[0]}/{fy[1][2:]}",
            f"{fy[0][2:]}-{fy[1][2:]}",
            f"{fy[0][2:]}/{fy[1][2:]}",
            "/",  # these are only special characters allowed in invoice
            "-",
        ]

        inv = bill_no
        for replace in replace_list:
            inv = inv.replace(replace, " ")
        inv = " ".join(inv.split()).lstrip("0")
        return inv

    @frappe.whitelist()
    def upload_gstr(self, gst_return, period, attach_file):
        if gst_return == "GSTR 2A":
            response = upload_gstr_2a(self.company_gstin, gst_return, period, attach_file)
        if gst_return == "GSTR 2B":
            response = upload_gstr_2b(self.company_gstin, gst_return, period, attach_file)
        return response

    @frappe.whitelist()
    def download_all_gstr(self, gstr_name, fiscal_year, otp=None):
        periods, download_history = self.get_downloads_history(gstr_name, fiscal_year)
        if gstr_name == "GSTR 2A":
            response = get_gstr_2a(self.company_gstin, periods, otp)
        elif gstr_name == "GSTR 2B":
            for period in periods[:]:
                download = next(
                    (i for i in download_history if i.return_period == period),
                    None,
                )
                if download:
                    periods.remove(period)
            response = get_gstr_2b(self.company_gstin, periods, otp)
        return response

    @frappe.whitelist()
    def download_missing_gstr(self, gstr_name, fiscal_year, otp=None):
        if gstr_name != "GSTR 2A":
            return

        periods, download_history = self.get_downloads_history(gstr_name, fiscal_year)
        for period in periods[:]:
            download = next(
                (i for i in download_history if i.return_period == period),
                None,
            )
            if download:
                periods.remove(period)

        response = get_gstr_2a(self.company_gstin, periods, otp)
        return response

    @frappe.whitelist()
    def fetch_download_history(self, gstr_name, fiscal_year, process_type):
        periods, download_history = self.get_downloads_history(gstr_name, fiscal_year)

        columns = ["Period", "Classification", "Status", "Downloaded On" if process_type == "download" else "Uploaded On"]
        data = {}
        for period in reversed(periods):
            data[period] = []
            for _class in CLASSIFICATION:
                download = next(
                    (
                        i
                        for i in download_history
                        if i.return_period == period
                        and i.classification in [_class, ""]
                    ),
                    None,
                )

                if process_type == "download":
                    status = "Downloaded" if download else "Not Downloaded"
                else:
                    status = "Uploaded" if download else "Not Uploaded"
                _dict = {
                    "Classification": _class if gstr_name == "GSTR 2A" else "ALL",
                    "Status": status,
                    "columns[-1:]": "✅ "
                    + download.last_updated_on.strftime("%d-%m-%Y %H:%M:%S")
                    if download
                    else "",
                }
                if _dict not in data[period]:
                    data[period].append(_dict)

        template = frappe.render_template(
            "adaequare_gsp/doctype/purchase_reconciliation_tool/download_history.html",
            {"columns": columns, "data": data},
        )
        return template

    def get_downloads_history(self, gstr_name, fiscal_year):
        fy_start, fy_end = frappe.db.get_value(
            "Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"]
        )
        today = datetime.today().date()
        fy_end = today if fy_end > today else fy_end
        periods = pd.date_range(fy_start, fy_end, freq="MS").strftime("%m%Y").tolist()

        download_history = frappe.db.get_list(
            "GSTR Download Log",
            filters={
                "return_period": ["in", periods],
                "gstin": self.company_gstin,
                "gst_return": gstr_name,
            },
            fields=["return_period", "classification", "last_updated_on"],
        )
        return periods, download_history

    @frappe.whitelist()
    def get_data_from_uploaded_json(self, attach_file):
        if attach_file:
            json_response = get_json_from_url(attach_file)
            ret_period = json_response.get('data').get('rtnprd')
            return ret_period

    @frappe.whitelist()
    def get_uploaded_gstr_ret_period(self, gst_return, attach_file):
        if attach_file:
            gstr_file_json = get_json_from_url(attach_file)
            try:
                if gst_return == "GSTR 2A":
                    ret_period = gstr_file_json.get('fp')
                if gst_return == "GSTR 2B":
                    ret_period = gstr_file_json.get('data').get('rtnprd')
                return ret_period
            except:
                return

@frappe.whitelist()
def get_summary_data(company_gstin, purchase_from_date, purchase_to_date, inward_from_date, inward_to_date):
    purchase = frappe.qb.DocType("Purchase Invoice")
    taxes = frappe.qb.DocType("Purchase Taxes and Charges")
    purchase_data = (
        frappe.qb.from_(purchase)
        .join(taxes)
        .on(taxes.parent == purchase.name)
        .where(
            purchase.posting_date[purchase_from_date : purchase_to_date]
        )  # TODO instead all purchases not matched yet but gst accounts affected, should come up here after a specific date.
        .where(company_gstin == purchase.company_gstin)
        .where(purchase.is_return == 0)
        .where(purchase.gst_category == "Registered Regular")
        # .where(purchase.bill_no.like("GST/%"))
        .groupby(taxes.parent)
        .select(
            "name",
            "supplier_name",
            "supplier_gstin",
        )
        .run(as_dict=True, debug=True)
    )

    inward_supply = frappe.qb.DocType("Inward Supply")
    inward_supply_item = frappe.qb.DocType("Inward Supply Item")
    inward_supply_data = (
        frappe.qb.from_(inward_supply)
        .join(inward_supply_item)
        .on(inward_supply_item.parent == inward_supply.name)
        .where(
            inward_supply.doc_date[inward_from_date : inward_to_date]
        ) 
        .where(company_gstin == inward_supply.company_gstin)
        .where(inward_supply.action.isin(["No Action", "Pending"]))
        .where(inward_supply.link_name.isnull())
        .where(inward_supply.classification.isin(["B2B", "B2BA"]))
        .where(inward_supply.doc_date < "2021-08-01")
        .groupby(inward_supply_item.parent)
        .select(
            "name",
            "supplier_name",
            "supplier_gstin",
            inward_supply.doc_number.as_("bill_no"),
            inward_supply.doc_date.as_("bill_date"),
            "reverse_charge",
            "place_of_supply",
            "classification",
            Sum(inward_supply_item.taxable_value).as_("taxable_value"),
            Sum(inward_supply_item.igst).as_("igst"),
            Sum(inward_supply_item.cgst).as_("cgst"),
            Sum(inward_supply_item.sgst).as_("sgst"),
            Sum(inward_supply_item.cess).as_("cess"),
        )
        .run(as_dict=True, debug=True)
    )

    summary_data = []
    summary_data.append({
        'no_of_doc_purchase': len(purchase_data),
        'no_of_inward_supp': len(inward_supply_data),
        'purchase_data': purchase_data
    })
    return summary_data
