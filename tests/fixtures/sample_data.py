# tests/fixtures/sample_data.py
"""
Sample data for testing
"""

SAMPLE_PRODUCT_COMPLEX = {
    "id": 987654321,
    "title": "Premium Wireless Headphones",
    "body_html": """
    <div class="product-description">
        <h2>Premium Audio Experience</h2>
        <p>Experience crystal-clear sound with our premium wireless headphones featuring:</p>
        <ul>
            <li>Active noise cancellation</li>
            <li>30-hour battery life</li>
            <li>Bluetooth 5.0 connectivity</li>
            <li>Comfortable over-ear design</li>
        </ul>
        <p><strong>Perfect for music lovers and professionals alike!</strong></p>
    </div>
    """,
    "vendor": "AudioTech",
    "product_type": "Electronics",
    "handle": "premium-wireless-headphones",
    "tags": ["audio", "wireless", "bluetooth", "noise-cancelling", "premium"],
    "images": [
        {
            "id": 111111111,
            "src": "https://example.com/headphones-black.jpg",
            "alt": "Black Premium Wireless Headphones"
        },
        {
            "id": 222222222,
            "src": "https://example.com/headphones-white.jpg", 
            "alt": "White Premium Wireless Headphones"
        }
    ],
    "variants": [
        {
            "id": 333333333,
            "title": "Black",
            "price": "199.99",
            "sku": "AUD-HP-001-BLK",
            "inventory_quantity": 25,
            "weight": 250,
            "weight_unit": "g"
        },
        {
            "id": 444444444,
            "title": "White", 
            "price": "199.99",
            "sku": "AUD-HP-001-WHT",
            "inventory_quantity": 15,
            "weight": 250,
            "weight_unit": "g"
        },
        {
            "id": 555555555,
            "title": "Silver",
            "price": "219.99", 
            "sku": "AUD-HP-001-SLV",
            "inventory_quantity": 0,
            "weight": 250,
            "weight_unit": "g"
        }
    ],
    "collections": [
        {"id": 777777777, "handle": "audio-equipment"},
        {"id": 888888888, "handle": "premium-electronics"}
    ],
    "metafields": [
        {
            "key": "warranty",
            "value": "2 years",
            "namespace": "product_specs"
        },
        {
            "key": "material",
            "value": "Premium plastic and metal",
            "namespace": "product_specs"
        }
    ]
}

SAMPLE_COLLECTION_COMPLEX = {
    "id": 777777777,
    "title": "Audio Equipment",
    "handle": "audio-equipment",
    "body_html": "<p>Discover our premium collection of audio equipment for the ultimate listening experience.</p>",
    "sort_order": "best-selling",
    "image": {
        "src": "https://example.com/audio-collection.jpg",
        "alt": "Audio Equipment Collection"
    }
}

INVALID_SCHEMAS_FOR_TESTING = {
    "invalid_product_missing_type": {
        "@context": "https://schema.org/",
        "name": "Test Product"
        # Missing @type
    },
    "invalid_product_wrong_type": {
        "@context": "https://schema.org/",
        "@type": "Organization",  # Wrong type
        "name": "Test Product"
    },
    "invalid_product_missing_required": {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Test Product"
        # Missing description, image, brand, offers
    },
    "invalid_offers": {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Test Product",
        "description": "Test description",
        "image": ["https://example.com/image.jpg"],
        "brand": {"@type": "Brand", "name": "Test Brand"},
        "offers": {
            "@type": "Offer"
            # Missing price, priceCurrency, availability
        }
    }
}