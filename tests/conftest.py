# tests/conftest.py
"""
Pytest configuration and shared fixtures
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.config import SchemaConfig
from src.core.shopify_client import ShopifyClient
from src.core.generator import SchemaGenerator

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return SchemaConfig(
        shop_domain="test-store",
        access_token="test-token",
        api_version="2023-10",
        max_products=10,
        enable_ai_features=False,
        include_collections=True,
        include_faq=True
    )

@pytest.fixture
def sample_config_with_ai():
    """Sample configuration with AI enabled"""
    return SchemaConfig(
        shop_domain="test-store",
        access_token="test-token",
        openai_api_key="test-openai-key",
        enable_ai_features=True,
        max_products=10
    )

@pytest.fixture
def sample_shop_info():
    """Sample shop information from Shopify API"""
    return {
        "id": 12345,
        "name": "Test Store",
        "email": "test@example.com", 
        "domain": "test-store.myshopify.com",
        "currency": "USD",
        "country": "US",
        "address1": "123 Test St",
        "city": "Test City",
        "province": "Test State",
        "zip": "12345",
        "phone": "+1234567890"
    }

@pytest.fixture
def sample_product():
    """Sample product data from Shopify API"""
    return {
        "id": 123456789,
        "title": "Test Product",
        "body_html": "<p>This is a test product description.</p>",
        "vendor": "Test Vendor",
        "product_type": "Test Type",
        "handle": "test-product",
        "tags": ["test", "product", "sample"],
        "images": [
            {
                "id": 987654321,
                "src": "https://example.com/image1.jpg",
                "alt": "Test Product Image"
            }
        ],
        "variants": [
            {
                "id": 111111111,
                "title": "Default Title",
                "price": "29.99",
                "sku": "TEST-001",
                "inventory_quantity": 10,
                "weight": 100,
                "weight_unit": "g"
            }
        ],
        "collections": [
            {"id": 555555555, "handle": "test-collection"}
        ]
    }

@pytest.fixture
def sample_collection():
    """Sample collection data from Shopify API"""
    return {
        "id": 555555555,
        "title": "Test Collection",
        "handle": "test-collection",
        "body_html": "<p>Test collection description</p>",
        "sort_order": "best-selling"
    }

@pytest.fixture
def mock_shopify_client(sample_shop_info, sample_product, sample_collection):
    """Mock Shopify client for testing"""
    with patch('core.shopify_client.ShopifyClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_shop_info.return_value = sample_shop_info
        mock_client.get_products.return_value = iter([sample_product])
        mock_client.get_collections.return_value = [sample_collection]
        mock_client_class.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('ai.enhancer.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Enhanced description"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        yield mock_client

@pytest.fixture
def sample_schemas():
    """Sample generated schemas for testing"""
    return {
        "generated_at": "2024-01-01T00:00:00",
        "shop_domain": "test-store",
        "total_products": 1,
        "organization": {
            "@context": "https://schema.org",
            "@type": "Organization", 
            "name": "Test Store",
            "url": "https://test-store.myshopify.com"
        },
        "products": [
            {
                "product_id": 123456789,
                "title": "Test Product",
                "handle": "test-product",
                "schemas": {
                    "product": {
                        "@context": "https://schema.org/",
                        "@type": "Product",
                        "name": "Test Product",
                        "description": "This is a test product description.",
                        "image": ["https://example.com/image1.jpg"],
                        "brand": {
                            "@type": "Brand",
                            "name": "Test Vendor"
                        },
                        "offers": [
                            {
                                "@type": "Offer",
                                "price": "29.99",
                                "priceCurrency": "USD",
                                "availability": "https://schema.org/InStock"
                            }
                        ]
                    }
                }
            }
        ]
    }
