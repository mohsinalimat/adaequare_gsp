# Copyright (c) 2013, Resilient Tech and contributors
# For license information, please see license.txt

from collections import defaultdict
import json

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.exceptions import DuplicateEntryError

from adaequare_gsp.helpers.gstn_public_api import GstnPublicApi
from adaequare_gsp.utils import show_progress, hide_progress


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_columns(filters):
    columns = [
        {
            "fieldname": "supplier",
            "label": _("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 300,
        },
        {
            "fieldname": "gstin",
            "label": _("GSTIN"),
            "fieldtype": "Data",
            "width": 200,
        },
    ]

    columns += [
        {"fieldname": filedname, "label": _(label), "fieldtype": "Data"}
        for filedname, label in get_months(filters.get("return_period", []))
    ]

    return columns


def get_data(filters):
    data = get_suppliers(filters)
    data = update_returns(filters, data)
    return data


def get_months(dates, only_fieldname=False):
    if not dates:
        return []

    start, end = tuple(getdate(date) for date in dates)

    def total_months(dt):
        return dt.month + 12 * dt.year

    months = []
    for total_month in range(total_months(start) - 1, total_months(end)):
        year, month = divmod(total_month, 12)

        month_date = getdate(f"{year}-{month + 1}-01")

        month = month_date.strftime("%m%Y")
        if not only_fieldname:
            month = (month, month_date.strftime("%b, %Y"))
        months.insert(0, month)
    return months


def get_suppliers(filters):
    if filters.get("only_from_purchase_invoice"):
        suppliers = frappe.db.get_all(
            "Purchase Invoice",
            group_by="supplier, supplier_gstin",
            fields=("supplier", "supplier_gstin as gstin"),
            filters={
                "supplier_gstin": ("is", "set"),
                "posting_date": ("between", filters.get("return_period", [])),
            },
            order_by="supplier",
        )

        return [supplier for supplier in suppliers if len(supplier.gstin) == 15]

    return frappe.db.sql(
        """
        SELECT link.link_name as supplier, address.gstin
        FROM `tabAddress` address
        INNER JOIN `tabDynamic Link` link
        ON address.name = link.parent
        WHERE address.gstin is not null
            AND length(address.gstin) = 15
            AND link.link_doctype = 'Supplier'
        GROUP BY link.link_name, address.gstin
    """,
        as_dict=True,
    )


def update_returns(filters, data):
    gstins = tuple(supplier["gstin"] for supplier in data)

    logs = frappe.get_all(
        "GST Returns Log",
        filters={
            "gstin": ("in", gstins),
            "return_type": filters.get("return_type"),
        },
        fields=("gstin", "return_period"),
    )

    filed_returns = defaultdict(list)
    for log in logs:
        filed_returns[log.gstin].append(log.return_period)

    for row in data:
        filed_months = filed_returns[row["gstin"]]

        for month in get_months(filters.get("return_period", []), True):
            row[month] = "✅" if month in filed_months else "❌"

    return data


@frappe.whitelist()
def fetch_latest_returns(financial_year, suppliers=None):
    if not suppliers:
        return

    suppliers = json.loads(suppliers)

    progress_title = "Loading"
    suppliers_count = len(suppliers)
    show_progress(progress_title, 0, suppliers_count)

    api = GstnPublicApi()
    start_year, end_year = financial_year.split("-")
    financial_year = start_year + "-" + end_year[-2:]

    logs = frappe.get_all(
        "GST Returns Log",
        filters={
            "gstin": ("in", [supplier["gstin"] for supplier in suppliers]),
        },
        pluck="arn",
    )

    created = 0
    for index, supplier in enumerate(suppliers):
        progress_msg = "Fetching returns for {} ({}/{})...".format(
            supplier["supplier"], index + 1, suppliers_count
        )
        show_progress(progress_title, index, suppliers_count, progress_msg)

        try:
            # TODO: check if api needs to be recalled (based on previos data)
            response = api.get_returns_info(supplier["gstin"], financial_year)
            for log in response.get("EFiledlist", []):
                if log in logs:
                    continue

                log.update(supplier)
                if create_gst_returns_log(log):
                    created += 1

        except Exception:
            frappe.clear_last_message()
            continue

    hide_progress(timeout=False)
    frappe.msgprint(
        f"{created} returns added!",
        title="success",
        indicator="green",
    )


def create_gst_returns_log(log):
    # TODO: ignore permission or not?
    try:
        frappe.get_doc(
            {
                "doctype": "GST Returns Log",
                "party_type": "Supplier",
                "party": log["supplier"],
                "gstin": log["gstin"],
                "arn": log["arn"],
                "mode_of_filing": log["mof"],
                "return_period": log["ret_prd"],
                "is_valid": log["valid"] == "Y",
                "status": log["status"],
                "return_type": log["rtntype"],
                "date_of_filling": getdate(log["dof"]),
            }
        ).insert(ignore_permissions=True)
        return True

    except DuplicateEntryError:
        frappe.clear_last_message()
