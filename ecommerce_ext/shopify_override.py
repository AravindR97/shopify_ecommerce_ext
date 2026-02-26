import frappe
from shopify.resources import Product, Metafield

# import original function
from ecommerce_integrations.ecommerce_integrations.shopify.product import (
    upload_erpnext_item as original_upload
)

from ecommerce_integrations.shopify.connection import temp_shopify_session
from ecommerce_integrations.shopify.constants import MODULE_NAME


@temp_shopify_session
def upload_erpnext_item(doc, method=None):

    original_upload(doc, method)

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

    metafields_to_sync = []

    if doc.custom_color:
        metafields_to_sync.append({
            "namespace": "custom",
            "key": "color",
            "value": doc.custom_color,
            "type": "single_line_text_field"
        })

    existing_metafields = product.metafields()

    for mf in metafields_to_sync:

        existing = next(
            (x for x in existing_metafields
             if x.namespace == mf["namespace"] and x.key == mf["key"]),
            None
        )

        if existing:
            existing.value = mf["value"]
            existing.save()
        else:
            Metafield.create({
                "metafield": {
                    "namespace": mf["namespace"],
                    "key": mf["key"],
                    "value": mf["value"],
                    "type": mf["type"],
                    "owner_id": product.id,
                    "owner_resource": "product"
                }
            })