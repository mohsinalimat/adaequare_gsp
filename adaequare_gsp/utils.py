import frappe


def show_progress(title, processed, total=100, msg=""):
    frappe.emit_js(
        "frappe.show_progress(`{}`, {}, {}, `{}`);".format(title, processed, total, msg)
    )


def hide_progress(timeout=True):
    js = "frappe.hide_progress()"
    if timeout:
        js = "setTimeout(() => {0}, 1000)".format(js)

    frappe.emit_js(js)
