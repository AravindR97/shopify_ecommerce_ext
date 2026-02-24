import frappe
from frappe import _
from frappe.utils import flt

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


@frappe.whitelist()
def create_material_receipt(data=None):
    try:

        if not data:
            data = frappe.form_dict

        data = frappe.parse_json(data)

        warehouse = data.get("warehouse")
        item_code = data.get("item_code")
        uom = data.get("uom")
        quantity = data.get("quantity")
        rate = data.get("rate")

        if not all([warehouse, item_code, uom, quantity, rate]):
            frappe.throw(_("All fields are required"))

        company = frappe.db.get_value("Warehouse", warehouse, "company")

        if not company:
            frappe.throw(_("Invalid Warehouse"))

        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.company = company

        stock_entry.append("items", {
            "item_code": item_code,
            "t_warehouse": warehouse,
            "uom": uom,
            "qty": flt(quantity),
            "basic_rate": flt(rate)
        })

        # Insert as Draft
        stock_entry.insert()

        return {
            "status": "success",
            "stock_entry": stock_entry.name,
            "docstatus": stock_entry.docstatus
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Material Receipt API Error")
        return {
            "status": "error",
            "message": str(e)
        }