# src/utils/constants.py
"""
Constants and mappings for the schema generator
"""

# Product category mapping
CATEGORY_MAPPING = {
    'apparel': 'Apparel & Accessories',
    'clothing': 'Apparel & Accessories',
    'shoes': 'Apparel & Accessories',
    'accessories': 'Apparel & Accessories',
    'jewelry': 'Apparel & Accessories',
    'bags': 'Apparel & Accessories',
    'electronics': 'Electronics',
    'computers': 'Electronics',
    'phones': 'Electronics',
    'tablets': 'Electronics',
    'audio': 'Electronics',
    'cameras': 'Electronics',
    'home': 'Home & Garden',
    'furniture': 'Home & Garden',
    'decor': 'Home & Garden',
    'kitchen': 'Home & Garden',
    'appliances': 'Home & Garden',
    'garden': 'Home & Garden',
    'beauty': 'Health & Beauty',
    'cosmetics': 'Health & Beauty',
    'skincare': 'Health & Beauty',
    'health': 'Health & Beauty',
    'wellness': 'Health & Beauty',
    'supplements': 'Health & Beauty',
    'books': 'Media',
    'movies': 'Media',
    'music': 'Media',
    'games': 'Media',
    'food': 'Food & Beverages',
    'beverages': 'Food & Beverages',
    'drinks': 'Food & Beverages',
    'snacks': 'Food & Beverages',
    'sports': 'Sports & Recreation',
    'fitness': 'Sports & Recreation',
    'outdoor': 'Sports & Recreation',
    'recreation': 'Sports & Recreation',
    'automotive': 'Automotive',
    'car': 'Automotive',
    'motorcycle': 'Automotive',
    'parts': 'Automotive',
    'toys': 'Toys & Games',
    'games': 'Toys & Games',
    'baby': 'Baby & Kids',
    'kids': 'Baby & Kids',
    'children': 'Baby & Kids',
    'pet': 'Pet Supplies',
    'pets': 'Pet Supplies',
    'office': 'Office & Business',
    'business': 'Office & Business',
    'industrial': 'Industrial & Scientific'
}

# Required fields for different schema types
REQUIRED_PRODUCT_FIELDS = [
    'name',
    'description',
    'image',
    'offers',
    'brand'
]

REQUIRED_ORGANIZATION_FIELDS = [
    'name',
    'url'
]

REQUIRED_OFFER_FIELDS = [
    'price',
    'priceCurrency',
    'availability'
]

# Schema.org types
SCHEMA_TYPES = {
    'PRODUCT': 'Product',
    'ORGANIZATION': 'Organization',
    'BREADCRUMB': 'BreadcrumbList',
    'FAQ': 'FAQPage',
    'REVIEW': 'Review',
    'AGGREGATE_RATING': 'AggregateRating',
    'OFFER': 'Offer',
    'BRAND': 'Brand'
}

# Availability mappings
AVAILABILITY_MAPPING = {
    'in_stock': 'https://schema.org/InStock',
    'out_of_stock': 'https://schema.org/OutOfStock',
    'preorder': 'https://schema.org/PreOrder',
    'backorder': 'https://schema.org/BackOrder',
    'discontinued': 'https://schema.org/Discontinued'
}

# Currency codes
SUPPORTED_CURRENCIES = [
    'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'SEK', 'NOK', 'DKK',
    'PLN', 'CZK', 'HUF', 'BGN', 'RON', 'HRK', 'RUB', 'CNY', 'INR', 'KRW',
    'SGD', 'HKD', 'MXN', 'BRL', 'ARS', 'CLP', 'COP', 'PEN', 'ZAR', 'NZD'
]

# Review platform indicators
REVIEW_PLATFORM_INDICATORS = {
    'yotpo': [
        'yotpo.com',
        'staticw2.yotpo.com',
        'yotpo-widget',
        'yotpo_reviews'
    ],
    'judgeme': [
        'judge.me',
        'judgeme_reviews',
        'judgeme-widget'
    ],
    'stamped': [
        'stamped.io',
        'stamped-reviews',
        'stamped-widget'
    ],
    'loox': [
        'loox.app',
        'loox-reviews',
        'loox-widget'
    ],
    'reviews_io': [
        'reviews.io',
        'reviews-io-widget'
    ]
}

# AI prompt templates
AI_PROMPTS = {
    'DESCRIPTION_ENHANCEMENT': """
    Improve this product description for SEO and user experience:
    
    Original: {description}
    Product: {title}
    Category: {category}
    
    Requirements:
    - 150-200 words
    - Include relevant keywords naturally
    - Focus on benefits and features
    - Include call-to-action
    - Optimize for search intent
    
    Return only the improved description.
    """,
    
    'FAQ_GENERATION': """
    Generate 3-5 frequently asked questions for this product:
    
    Product: {title}
    Description: {description}
    Category: {category}
    
    Return as JSON: {{"questions": [{{"question": "...", "answer": "..."}}]}}
    """,
    
    'KEYWORD_EXTRACTION': """
    Extract 10-15 relevant SEO keywords for this product:
    
    Product: {title}
    Description: {description}
    Category: {category}
    
    Return as comma-separated list focusing on:
    - Product-specific terms
    - Category keywords
    - Feature-based keywords
    - Use case keywords
    """,
    
    'ATTRIBUTE_EXTRACTION': """
    Extract structured attributes from this product description:
    
    {description}
    
    Return as JSON with these possible attributes:
    {{
        "material": "",
        "color": [],
        "size": [],
        "weight": "",
        "dimensions": "",
        "care_instructions": "",
        "features": [],
        "compatibility": [],
        "warranty": ""
    }}
    
    Only include attributes explicitly mentioned.
    """
}

# Google Rich Results requirements
GOOGLE_RICH_RESULTS_REQUIREMENTS = {
    'Product': {
        'required': ['name', 'image', 'offers'],
        'recommended': ['description', 'brand', 'sku', 'aggregateRating'],
        'image_requirements': {
            'min_width': 160,
            'min_height': 90,
            'aspect_ratio': '16:9, 4:3, or 1:1'
        }
    },
    'Review': {
        'required': ['reviewBody', 'author', 'reviewRating'],
        'recommended': ['datePublished', 'publisher']
    },
    'FAQ': {
        'required': ['mainEntity'],
        'recommended': ['name']
    }
}

# Default values
DEFAULT_VALUES = {
    'PRICE_VALID_MONTHS': 6,
    'MAX_DESCRIPTION_LENGTH': 5000,
    'MAX_FAQ_QUESTIONS': 10,
    'MAX_KEYWORDS': 15,
    'DEFAULT_CURRENCY': 'USD',
    'DEFAULT_COUNTRY': 'US'
}