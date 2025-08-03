# tests/test_shopify_client.py
"""
Tests for Shopify API client
"""

import pytest
import requests
import json
from unittest.mock import Mock, patch
from src.core.shopify_client import ShopifyClient, ShopifyAPIError

class TestShopifyClient:
    """Test ShopifyClient class"""
    
    def test_client_initialization(self, sample_config):
        """Test client initialization"""
        client = ShopifyClient(sample_config)
        
        assert client.config == sample_config
        assert client.session.headers['X-Shopify-Access-Token'] == sample_config.access_token
        assert client.session.headers['Content-Type'] == 'application/json'
        assert client.rate_limit_remaining == 40
    
    @patch('src.core.shopify_client.requests.Session')
    def test_successful_api_request(self, mock_session, sample_config):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-type': 'application/json',
            'X-Shopify-Shop-Api-Call-Limit': '1/40'
        }
        mock_response.json.return_value = {'shop': {'name': 'Test Shop'}}
        mock_response.text = '{"shop": {"name": "Test Shop"}}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = ShopifyClient(sample_config)
        result = client._make_request('GET', '/shop.json')
        
        assert result == {'shop': {'name': 'Test Shop'}}
        mock_session_instance.request.assert_called_once()
    
    @patch('src.core.shopify_client.requests.Session')
    def test_rate_limit_handling(self, mock_session, sample_config):
        """Test rate limit handling"""
        # Mock rate limited response followed by successful response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        rate_limit_response.text = 'Rate limit exceeded'
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.headers = {
            'content-type': 'application/json',
            'X-Shopify-Shop-Api-Call-Limit': '39/40'
        }
        success_response.json.return_value = {'shop': {'name': 'Test Shop'}}
        success_response.text = '{"shop": {"name": "Test Shop"}}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = [rate_limit_response, success_response]
        mock_session.return_value = mock_session_instance
        
        with patch('time.sleep') as mock_sleep:
            client = ShopifyClient(sample_config)
            result = client._make_request('GET', '/shop.json')
        
        assert result == {'shop': {'name': 'Test Shop'}}
        # Should be called twice: once for 429 retry, once for approaching rate limit
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list == [((1,),), ((2,),)]
        assert mock_session_instance.request.call_count == 2
    
    @patch('src.core.shopify_client.requests.Session')
    def test_non_json_response_error(self, mock_session, sample_config):
        """Test error handling for non-JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = '<html>Password protected</html>'
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = ShopifyClient(sample_config)
        
        with pytest.raises(ShopifyAPIError, match="Non-JSON response"):
            client._make_request('GET', '/shop.json')
    
    @patch('src.core.shopify_client.requests.Session')
    def test_get_shop_info(self, mock_session, sample_config, sample_shop_info):
        """Test get_shop_info method"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'shop': sample_shop_info}
        mock_response.text = '{"shop": ' + json.dumps(sample_shop_info) + '}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = ShopifyClient(sample_config)
        shop_info = client.get_shop_info()
        
        assert shop_info == sample_shop_info
        mock_session_instance.request.assert_called_once()
        args, kwargs = mock_session_instance.request.call_args
        assert args[0] == 'GET'
        assert '/shop.json' in args[1]
    
    @patch('src.core.shopify_client.requests.Session')
    def test_get_products_pagination(self, mock_session, sample_config, sample_product):
        """Test product pagination"""
        # First page response
        first_response = Mock()
        first_response.status_code = 200
        first_response.headers = {
            'content-type': 'application/json',
            'Link': '</admin/api/2023-10/products.json?page_info=next123>; rel="next"'
        }
        first_response.json.return_value = {'products': [sample_product]}
        first_response.text = '{"products": [' + json.dumps(sample_product) + ']}'
        
        # Second page response (with another product)
        second_response = Mock()
        second_response.status_code = 200
        second_response.headers = {'content-type': 'application/json'}
        second_response.json.return_value = {'products': [sample_product]}  # Same product for simplicity
        second_response.text = '{"products": [' + json.dumps(sample_product) + ']}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = [first_response, second_response]
        
        # Mock the head method for pagination - first call returns next link, second call returns no link
        first_head_response = Mock()
        first_head_response.headers = {'Link': '</admin/api/2023-10/products.json?page_info=next123>; rel="next"'}
        
        second_head_response = Mock()
        second_head_response.headers = {'Link': ''}  # No next page
        
        mock_session_instance.head.side_effect = [first_head_response, second_head_response]
        
        mock_session.return_value = mock_session_instance
        
        client = ShopifyClient(sample_config)
        products = list(client.get_products(limit=5))
        
        assert len(products) == 2
        assert products[0] == sample_product
        assert products[1] == sample_product
        assert mock_session_instance.request.call_count == 2
    
    def test_parse_next_link(self, sample_config):
        """Test parsing of pagination links"""
        client = ShopifyClient(sample_config)
        
        # Test with next link
        link_header = '</admin/api/2023-10/products.json?page_info=abc123>; rel="next"'
        next_link = client._parse_next_link(link_header)
        assert 'page_info=abc123' in next_link
        
        # Test with no next link
        link_header = '</admin/api/2023-10/products.json?page_info=abc123>; rel="prev"'
        next_link = client._parse_next_link(link_header)
        assert next_link is None
        
        # Test with empty header
        next_link = client._parse_next_link('')
        assert next_link is None