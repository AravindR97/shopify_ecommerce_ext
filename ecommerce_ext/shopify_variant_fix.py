import frappe
import requests
from shopify.resources import Product
from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def prevent_duplicate_variant_and_fix_image(doc, method=None):
    """
    1. Prevent duplicate variant creation popup
    2. Attach image to correct Shopify variant
    3. Do NOT overwrite product image
    """

    if doc.flags.from_integration:
        return

    # Only variants
    if not doc.variant_of:
        return

    # Get Shopify Product ID from template mapping
    product_id = frappe.db.get_value(
        "Ecommerce Item",
        {
            "erpnext_item_code": doc.variant_of,
            "integration": MODULE_NAME
        },
        "integration_item_code"
    )

    if not product_id:
        return

    product = Product.find(product_id)

    if not product:
        return

    # -----------------------------------------
    # STOP DUPLICATE VARIANT CREATION
    # -----------------------------------------
    existing_variant = None

    for variant in product.variants:
        if variant.sku == doc.item_code:
            existing_variant = variant
            break

    if existing_variant:
        # 🔥 CRITICAL LINE
        # Tell core integration to skip upload
        doc.flags.from_integration = True

    else:
        # Variant not yet created → let core handle it
        return

    # -----------------------------------------
    # FIX VARIANT IMAGE (Attach Properly)
    # -----------------------------------------
    if not doc.image:
        return

    image_url = frappe.utils.get_url(doc.image)

    # Correct DocType name (singular!)
    settings = frappe.get_doc("Shopify Setting")

    shop_url = settings.shopify_url
    token = settings.get_password("access_token")

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }

    # Avoid duplicate variant image
    for img in product.images or []:
        if img.src == image_url and existing_variant.id in (img.variant_ids or []):
            return

    image_payload = {
        "image": {
            "src": image_url,
            "variant_ids": [existing_variant.id]
        }
    }

    url = f"https://{shop_url}/admin/api/2023-10/products/{product_id}/images.json"

    response = requests.post(url, json=image_payload, headers=headers)

    if response.status_code not in (200, 201):
        frappe.log_error(
            title="Shopify Variant Image Error",
            message=response.text
        )