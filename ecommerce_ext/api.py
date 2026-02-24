import frappe
from frappe import _

@frappe.whitelist()
def get_item_by_barcode(barcode):
    if not barcode:
        frappe.throw(_("Barcode is required"))

    # Fetch item directly using barcode field
    item = frappe.db.get_value(
        "Item",
        {"custom_barcode": barcode},
        [
            "name",
            "item_name",
            "item_group",
            "stock_uom",
            "description",
            "disabled"
        ],
        as_dict=True
    )

    if not item:
        frappe.throw(_("No Item found for this barcode"))

    uoms = frappe.get_all(
        "UOM Conversion Detail",
        filters={"parent": item.name},
        pluck="uom"
    )

    return {
        "item_code": item.name,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "default_uom": item.stock_uom,
        "description": item.description,
        "available_uoms": uoms
    }