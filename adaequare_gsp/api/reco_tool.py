import frappe
from math import ceil
from calendar import monthrange
from datetime import datetime

# filters
# get 2 data sets
# rules to match data with preference
@frappe.whitelist()
def get_date_range(period):
    now = datetime.now()
    start_month = end_month = month = now.month
    start_year = end_year = year = now.year
    quarter = ceil(month / 3)

    if "Previous Month" in period:
        start_month = end_month = month - 1 or 12
    elif "Quarter" in period:
        end_month = quarter * 3
        if "Previous" in period:
            end_month = (quarter - 1) * 3 or 12
        start_month = end_month - 2

    if start_month > month:
        start_year = end_year = year - 1
    elif "Year" in period:
        start_month = 4
        end_month = 3
        if "Previous" in period:
            start_year = end_year = year - 1
        if start_month > month:
            start_year -= 1
        else:
            end_year += 1

    date1 = datetime.strftime(datetime(start_year, start_month, 1), "%Y-%m-%d")
    date2 = datetime(end_year, end_month, monthrange(end_year, end_month)[1])
    date2 = datetime.strftime(date2 if date2 < now else now, "%Y-%m-%d")
    return [date1, date2]
