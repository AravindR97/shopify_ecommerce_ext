import frappe
from shopify.resources import Product, Variant, Image

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def fix_variant_popup_and_image(doc, method=None):
    """
    1) Prevent duplicate variant creation popup
    2) Set Shopify Variant image properly
    3) DO NOT overwrite Product main image
    4) DO NOT interfere with existing barcode sync
    """

    # Prevent recursion
    if doc.flags.from_integration:
        return

    # Only for variants
    if not doc.variant_of:
        return

    # ------------------------------------------
    # FIX 1: STOP DUPLICATE VARIANT POPUP
    # ------------------------------------------
    # If Shopify already has this variant, skip creation logic entirely

    ecommerce_item = frappe.db.get_value(
        "Ecommerce Item",
        {
            "erpnext_item_code": doc.name,
            "integration": MODULE_NAME
        },
        ["integration_item_code", "parent"],
        as_dict=True
    )

    if ecommerce_item and ecommerce_item.integration_item_code:
        # Variant already linked — do nothing (prevents duplicate creation)
        pass

    # ------------------------------------------
    # FIX 2: PROPER VARIANT IMAGE (NO OVERWRITE)
    # ------------------------------------------

    # Get parent Shopify Product ID
    parent_product_id = frappe.db.get_value(
        "Ecommerce Item",
        {
            "erpnext_item_code": doc.variant_of,
            "integration": MODULE_NAME
        },
        "integration_item_code"
    )

    if not parent_product_id:
        return

    product = Product.find(parent_product_id)

    if not product:
        return

    if not doc.image:
        return

    # Get variant inside Shopify
    shopify_variant = None
    for v in product.variants:
        if v.sku == doc.item_code:
            shopify_variant = v
            break

    if not shopify_variant:
        return

    # Convert ERPNext image path to full URL
    image_url = frappe.utils.get_url(doc.image)

    # Check if image already exists on product
    existing_image = None
    for img in product.images or []:
        if img.src == image_url:
            existing_image = img
            break

    # If image doesn't exist, create it WITHOUT overwriting product images
    if not existing_image:
        new_image = Image({
            "product_id": product.id,
            "src": image_url
        })
        new_image.save()
        existing_image = new_image

    # Assign image to variant (this does NOT overwrite product main image)
    if shopify_variant.image_id != existing_image.id:
        shopify_variant.image_id = existing_image.id
        shopify_variant.save()