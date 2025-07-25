# tests/test_config.py
"""
Tests for configuration management
"""

import pytest
import tempfile
import os
import yaml
from core.config import SchemaConfig

class TestSchemaConfig:
    """Test SchemaConfig class"""
    
    def test_create_basic_config(self):
        """Test creating basic configuration"""
        config = SchemaConfig(
            shop_domain="test-shop",
            access_token="test-token"
        )
        
        assert config.shop_domain == "test-shop"
        assert config.access_token == "test-token"
        assert config.api_version == "2023-10"  # default
        assert config.max_products == 250  # default
        assert not config.enable_ai_features  # default
    
    def test_config_with_ai(self):
        """Test configuration with AI features"""
        config = SchemaConfig(
            shop_domain="test-shop",
            access_token="test-token",
            openai_api_key="test-openai-key",
            enable_ai_features=True
        )
        
        assert config.openai_api_key == "test-openai-key"
        assert config.enable_ai_features is True
    
    def test_base_url_property(self):
        """Test base URL property construction"""
        config = SchemaConfig(
            shop_domain="test-shop",
            access_token="test-token",
            api_version="2023-10"
        )
        
        expected_url = "https://test-shop.myshopify.com/admin/api/2023-10"
        assert config.base_url == expected_url
    
    def test_config_from_env(self):
        """Test loading configuration from environment variables"""
        # Set environment variables
        os.environ['SHOPIFY_SHOP_DOMAIN'] = 'env-test-shop'
        os.environ['SHOPIFY_ACCESS_TOKEN'] = 'env-test-token'
        os.environ['OPENAI_API_KEY'] = 'env-openai-key'
        os.environ['ENABLE_AI_FEATURES'] = 'true'
        os.environ['MAX_PRODUCTS'] = '50'
        
        try:
            config = SchemaConfig.from_env()
            
            assert config.shop_domain == 'env-test-shop'
            assert config.access_token == 'env-test-token'
            assert config.openai_api_key == 'env-openai-key'
            assert config.enable_ai_features is True
            assert config.max_products == 50
        
        finally:
            # Clean up environment variables
            for key in ['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN', 'OPENAI_API_KEY', 
                       'ENABLE_AI_FEATURES', 'MAX_PRODUCTS']:
                os.environ.pop(key, None)
    
    def test_config_to_yaml_file(self):
        """Test saving configuration to YAML file"""
        config = SchemaConfig(
            shop_domain="test-shop",
            access_token="test-token",
            enable_ai_features=True,
            max_products=100
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_file = f.name
        
        try:
            config.to_file(temp_file)
            
            # Verify file was created and has correct content
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data['shop_domain'] == 'test-shop'
            assert loaded_data['access_token'] == 'test-token'
            assert loaded_data['enable_ai_features'] is True
            assert loaded_data['max_products'] == 100
        
        finally:
            os.unlink(temp_file)
    
    def test_config_from_yaml_file(self):
        """Test loading configuration from YAML file"""
        config_data = {
            'shop_domain': 'yaml-test-shop',
            'access_token': 'yaml-test-token',
            'api_version': '2023-10',
            'enable_ai_features': False,
            'max_products': 75
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = SchemaConfig.from_file(temp_file)
            
            assert config.shop_domain == 'yaml-test-shop'
            assert config.access_token == 'yaml-test-token'
            assert config.api_version == '2023-10'
            assert config.enable_ai_features is False
            assert config.max_products == 75
        
        finally:
            os.unlink(temp_file)