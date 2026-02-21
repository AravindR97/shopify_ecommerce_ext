import frappe
import requests


# -----------------------------------------------------------
# MAP YOUR CUSTOM ERPNEXT FIELDS TO SHOPIFY METAFIELD KEYS
# Add/remove entries here as you add more custom fields.
#
# Format:
#   "erpnext_fieldname": ("metafield_namespace", "metafield_key", "shopify_type")
#
# Common Shopify metafield types for text:
#   "single_line_text_field", "multi_line_text_field"
# -----------------------------------------------------------
CUSTOM_FIELD_MAP = {
    "custom_barcode": ("custom", "barcode", "single_line_text_field"),
    "custom_color": ("custom", "color", "single_line_text_field"),
    # Add more fields here as needed
}


def push_metafields_to_shopify(doc, method=None):
    """
    Called after an ERPNext Item is saved.
    Finds the linked Shopify product and pushes custom fields as metafields.
    """

    # Only proceed if this item is synced with Shopify
    shopify_product_id = get_shopify_product_id(doc.name)
    if not shopify_product_id:
        return

    # Get Shopify connection settings
    settings = get_shopify_settings()
    if not settings:
        return

    # Build the metafields payload from the item's custom fields
    metafields = build_metafields_payload(doc)
    if not metafields:
        return

    # Push each metafield to Shopify
    push_metafields(settings, shopify_product_id, metafields)


def get_shopify_product_id(item_code):
    """
    Looks up the Shopify Product ID linked to this ERPNext item.
    ecommerce_integrations stores this in the Ecommerce Item doctype.
    """
    result = frappe.db.get_value(
        "Ecommerce Item",
        {"erpnext_item_code": item_code, "integration": "shopify"},
        "integration_item_code",  # this is the Shopify product ID
    )
    return result


def get_shopify_settings():
    """
    Fetches Shopify store URL and API credentials from
    the Shopify Setting doctype provided by ecommerce_integrations.
    """
    try:
        settings = frappe.get_doc("Shopify Setting")
        if not settings.enable_shopify:
            return None
        return settings
    except Exception:
        frappe.log_error("ecommerce_ext: Could not load Shopify Settings")
        return None


def build_metafields_payload(doc):
    """
    Reads the custom fields from the Item doc and builds
    a list of Shopify metafield dicts, skipping any empty fields.
    """
    metafields = []

    for erpnext_field, (namespace, key, field_type) in CUSTOM_FIELD_MAP.items():
        value = doc.get(erpnext_field)
        if value:  # skip empty/null fields
            metafields.append({
                "namespace": namespace,
                "key": key,
                "value": str(value),
                "type": field_type,
            })

    return metafields


def push_metafields(settings, shopify_product_id, metafields):
    """
    Calls the Shopify REST API to upsert metafields on a product.
    Uses the /products/{id}/metafields.json endpoint.
    """
    shop_url = settings.shopify_url.rstrip("/")  # e.g. your-store.myshopify.com
    api_key = settings.shared_secret
    password = settings.password  # Admin API access token

    base_url = f"https://{shop_url}/admin/api/2024-01/products/{shopify_product_id}/metafields.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": password,
    }

    for metafield in metafields:
        payload = {"metafield": metafield}
        try:
            response = requests.post(base_url, json=payload, headers=headers)
            if response.status_code not in (200, 201):
                frappe.log_error(
                    f"ecommerce_ext: Failed to push metafield '{metafield['key']}' "
                    f"for product {shopify_product_id}. "
                    f"Response: {response.status_code} - {response.text}"
                )
        except Exception as e:
            frappe.log_error(f"ecommerce_ext: Exception pushing metafield - {str(e)}")