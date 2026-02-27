import frappe
from shopify.resources import Product

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def sync_barcode_to_shopify(doc, method=None):

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

    # =====================================================
    # ✅ DESCRIPTION FIX (SAFE ADDITION)
    # =====================================================
    if doc.variant_of:
        template = frappe.get_doc("Item", doc.variant_of)

        if template.description and product.body_html != template.description:
            product.body_html = template.description
            product.save()
    # =====================================================


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

    image_url = frappe.utils.get_url(doc.image)

    existing_images = product.images or []
    already_exists = any(img.src == image_url for img in existing_images)

    if already_exists:
        return

    product.images = [{"src": image_url}]
    product.save()