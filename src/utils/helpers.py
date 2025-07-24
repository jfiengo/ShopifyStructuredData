# src/utils/helpers.py
"""
Utility functions for the schema generator
"""

import re
import html
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

def clean_html(html_content: str) -> str:
    """Clean HTML content to extract plain text"""
    if not html_content:
        return ""
    
    # Parse HTML and extract text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean up whitespace
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    return text.strip()

def generate_price_valid_until(months: int = 6) -> str:
    """Generate a price valid until date"""
    future_date = datetime.now() + timedelta(days=30 * months)
    return future_date.strftime('%Y-%m-%d')

def extract_numeric_value(text: str, pattern: str = r'(\d+(?:\.\d+)?)') -> Optional[float]:
    """Extract numeric value from text using regex"""
    if not text:
        return None
    
    match = re.search(pattern, str(text))
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None

def normalize_currency(currency_code: str) -> str:
    """Normalize currency code to standard format"""
    currency_map = {
        'usd': 'USD',
        'eur': 'EUR',
        'gbp': 'GBP',
        'cad': 'CAD',
        'aud': 'AUD',
        'jpy': 'JPY'
    }
    
    return currency_map.get(currency_code.lower(), currency_code.upper())

def extract_dimensions(text: str) -> Optional[Dict[str, Any]]:
    """Extract dimensions from product description"""
    if not text:
        return None
    
    # Common dimension patterns
    patterns = {
        'length': r'length[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm|in|inches?|ft|feet)',
        'width': r'width[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm|in|inches?|ft|feet)',
        'height': r'height[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm|in|inches?|ft|feet)',
        'depth': r'depth[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm|in|inches?|ft|feet)',
        'diameter': r'diameter[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm|in|inches?|ft|feet)'
    }
    
    dimensions = {}
    text_lower = text.lower()
    
    for dimension, pattern in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            value, unit = match.groups()
            dimensions[dimension] = {
                'value': float(value),
                'unit': unit
            }
    
    return dimensions if dimensions else None

def extract_weight(text: str) -> Optional[Dict[str, Any]]:
    """Extract weight from product description"""
    if not text:
        return None
    
    # Weight patterns
    pattern = r'weight[:\s]*(\d+(?:\.\d+)?)\s*(g|kg|lb|lbs|oz|ounces?|pounds?)'
    
    match = re.search(pattern, text.lower())
    if match:
        value, unit = match.groups()
        return {
            'value': float(value),
            'unit': unit
        }
    
    return None

def extract_materials(text: str) -> List[str]:
    """Extract materials from product description"""
    if not text:
        return []
    
    # Common materials
    materials = [
        'cotton', 'polyester', 'silk', 'wool', 'linen', 'leather', 'suede',
        'denim', 'cashmere', 'bamboo', 'organic cotton', 'recycled polyester',
        'stainless steel', 'aluminum', 'brass', 'copper', 'silver', 'gold',
        'plastic', 'wood', 'bamboo', 'ceramic', 'glass', 'rubber'
    ]
    
    found_materials = []
    text_lower = text.lower()
    
    for material in materials:
        if material in text_lower:
            found_materials.append(material.title())
    
    return found_materials

def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL"""
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def truncate_text(text: str, max_length: int = 160, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if not text or len(text) <= max_length:
        return text
    
    # Try to cut at word boundary
    if ' ' in text[:max_length]:
        truncated = text[:max_length].rsplit(' ', 1)[0]
    else:
        truncated = text[:max_length]
    
    return truncated + suffix

def format_price(price: str, currency: str = 'USD') -> str:
    """Format price string consistently"""
    try:
        # Extract numeric value
        numeric_price = extract_numeric_value(price)
        if numeric_price is not None:
            return f"{numeric_price:.2f}"
    except:
        pass
    
    return str(price)

def generate_sku(product_title: str, variant_title: str = None, fallback: str = None) -> str:
    """Generate SKU from product and variant titles"""
    # Start with product title
    sku_parts = [product_title]
    
    if variant_title and variant_title != product_title:
        sku_parts.append(variant_title)
    
    # Clean and format
    sku = '-'.join(sku_parts)
    sku = re.sub(r'[^a-zA-Z0-9\-]', '', sku.replace(' ', '-'))
    sku = re.sub(r'-+', '-', sku).strip('-').upper()
    
    return sku if sku else fallback or 'UNKNOWN-SKU'