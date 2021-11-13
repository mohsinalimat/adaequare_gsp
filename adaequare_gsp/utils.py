import frappe
from erpnext.regional.india import state_numbers


def show_progress(title, processed, total=100, msg=""):
    frappe.emit_js(
        "frappe.show_progress(`{}`, {}, {}, `{}`);".format(title, processed, total, msg)
    )


def hide_progress(timeout=True):
    js = "frappe.hide_progress()"
    if timeout:
        js = "setTimeout(() => {0}, 1000)".format(js)

    frappe.emit_js(js)


def add_spacing(value, num):
    x = ""
    value = str(value)
    for i in range(0, len(value), num):
        x = x + value[i : i + num] + " "
    return x


def get_state(code):
    for state, scode in state_numbers.items():
        if int(scode) == code:
            return state


def get_sub_supply_type(code):
    map = {
        1: "Supply",
        2: "Import",
        3: "Export",
        4: "Job Work",
        5: "For Own Use",
        6: "Job work Returns",
        7: "Sales Return",
        8: "Others",
        9: "SKD/CKD",
        10: "Line Sales",
        11: "Recipient Not Known",
        12: "Exhibition or Fairs",
    }
    return map[int(code)]
