# Copyright (c) 2021, Resilient Tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GSTReturnsLog(Document):
    def validate(self):
        valid_party_types = ("Supplier", "Customer")
        if self.party_type not in valid_party_types:
            frappe.throw(f"Party Type can only be one of {valid_party_types}")
