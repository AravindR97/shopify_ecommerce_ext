import frappe
from shopify.resources import Product, Image

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def set_shopify_variant_image(doc, method=None):
    """
    When an ERPNext Item Variant has an image,
    attach that image to the corresponding Shopify Variant.
    """

    # Avoid recursion
    if doc.flags.from_integration:
        return

    # Only for variants
    if not doc.variant_of:
        return

    # No image attached
    if not doc.image:
        return

    # ------------------------------------------
    # Get Shopify Product ID (parent item)
    # ------------------------------------------
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

    # ------------------------------------------
    # Find matching Shopify Variant by SKU
    # ------------------------------------------
    shopify_variant = None
    for variant in product.variants:
        if variant.sku == doc.item_code:
            shopify_variant = variant
            break

    if not shopify_variant:
        return

    # ------------------------------------------
    # Create Image in Shopify
    # ------------------------------------------
    image_url = frappe.utils.get_url(doc.image)

    new_image = Image({
        "product_id": product.id,
        "src": image_url
    })
    new_image.save()

    # ------------------------------------------
    # Assign image to Variant
    # ------------------------------------------
    shopify_variant.image_id = new_image.id
    shopify_variant.save()