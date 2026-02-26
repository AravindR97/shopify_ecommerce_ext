import frappe
from shopify.resources import Product

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def sync_barcode_to_shopify(doc, method=None):
    """
    Sync ERPNext custom_barcode field to Shopify Variant barcode
    Sync ERPNext image field to Shopify Product Media (Images)
    """

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

    # ------------------------
    # BARCODE SYNC
    # ------------------------
    variant = product.variants[0]
    new_barcode = doc.custom_barcode or ""

    if variant.barcode != new_barcode:
        variant.barcode = new_barcode
        variant.save()

    # ------------------------
    # IMAGE SYNC
    # ------------------------
    if not doc.image:
        return

    # Convert relative file path to full URL
    image_url = frappe.utils.get_url(doc.image)

    # Check if image already exists in Shopify
    existing_images = product.images or []
    already_exists = any(img.src == image_url for img in existing_images)

    if already_exists:
        return

    # Add new image to Shopify product
    product.images = [{"src": image_url}]
    product.save()