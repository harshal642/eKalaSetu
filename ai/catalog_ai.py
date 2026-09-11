"""
catalog_ai.py
-------------
KalaSetu AI Catalog Assistant.

Prototype implementation:
- No external API
- No API key required
- Uses artisan answers
- Generates customer-friendly catalog information
- Generates a recommended target market
"""

from datetime import datetime


def _clean(value):
    if value is None:
        return ""

    return str(value).strip()


def _parse_cost(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_product_name(material, size, language):
    """
    Generate a simple product name from the artisan's material and size.
    """

    material = _clean(material)

    if language == "mr":

        if material:
            return f"{material} हस्तनिर्मित कलाकृती"

        return "हस्तनिर्मित कलाकृती"

    if language == "hi":

        if material:
            return f"{material} हस्तनिर्मित कलाकृति"

        return "हस्तनिर्मित कलाकृति"

    # English
    if material:
        return f"Handmade {material} Craft"

    return "Handmade Artisan Product"


def _build_description(
    material,
    size,
    making_time,
    language
):
    """
    Build a customer-friendly description.

    Making time is used as supporting information but is not
    required to be shown on the customer page.
    """

    material = _clean(material)
    size = _clean(size)
    making_time = _clean(making_time)

    if language == "mr":

        text = "ही एक सुंदर पारंपरिक हस्तनिर्मित कलाकृती आहे."

        if material:
            text += f" ही कलाकृती {material} वापरून तयार केली आहे."

        if size:
            text += f" आकारमान: {size}."

        text += " प्रत्येक वस्तू कारागिराच्या कौशल्याने आणि काळजीपूर्वक तयार केली जाते."

        return text

    if language == "hi":

        text = "यह एक सुंदर पारंपरिक हस्तनिर्मित कलाकृति है।"

        if material:
            text += f" यह कलाकृति {material} का उपयोग करके बनाई गई है।"

        if size:
            text += f" आकार: {size}।"

        text += " प्रत्येक वस्तु कारीगर के कौशल और मेहनत से सावधानीपूर्वक तैयार की जाती है।"

        return text

    # English

    text = (
        "This is a beautiful traditional handmade product."
    )

    if material:
        text += (
            f" It is carefully crafted using {material}."
        )

    if size:
        text += f" Size: {size}."

    text += (
        " Each piece is created with traditional "
        "craftsmanship and attention to detail."
    )

    return text


def _detect_target_market(
    material,
    size,
    language
):
    """
    Simple transparent market recommendation engine.
    """

    material_lower = _clean(material).lower()

    markets_en = []

    if any(
        word in material_lower
        for word in [
            "bamboo",
            "wood",
            "wooden",
            "cane"
        ]
    ):
        markets_en.extend([
            "Home Décor",
            "Gift Shops",
            "Handmade Marketplaces"
        ])

    elif any(
        word in material_lower
        for word in [
            "clay",
            "terracotta",
            "pottery",
            "mud"
        ]
    ):
        markets_en.extend([
            "Home Décor",
            "Art & Craft Stores",
            "Gift Shops"
        ])

    elif any(
        word in material_lower
        for word in [
            "cotton",
            "silk",
            "fabric",
            "cloth",
            "thread"
        ]
    ):
        markets_en.extend([
            "Fashion & Lifestyle",
            "Handloom Markets",
            "Online Marketplaces"
        ])

    elif any(
        word in material_lower
        for word in [
            "brass",
            "copper",
            "metal",
            "silver"
        ]
    ):
        markets_en.extend([
            "Premium Gift Shops",
            "Home Décor",
            "Art & Craft Stores"
        ])

    elif any(
        word in material_lower
        for word in [
            "paper",
            "paint",
            "colour",
            "color"
        ]
    ):
        markets_en.extend([
            "Art & Craft Stores",
            "Gift Shops",
            "Online Marketplaces"
        ])

    else:
        markets_en.extend([
            "Handmade Marketplaces",
            "Local Gift Shops",
            "Online Marketplaces"
        ])

    if language == "mr":

        translations = {
            "Home Décor": "घर सजावट",
            "Gift Shops": "भेटवस्तू दुकाने",
            "Handmade Marketplaces": "हस्तनिर्मित वस्तू बाजार",
            "Art & Craft Stores": "कला व हस्तकला दुकाने",
            "Fashion & Lifestyle": "फॅशन व जीवनशैली",
            "Handloom Markets": "हातमाग बाजार",
            "Online Marketplaces": "ऑनलाइन बाजारपेठ",
            "Premium Gift Shops": "प्रीमियम भेटवस्तू दुकाने",
        }

        return [
            translations.get(item, item)
            for item in markets_en
        ]

    if language == "hi":

        translations = {
            "Home Décor": "होम डेकोर",
            "Gift Shops": "उपहार दुकानें",
            "Handmade Marketplaces": "हस्तनिर्मित वस्तु बाजार",
            "Art & Craft Stores": "कला एवं हस्तशिल्प दुकानें",
            "Fashion & Lifestyle": "फैशन एवं लाइफस्टाइल",
            "Handloom Markets": "हथकरघा बाजार",
            "Online Marketplaces": "ऑनलाइन बाजार",
            "Premium Gift Shops": "प्रीमियम उपहार दुकानें",
        }

        return [
            translations.get(item, item)
            for item in markets_en
        ]

    return markets_en


def generate_catalog(
    product_data: dict,
    language: str = "en"
) -> dict:

    material = _clean(
        product_data.get("material")
    )

    making_time = _clean(
        product_data.get("making_time")
    )

    making_cost = _parse_cost(
        product_data.get("making_cost")
    )

    size = _clean(
        product_data.get("size")
    )

    name = _build_product_name(
        material,
        size,
        language
    )

    description = _build_description(
        material,
        size,
        making_time,
        language
    )

    target_market = _detect_target_market(
        material,
        size,
        language
    )

    return {

        "name": name,

        "description": description,

        "material": material,

        "size": size,

        "target_market": target_market,

        # Internal AI inputs
        "making_time": making_time,

        "making_cost": making_cost,

        "status": "draft",

        "generated_at":
            datetime.utcnow().isoformat(),
    }