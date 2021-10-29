import frappe
from adaequare_gsp.helpers.gstn_public_api import GstnPublicApi
from adaequare_gsp.adaequare_gsp.doctype.adaequare_settings.adaequare_settings import (
    update_party_gstin_details,
    get_parties
)


@frappe.whitelist()
def get_gstin_details(gstin):
    api = GstnPublicApi()
    return api.get_gstin_info(gstin)


@frappe.whitelist()
def get_party_gstin(customer=None, supplier=None):
    if customer:
        tab = "tabCustomer"
        values = {"party": customer}
    elif supplier:
        tab = "tabSupplier"
        values = {"party": supplier}
    else:
        return

    gstin = frappe.db.sql(
        """
        SELECT addr.gstin, party.pan
        FROM `tabAddress` as addr
            LEFT JOIN `tabDynamic Link` as link
            ON addr.name = link.parent
            LEFT JOIN {} as party
            ON link.link_name = party.name
            WHERE link.link_name = %(party)s
    """.format(
            tab
        ),
        values,
        as_dict=1,
    )

    for r in gstin:
        if r.get("gstin") and r.get("gstin")[2:12] == r.get("pan"):
            return r.gstin

@frappe.whitelist()
def update_party(dt, dn):
    parties = get_parties(dt, {'name': dn}) if dt == 'Customer' else get_parties(dt, {'name': dn})
    update_party_gstin_details(1, dt, parties)
    return True
