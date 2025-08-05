# tests/test_validation.py
"""
Tests for schema validation
"""

import pytest
from unittest.mock import Mock, patch
from src.validation.schema_validator import SchemaValidator

class TestSchemaValidator:
    """Test SchemaValidator class"""
    
    def test_validator_initialization(self):
        """Test validator initialization"""
        validator = SchemaValidator()
        assert validator.session is not None
    
    def test_validate_product_schema_valid(self):
        """Test validation of valid product schema"""
        validator = SchemaValidator()
        
        valid_product_schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Test Product",
            "description": "Test description",
            "image": ["https://example.com/image.jpg"],
            "brand": {
                "@type": "Brand",
                "name": "Test Brand"
            },
            "offers": {
                "@type": "Offer",
                "price": "29.99",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        }
        
        result = validator.validate_product_schema(valid_product_schema)
        
        assert result['valid'] is True
        assert result['schema_type'] == 'Product'
        assert len(result['errors']) == 0
    
    def test_validate_product_schema_invalid(self):
        """Test validation of invalid product schema"""
        validator = SchemaValidator()
        
        invalid_product_schema = {
            "@context": "https://schema.org/",
            "@type": "Product"
            # Missing required fields: name, offers
        }
        
        result = validator.validate_product_schema(invalid_product_schema)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('name' in error for error in result['errors'])
        assert any('offers' in error for error in result['errors'])
    
    def test_validate_organization_schema_valid(self):
        """Test validation of valid organization schema"""
        validator = SchemaValidator()
        
        valid_org_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test Organization",
            "url": "https://example.com"
        }
        
        result = validator.validate_organization_schema(valid_org_schema)
        
        assert result['valid'] is True
        assert result['schema_type'] == 'Organization'
        assert len(result['errors']) == 0
    
    def test_validate_breadcrumb_schema_valid(self):
        """Test validation of valid breadcrumb schema"""
        validator = SchemaValidator()
        
        valid_breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": "https://example.com"
                },
                {
                    "@type": "ListItem", 
                    "position": 2,
                    "name": "Products",
                    "item": "https://example.com/products"
                }
            ]
        }
        
        result = validator.validate_breadcrumb_schema(valid_breadcrumb_schema)
        
        assert result['valid'] is True
        assert result['schema_type'] == 'BreadcrumbList'
        assert len(result['errors']) == 0
    
    def test_validate_faq_schema_valid(self):
        """Test validation of valid FAQ schema"""
        validator = SchemaValidator()
        
        valid_faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "What is this product?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "This is a test product."
                    }
                }
            ]
        }
        
        result = validator.validate_faq_schema(valid_faq_schema)
        
        assert result['valid'] is True
        assert result['schema_type'] == 'FAQPage'
        assert len(result['errors']) == 0
    
    @patch('validation.schema_validator.requests.Session.get')
    def test_analyze_existing_structured_data(self, mock_get):
        """Test analysis of existing structured data"""
        validator = SchemaValidator()
        
        # Mock HTML response with JSON-LD
        html_content = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": "Test Product"
            }
            </script>
        </head>
        <body>Content</body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode()
        mock_get.return_value = mock_response
        
        result = validator.analyze_existing_structured_data("https://example.com/product")
        
        assert result['found_schemas'] == 1
        assert result['has_product_schema'] is True
        assert len(result['schemas']) == 1
        assert result['schemas'][0]['@type'] == 'Product'
    
    def test_validate_against_google_requirements(self):
        """Test Google Rich Results validation"""
        validator = SchemaValidator()
        
        # Product schema missing some Google requirements
        product_schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Test Product"
            # Missing offers (required by Google)
        }
        
        result = validator.validate_against_google_requirements(product_schema)
        
        assert result['eligible_for_rich_results'] is False
        assert len(result['errors']) > 0
        assert any('offers' in error for error in result['errors'])