import frappe
import requests
from shopify.resources import Product
from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def fix_variant_popup_and_image(doc, method=None):
    """
    1) Prevent 'Variant already exists' popup
    2) Attach image to correct Shopify variant
    3) Do NOT overwrite product image
    """

    if doc.flags.from_integration:
        return

    # Only run for variant items
    if not doc.variant_of:
        return

    # Get Shopify Product ID (mapped to template)
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

    # ---------------------------------------
    # STEP 1: STOP VARIANT DUPLICATE POPUP
    # ---------------------------------------
    existing_variant = None

    for variant in product.variants:
        if variant.sku == doc.item_code:
            existing_variant = variant
            break

    if not existing_variant:
        # Let core create it normally
        return

    # If exists → update safely instead of letting core fail
    price = doc.standard_rate or 0

    if str(existing_variant.price) != str(price):
        existing_variant.price = price
        existing_variant.save()

    # ---------------------------------------
    # STEP 2: ATTACH VARIANT IMAGE PROPERLY
    # ---------------------------------------
    if not doc.image:
        return

    image_url = frappe.utils.get_url(doc.image)

    settings = frappe.get_doc("Shopify Settings")
    shop_url = settings.shopify_url
    token = settings.get_password("access_token")

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }

    # Check if image already attached to this variant
    for img in product.images or []:
        if img.src == image_url and existing_variant.id in (img.variant_ids or []):
            return  # already correct

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