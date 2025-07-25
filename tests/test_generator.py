# tests/test_generator.py
"""
Tests for schema generator
"""

import pytest
from unittest.mock import Mock, patch
from src.core.generator import SchemaGenerator

class TestSchemaGenerator:
    """Test SchemaGenerator class"""
    
    def test_generator_initialization(self, sample_config):
        """Test generator initialization"""
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            
            assert generator.config == sample_config
            assert generator.ai_enhancer is None
            assert generator.review_integrator is None
    
    def test_generator_with_ai_enhancer(self, sample_config_with_ai):
        """Test generator with AI enhancer"""
        mock_ai_enhancer = Mock()
        
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config_with_ai, ai_enhancer=mock_ai_enhancer)
            
            assert generator.ai_enhancer == mock_ai_enhancer
    
    def test_generate_product_schema(self, sample_config, sample_product, sample_shop_info):
        """Test product schema generation"""
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            
            schema = generator.generate_product_schema(sample_product, sample_shop_info)
            
            assert schema['@context'] == "https://schema.org/"
            assert schema['@type'] == "Product"
            assert schema['name'] == sample_product['title']
            assert schema['description'] == "This is a test product description."
            assert schema['image'] == ["https://example.com/image1.jpg"]
            assert schema['brand']['name'] == sample_product['vendor']
            assert len(schema['offers']) == 1
            assert schema['offers'][0]['price'] == "29.99"
    
    def test_generate_organization_schema(self, sample_config, sample_shop_info):
        """Test organization schema generation"""
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            
            schema = generator.generate_organization_schema(sample_shop_info)
            
            assert schema['@context'] == "https://schema.org"
            assert schema['@type'] == "Organization"
            assert schema['name'] == sample_shop_info['name']
            assert schema['url'] == f"https://{sample_shop_info['domain']}"
            assert 'contactPoint' in schema
            assert 'address' in schema
    
    def test_generate_breadcrumb_schema(self, sample_config, sample_product, sample_collection):
        """Test breadcrumb schema generation"""
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            
            collections = [sample_collection]
            schema = generator.generate_breadcrumb_schema(sample_product, collections)
            
            assert schema['@context'] == "https://schema.org"
            assert schema['@type'] == "BreadcrumbList"
            assert len(schema['itemListElement']) >= 2  # Home + Product (+ Collection if matched)
            
            # Check home breadcrumb
            home_item = schema['itemListElement'][0]
            assert home_item['@type'] == "ListItem"
            assert home_item['position'] == 1
            assert home_item['name'] == "Home"
    
    def test_generate_offers_with_multiple_variants(self, sample_config, sample_shop_info):
        """Test offer generation with multiple variants"""
        variants = [
            {
                "id": 111,
                "title": "Small",
                "price": "19.99",
                "sku": "TEST-S",
                "inventory_quantity": 5
            },
            {
                "id": 222,
                "title": "Large", 
                "price": "29.99",
                "sku": "TEST-L",
                "inventory_quantity": 0
            }
        ]
        
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            offers = generator._generate_offers(variants, sample_shop_info)
            
            assert len(offers) == 2
            
            # Check first offer (in stock)
            assert offers[0]['price'] == "19.99"
            assert offers[0]['availability'] == "https://schema.org/InStock"
            assert offers[0]['sku'] == "TEST-S"
            
            # Check second offer (out of stock)
            assert offers[1]['price'] == "29.99"
            assert offers[1]['availability'] == "https://schema.org/OutOfStock"
            assert offers[1]['sku'] == "TEST-L"
    
    def test_categorize_product_basic(self, sample_config):
        """Test basic product categorization"""
        with patch('core.generator.ShopifyClient'):
            generator = SchemaGenerator(sample_config)
            
            # Test clothing category
            product = {
                'product_type': 'clothing',
                'tags': ['shirt', 'cotton']
            }
            category = generator._categorize_product(product)
            assert category == 'Apparel & Accessories'
            
            # Test electronics category
            product = {
                'product_type': 'electronics',
                'tags': ['phone', 'mobile']
            }
            category = generator._categorize_product(product)
            assert category == 'Electronics'
            
            # Test unknown category
            product = {
                'product_type': 'unknown',
                'tags': ['weird', 'unusual']
            }
            category = generator._categorize_product(product)
            assert category == 'Other'
    
    @patch('core.generator.ShopifyClient')
    def test_complete_schema_package_generation(self, mock_client_class, sample_config, 
                                              sample_shop_info, sample_product, sample_collection):
        """Test complete schema package generation"""
        # Setup mock client
        mock_client = Mock()
        mock_client.get_shop_info.return_value = sample_shop_info
        mock_client.get_products.return_value = iter([sample_product])
        mock_client.get_collections.return_value = [sample_collection]
        mock_client_class.return_value = mock_client
        
        generator = SchemaGenerator(sample_config)
        schemas = generator.generate_complete_schema_package()
        
        # Verify structure
        assert 'generated_at' in schemas
        assert schemas['shop_domain'] == sample_config.shop_domain
        assert schemas['total_products'] == 1
        assert 'organization' in schemas
        assert 'products' in schemas
        assert 'collections' in schemas
        
        # Verify organization schema
        org_schema = schemas['organization']
        assert org_schema['@type'] == 'Organization'
        assert org_schema['name'] == sample_shop_info['name']
        
        # Verify product schemas
        assert len(schemas['products']) == 1
        product_package = schemas['products'][0]
        assert product_package['product_id'] == sample_product['id']
        assert product_package['title'] == sample_product['title']
        assert 'product' in product_package['schemas']
        assert 'breadcrumb' in product_package['schemas']
        
        if sample_config.include_faq:
            assert 'faq' in product_package['schemas']