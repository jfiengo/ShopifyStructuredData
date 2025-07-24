# src/core/shopify_client.py
"""
Shopify API client with rate limiting and error handling
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Generator
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ShopifyAPIError(Exception):
    """Custom exception for Shopify API errors"""
    pass

class ShopifyClient:
    """Shopify API client with built-in rate limiting and pagination"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'X-Shopify-Access-Token': config.access_token,
            'Content-Type': 'application/json'
        })
        self.rate_limit_remaining = 40  # Shopify's bucket size
        self.rate_limit_reset_time = time.time()
    
    def _handle_rate_limit(self, response):
        """Handle Shopify's leaky bucket rate limiting"""
        if 'X-Shopify-Shop-Api-Call-Limit' in response.headers:
            current, limit = map(int, response.headers['X-Shopify-Shop-Api-Call-Limit'].split('/'))
            self.rate_limit_remaining = limit - current
            
            # If we're close to the limit, wait a bit
            if self.rate_limit_remaining < 5:
                logger.warning("Approaching rate limit, waiting 2 seconds...")
                time.sleep(2)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the Shopify API with error handling"""
        url = urljoin(self.config.base_url, endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            self._handle_rate_limit(response)
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Shopify API request failed: {e}")
            raise ShopifyAPIError(f"API request failed: {e}")
    
    def get_shop_info(self) -> Dict:
        """Get shop information"""
        return self._make_request('GET', '/shop.json').get('shop', {})
    
    def get_products(self, limit: int = 250) -> Generator[Dict, None, None]:
        """Get products with pagination"""
        params = {'limit': min(limit, 250)}
        endpoint = '/products.json'
        
        while endpoint and limit > 0:
            response = self._make_request('GET', endpoint, params=params)
            products = response.get('products', [])
            
            for product in products[:limit]:
                yield product
                limit -= 1
                if limit <= 0:
                    return
            
            # Handle pagination
            link_header = self.session.head(urljoin(self.config.base_url, endpoint)).headers.get('Link', '')
            next_endpoint = self._parse_next_link(link_header)
            endpoint = next_endpoint
            params = {}  # Clear params for subsequent requests
    
    def get_collections(self) -> List[Dict]:
        """Get all collections"""
        return self._make_request('GET', '/collections.json').get('collections', [])
    
    def get_product_metafields(self, product_id: int) -> List[Dict]:
        """Get metafields for a specific product"""
        endpoint = f'/products/{product_id}/metafields.json'
        return self._make_request('GET', endpoint).get('metafields', [])
    
    def _parse_next_link(self, link_header: str) -> Optional[str]:
        """Parse pagination link from Link header"""
        if not link_header:
            return None
        
        import re
        match = re.search(r'<([^>]+)>; rel="next"', link_header)
        if match:
            # Extract just the path from the full URL
            full_url = match.group(1)
            return full_url.split('/admin/api/')[1] if '/admin/api/' in full_url else None
        return None