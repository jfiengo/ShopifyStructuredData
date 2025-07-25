# tests/test_utils.py
"""
Tests for utility functions
"""

import pytest
from utils.helpers import (
    clean_html, generate_price_valid_until, extract_numeric_value,
    normalize_currency, truncate_text, format_price
)

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_clean_html(self):
        """Test HTML cleaning function"""
        html_input = "<p>This is <strong>bold</strong> text with <em>emphasis</em>.</p>"
        expected_output = "This is bold text with emphasis."
        
        result = clean_html(html_input)
        assert result == expected_output
    
    def test_clean_html_with_complex_markup(self):
        """Test HTML cleaning with complex markup"""
        html_input = """
        <div class="product-description">
            <h2>Product Features</h2>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
            </ul>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
        </div>
        """
        
        result = clean_html(html_input)
        
        # Should remove all HTML tags and scripts/styles
        assert '<' not in result
        assert '>' not in result
        assert 'alert' not in result
        assert 'body { color: red; }' not in result
        assert 'Product Features' in result
        assert 'Feature 1' in result
    
    def test_generate_price_valid_until(self):
        """Test price valid until date generation"""
        from datetime import datetime, timedelta
        
        # Test default (6 months)
        result = generate_price_valid_until()
        expected = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        assert result == expected
        
        # Test custom months
        result = generate_price_valid_until(months=3)
        expected = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        assert result == expected
    
    def test_extract_numeric_value(self):
        """Test numeric value extraction"""
        assert extract_numeric_value("29.99") == 29.99
        assert extract_numeric_value("Price: $49.95") == 49.95
        assert extract_numeric_value("Weight: 2.5kg") == 2.5
        assert extract_numeric_value("No numbers here") is None
        assert extract_numeric_value("") is None
    
    def test_normalize_currency(self):
        """Test currency code normalization"""
        assert normalize_currency("usd") == "USD"
        assert normalize_currency("EUR") == "EUR"
        assert normalize_currency("gbp") == "GBP"
        assert normalize_currency("unknown") == "UNKNOWN"
    
    def test_truncate_text(self):
        """Test text truncation"""
        long_text = "This is a very long text that needs to be truncated because it exceeds the maximum length."
        
        result = truncate_text(long_text, max_length=20)
        assert len(result) <= 23  # 20 + "..." = 23
        assert result.endswith("...")
        
        short_text = "Short text"
        result = truncate_text(short_text, max_length=20)
        assert result == short_text  # Should not be truncated
    
    def test_format_price(self):
        """Test price formatting"""
        assert format_price("29.99") == "29.99"
        assert format_price("$29.99") == "29.99"
        assert format_price("29") == "29.00"
        assert format_price("invalid") == "invalid"