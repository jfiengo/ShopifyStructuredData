# tests/performance/test_performance.py
"""
Performance tests for schema generation
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from src.core.config import SchemaConfig
from src.core.generator import SchemaGenerator

class TestPerformance:
    """Performance tests"""
    
    @patch('src.core.shopify_client.requests.Session')
    def test_large_product_set_performance(self, mock_session):
        """Test performance with large number of products"""
        # Mock responses for large dataset
        shop_response = Mock()
        shop_response.status_code = 200
        shop_response.headers = {'content-type': 'application/json'}
        shop_response.json.return_value = {
            'shop': {
                'id': 12345,
                'name': 'Performance Test Store',
                'currency': 'USD'
            }
        }
        shop_response.text = '{"shop": {"id": 12345, "name": "Performance Test Store", "currency": "USD"}}'
        
        # Create 100 mock products
        mock_products = []
        for i in range(100):
            mock_products.append({
                'id': i,
                'title': f'Product {i}',
                'body_html': f'<p>Description for product {i}</p>',
                'vendor': 'Test Vendor',
                'product_type': 'Test',
                'handle': f'product-{i}',
                'tags': ['test'],
                'images': [{'src': f'https://example.com/image{i}.jpg'}],
                'variants': [{
                    'id': i * 10,
                    'title': 'Default',
                    'price': '19.99',
                    'sku': f'SKU-{i}',
                    'inventory_quantity': 10
                }]
            })
        
        products_response = Mock()
        products_response.status_code = 200
        products_response.headers = {'content-type': 'application/json'}
        products_response.json.return_value = {'products': mock_products}
        products_response.text = '{"products": ' + json.dumps(mock_products) + '}'
        
        collections_response = Mock()
        collections_response.status_code = 200
        collections_response.headers = {'content-type': 'application/json'}
        collections_response.json.return_value = {'collections': []}
        collections_response.text = '{"collections": []}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = [shop_response, products_response, collections_response]
        
        # Mock the head method for pagination
        head_response = Mock()
        head_response.headers = {'Link': ''}  # No next page
        mock_session_instance.head.return_value = head_response
        
        mock_session.return_value = mock_session_instance
        
        # Test configuration
        config = SchemaConfig(
            shop_domain="performance-test",
            access_token="test-token",
            max_products=100,
            include_collections=False,
            include_faq=False  # Disable to focus on core performance
        )
        
        # Measure generation time
        start_time = time.time()
        generator = SchemaGenerator(config)
        schemas = generator.generate_complete_schema_package()
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Verify results
        assert schemas['total_products'] == 100
        assert len(schemas['products']) == 100
        
        # Performance assertions (adjust thresholds as needed)
        assert generation_time < 10.0  # Should complete in under 10 seconds
        
        # Calculate products per second
        products_per_second = 100 / generation_time
        assert products_per_second > 10  # Should process at least 10 products per second
        
        print(f"Generated schemas for 100 products in {generation_time:.2f}s ({products_per_second:.1f} products/sec)")
    
    def test_memory_usage_with_large_schemas(self):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large schema structure
        large_schemas = {
            'products': []
        }
        
        # Add 1000 product schemas
        for i in range(1000):
            product_schema = {
                'product_id': i,
                'title': f'Product {i}' * 10,  # Make strings longer
                'schemas': {
                    'product': {
                        '@context': 'https://schema.org/',
                        '@type': 'Product',
                        'name': f'Product {i}' * 10,
                        'description': f'Long description for product {i}' * 50,
                        'image': [f'https://example.com/image{j}.jpg' for j in range(10)],
                        'offers': [{
                            '@type': 'Offer',
                            'price': '19.99',
                            'priceCurrency': 'USD'
                        } for _ in range(5)]
                    }
                }
            }
            large_schemas['products'].append(product_schema)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.1f}MB for 1000 product schemas")