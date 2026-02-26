import frappe
from shopify.resources import Product, Metafield

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def upload_erpnext_item(doc, method=None):

    frappe.msgprint("Custom Shopify hook triggered")

    product_id = frappe.db.get_value(
        "Ecommerce Item",
        {
            "erpnext_item_code": doc.name,
            "integration": MODULE_NAME
        },
        "integration_item_code"
    )

    frappe.msgprint(f"Product ID found: {product_id}")

    if not product_id:
        return

    product = Product.find(product_id)

    namespace = "custom"
    key = "color"

    existing_metafields = product.metafields()

    existing = next(
        (mf for mf in existing_metafields
         if mf.namespace == namespace and mf.key == key),
        None
    )

    if doc.custom_color:
        if existing:
            existing.value = doc.custom_color
            existing.save()
        else:
            Metafield.create({
                "metafield": {
                    "namespace": namespace,
                    "key": key,
                    "value": doc.custom_color,
                    "type": "single_line_text_field",
                    "owner_id": product.id,
                    "owner_resource": "product"
                }
            })

    elif existing:
        existing.destroy()