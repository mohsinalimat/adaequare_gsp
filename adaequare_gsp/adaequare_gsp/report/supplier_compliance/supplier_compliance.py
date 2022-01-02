# Copyright (c) 2013, Resilient Tech and contributors
# For license information, please see license.txt

from datetime import datetime
import json

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import add_months
from frappe.utils.data import add_days, now_datetime
from six import string_types

from erpnext.accounts.utils import get_fiscal_year

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


def get_months(dates, as_datetime=False):
    if not dates:
        return []

    start, end = tuple(getdate(date) for date in dates)
    if end.month == getdate().month:
        end = add_months(end, -1)

    def total_months(dt):
        return dt.month + 12 * dt.year

    months = []
    for total_month in range(total_months(start) - 1, total_months(end)):
        year, month = divmod(total_month, 12)

        month = getdate(f"{year}-{month + 1}-01")
        fieldname = month.strftime("%m%Y")
        if not as_datetime:
            month = month.strftime("%b, %Y")

        months.insert(0, (fieldname, month))
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
    if not data:
        return data

    logs = frappe.db.sql(
        """
            SELECT log.gstin, child.return_period
            FROM `tabGST Returns Log` log
            INNER JOIN `tabGST Returns Log Item` child
            ON child.parent = log.name
            WHERE log.gstin in ({0})
                AND child.return_type = %s
        """.format(
            ", ".join(frappe.db.escape(supplier["gstin"]) for supplier in data)
        ),
        as_dict=True,
        values=filters.return_type,
    )

    filed_returns = {}
    for log in logs:
        if log.gstin not in filed_returns:
            filed_returns[log.gstin] = []
        filed_returns[log.gstin].append(log.return_period)

    for row in data:
        filed_months = filed_returns.get(row["gstin"], [])
        latest_filed_month = max(
            (datetime.strptime(month, "%m%Y").date() for month in filed_months),
            default=datetime.min.date(),
        )
        for fieldname, month in get_months(filters.get("return_period", []), True):
            if fieldname in filed_months:
                row[fieldname] = "✅"
            elif month < latest_filed_month:
                row[fieldname] = "➖"
            else:
                row[fieldname] = "❌"

    return data


@frappe.whitelist()
def fetch_latest_returns(fy, suppliers):
    if isinstance(suppliers, string_types):
        suppliers = json.loads(suppliers)

    progress_title = "Loading"
    suppliers_count = len(suppliers)
    show_progress(progress_title, 0, suppliers_count)

    api = GstnPublicApi()
    current_fy = get_fiscal_year(now_datetime())[0]
    fy_end_date = get_fiscal_year(fiscal_year=fy)[2]
    next_fy = add_fiscal_year(fy, 1)

    logs_name = []
    for supplier in suppliers:
        logs_name.append(f"{supplier['gstin']}-{fy}")
        # Fetch for next fy
        if fy != current_fy and supplier.get(f"03{fy_end_date.year}") != "✅":
            logs_name.append(f"{supplier['gstin']}-{next_fy}")

    logs = frappe.db.sql(
        """
        SELECT log.name, log.last_synced_on, log.gstin, child.arn
        FROM `tabGST Returns Log` log
        LEFT JOIN `tabGST Returns Log Item` child
        ON child.parent = log.name
        WHERE log.name in ({0})
    """.format(
            ", ".join(map(frappe.db.escape, logs_name))
        ),
        as_dict=True,
        debug=True,
    )
    existing_logs = frappe._dict()
    for log in logs:
        arn = log.pop("arn")
        if log.name not in existing_logs:
            existing_logs[log.name] = {"returns": [], **log}
        if arn:
            existing_logs[log.name]["returns"].append(arn)

    counter = frappe._dict(created=0, updated=0, skipped=0, api_calls=0, failed=[])
    for idx, supplier in enumerate(suppliers, 1):
        docname = f"{supplier['gstin']}-{fy}"
        log_exists = docname in existing_logs

        progress_msg = "Fetching returns for {} ({}/{})...".format(
            supplier["supplier"], idx, suppliers_count
        )
        show_progress(progress_title, idx, suppliers_count, progress_msg)
        try:
            if fy != current_fy and supplier.get(f"03{fy_end_date.year}") != "✅":
                next_year_docname = f"{supplier['gstin']}-{next_fy}"

                counter.api_calls += 1
                response = api.get_returns_info(supplier["gstin"], next_fy)
                if create_gst_returns_log(
                    next_fy,
                    supplier,
                    response.get("EFiledlist", []),
                    next_year_docname,
                    existing_logs.get(next_year_docname, {}).get("returns", []),
                ):
                    counter.created += 1

            counter_update_key = "created"
            if log_exists:
                counter_update_key = "updated"
                last_synced_on = existing_logs[docname]["last_synced_on"]
                # TODO: get this value from Adaequare settings
                dont_update_days = 10
                if (
                    fy != current_fy and last_synced_on.date() > fy_end_date
                ) or last_synced_on > add_days(now_datetime(), -dont_update_days):
                    counter.skipped += 1
                    continue

            counter.api_calls += 1
            response = api.get_returns_info(supplier["gstin"], fy)
            if create_gst_returns_log(
                fy,
                supplier,
                response.get("EFiledlist", []),
                docname,
                existing_logs.get(docname, {}).get("returns", []),
                log_exists,
            ):
                counter[counter_update_key] += 1

        except Exception as e:
            frappe.clear_last_message()
            print("Unexpected error:", e)
            counter.failed.append(frappe._dict(supplier=supplier, error=e))
            continue

    hide_progress(timeout=False)
    end_message = """
        <b>{skipped}</b> API calls saved,
        <b>{api_calls}</b> times API called,
        <b>{created}</b> returns created and <b>{updated}</b> returns updated!
        <br><br>
        Failed<b>({failed_count})</b> to fetch data for following suppliers:
        <ul>
        {failed_suppliers}
        </ul>
    """.format(
        failed_suppliers="".join(
            f"<li><b>{f.supplier['supplier']}({f.supplier['gstin']})</b>: {f.error}</li>"
            for f in counter.failed
        ),
        failed_count=len(counter.failed),
        **counter,
    )
    frappe.msgprint(end_message, title="success", indicator="green")


def create_gst_returns_log(fy, supplier, returns, docname, existing_arns, update=None):
    print("creating return log for", supplier, fy)
    doctype = "GST Returns Log"
    returns = [
        {
            "arn": log["arn"],
            "mode_of_filing": log["mof"],
            "return_period": log["ret_prd"],
            "is_valid": log.get("valid", "Y") == "Y",
            "status": log["status"],
            "return_type": log["rtntype"],
            "date_of_filling": datetime.strptime(log["dof"], "%d-%m-%Y").date(),
        }
        for log in returns
        if log["arn"] not in existing_arns
    ]

    if not returns:
        return

    if update is None:
        update = frappe.db.exists(doctype, docname)

    doc = (
        frappe.get_doc(doctype, docname)
        if update
        else frappe.get_doc(
            {
                "doctype": doctype,
                "party_type": "Supplier",
                "party": supplier["supplier"],
                "gstin": supplier["gstin"],
                "last_synced_on": now_datetime(),
                "financial_year": fy,
            }
        )
    )
    doc.extend("returns", returns)
    return doc.save(ignore_permissions=True)


def add_fiscal_year(fy, years):
    start, end = fy.split("-")
    return f"{int(start) + years}-{int(end) + years}"
