# Copyright (c) 2026, Aravind R and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemStorageLocation(Document):
    def before_insert(self):
        self.aisle = self.aisle.upper()
        self.rack = self.rack.upper()
        self.location = self.warehouse + " - " + self.aisle + " - " + self.rack
