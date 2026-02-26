import frappe
from shopify.resources import Product

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def sync_barcode_to_shopify(doc, method=None):
    """
    Sync ERPNext custom_barcode field to Shopify Variant barcode
    """
    frappe.msgprint("Syncing barcode to Shopify...")

    if doc.flags.from_integration:
        return

    if doc.has_variants:
        return

    product_id = frappe.db.get_value(
        "Ecommerce Item",
        {
            "erpnext_item_code": doc.name,
            "integration": MODULE_NAME
        },
        "integration_item_code"
    )

    if not product_id:
        return

    product = Product.find(product_id)

    if not product or not product.variants:
        return

    variant = product.variants[0]

    new_barcode = doc.custom_barcode or ""

    if variant.barcode == new_barcode:
        return

    variant.barcode = new_barcode
    variant.save()