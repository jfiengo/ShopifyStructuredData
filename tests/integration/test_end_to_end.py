# tests/integration/test_end_to_end.py
"""
End-to-end integration tests
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch
from src.core.config import SchemaConfig
from src.core.generator import SchemaGenerator

class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @patch('src.core.shopify_client.requests.Session')
    def test_complete_schema_generation_flow(self, mock_session, sample_shop_info, sample_product):
        """Test complete schema generation flow"""
        # Mock API responses
        shop_response = Mock()
        shop_response.status_code = 200
        shop_response.headers = {'content-type': 'application/json'}
        shop_response.json.return_value = {'shop': sample_shop_info}
        shop_response.text = '{"shop": ' + json.dumps(sample_shop_info) + '}'
        
        products_response = Mock()
        products_response.status_code = 200
        products_response.headers = {'content-type': 'application/json'}
        products_response.json.return_value = {'products': [sample_product]}
        products_response.text = '{"products": [' + json.dumps(sample_product) + ']}'
        
        collections_response = Mock()
        collections_response.status_code = 200
        collections_response.headers = {'content-type': 'application/json'}
        collections_response.json.return_value = {'collections': []}
        collections_response.text = '{"collections": []}'
        
        mock_session_instance = Mock()
        
        # Create a function to return responses based on the endpoint being called
        def mock_request_side_effect(method, url, **kwargs):
            if 'shop.json' in url:
                return shop_response
            elif 'products.json' in url:
                return products_response
            elif 'collections.json' in url or 'custom_collections.json' in url or 'smart_collections.json' in url:
                return collections_response
            else:
                # Default response for any other endpoints
                default_response = Mock()
                default_response.status_code = 200
                default_response.headers = {'content-type': 'application/json'}
                default_response.json.return_value = {}
                default_response.text = '{}'
                return default_response
        
        mock_session_instance.request.side_effect = mock_request_side_effect
        
        # Mock the head method for pagination
        head_response = Mock()
        head_response.headers = {'Link': ''}  # No next page
        mock_session_instance.head.return_value = head_response
        
        mock_session.return_value = mock_session_instance
        
        # Create configuration
        config = SchemaConfig(
            shop_domain="test-store",
            access_token="test-token",
            max_products=1,
            include_collections=True,
            include_faq=True
        )
        
        # Generate schemas
        generator = SchemaGenerator(config)
        schemas = generator.generate_complete_schema_package()
        
        # Verify complete structure
        assert 'generated_at' in schemas
        assert schemas['shop_domain'] == 'test-store'
        assert schemas['total_products'] == 1
        assert 'organization' in schemas
        assert 'products' in schemas
        assert 'collections' in schemas
        
        # Verify organization schema
        org_schema = schemas['organization']
        assert org_schema['@type'] == 'Organization'
        assert org_schema['name'] == sample_shop_info['name']
        
        # Verify product schema
        product_package = schemas['products'][0]
        assert product_package['product_id'] == sample_product['id']
        assert 'product' in product_package['schemas']
        assert 'breadcrumb' in product_package['schemas']
        assert 'faq' in product_package['schemas']
        
        product_schema = product_package['schemas']['product']
        assert product_schema['@type'] == 'Product'
        assert product_schema['name'] == sample_product['title']
    
    def test_schema_validation_integration(self, sample_schemas):
        """Test integration between generation and validation"""
        from src.validation.schema_validator import SchemaValidator
        
        validator = SchemaValidator()
        
        # Validate organization schema
        org_result = validator.validate_organization_schema(sample_schemas['organization'])
        assert org_result['valid'] is True
        
        # Validate product schema
        product_schema = sample_schemas['products'][0]['schemas']['product']
        product_result = validator.validate_product_schema(product_schema)
        assert product_result['valid'] is True
    
    def test_file_export_and_import(self, sample_schemas):
        """Test exporting schemas to file and importing them back"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_schemas, f, indent=2)
            temp_file = f.name
        
        try:
            # Read back the file
            with open(temp_file, 'r') as f:
                loaded_schemas = json.load(f)
            
            # Verify data integrity
            assert loaded_schemas['shop_domain'] == sample_schemas['shop_domain']
            assert loaded_schemas['total_products'] == sample_schemas['total_products']
            assert len(loaded_schemas['products']) == len(sample_schemas['products'])
            
            # Verify schema structure is preserved
            org_schema = loaded_schemas['organization']
            assert org_schema['@type'] == 'Organization'
            
            product_schema = loaded_schemas['products'][0]['schemas']['product']
            assert product_schema['@type'] == 'Product'
        
        finally:
            import os
            os.unlink(temp_file)