# src/validation/schema_validator.py
"""
Schema validation logic for structured data
"""

import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import urljoin

from ..utils.constants import (
    REQUIRED_PRODUCT_FIELDS, 
    REQUIRED_ORGANIZATION_FIELDS,
    GOOGLE_RICH_RESULTS_REQUIREMENTS,
    SCHEMA_TYPES
)
from ..utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validate schemas against various standards and requirements"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def validate_product_schema(self, schema: Dict) -> Dict:
        """Validate a Product schema"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_type': 'Product'
        }
        
        # Check schema type
        if schema.get('@type') != 'Product':
            result['errors'].append("Schema type must be 'Product'")
            result['valid'] = False
        
        # Check required fields
        for field in REQUIRED_PRODUCT_FIELDS:
            if field not in schema or not schema[field]:
                result['errors'].append(f"Missing required field: {field}")
                result['valid'] = False
        
        # Validate offers
        if 'offers' in schema:
            offers_validation = self._validate_offers(schema['offers'])
            if not offers_validation['valid']:
                result['errors'].extend(offers_validation['errors'])
                result['valid'] = False
        
        # Validate images
        if 'image' in schema:
            image_validation = self._validate_images(schema['image'])
            if not image_validation['valid']:
                result['warnings'].extend(image_validation['warnings'])
        
        # Check for recommended fields
        recommended_fields = ['brand', 'sku', 'description', 'category']
        for field in recommended_fields:
            if field not in schema or not schema[field]:
                result['warnings'].append(f"Recommended field missing: {field}")
        
        return result
    
    def validate_organization_schema(self, schema: Dict) -> Dict:
        """Validate an Organization schema"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_type': 'Organization'
        }
        
        # Check schema type
        if schema.get('@type') != 'Organization':
            result['errors'].append("Schema type must be 'Organization'")
            result['valid'] = False
        
        # Check required fields
        for field in REQUIRED_ORGANIZATION_FIELDS:
            if field not in schema or not schema[field]:
                result['errors'].append(f"Missing required field: {field}")
                result['valid'] = False
        
        # Validate URL format
        if 'url' in schema:
            if not self._is_valid_url(schema['url']):
                result['errors'].append("Invalid URL format")
                result['valid'] = False
        
        # Check for recommended fields
        recommended_fields = ['description', 'contactPoint', 'address', 'sameAs']
        for field in recommended_fields:
            if field not in schema:
                result['warnings'].append(f"Recommended field missing: {field}")
        
        return result
    
    def validate_breadcrumb_schema(self, schema: Dict) -> Dict:
        """Validate a BreadcrumbList schema"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_type': 'BreadcrumbList'
        }
        
        # Check schema type
        if schema.get('@type') != 'BreadcrumbList':
            result['errors'].append("Schema type must be 'BreadcrumbList'")
            result['valid'] = False
        
        # Check itemListElement
        if 'itemListElement' not in schema:
            result['errors'].append("Missing required field: itemListElement")
            result['valid'] = False
        else:
            items = schema['itemListElement']
            if not isinstance(items, list) or len(items) == 0:
                result['errors'].append("itemListElement must be a non-empty list")
                result['valid'] = False
            else:
                # Validate each breadcrumb item
                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        result['errors'].append(f"Breadcrumb item {i+1} must be an object")
                        result['valid'] = False
                        continue
                    
                    if item.get('@type') != 'ListItem':
                        result['errors'].append(f"Breadcrumb item {i+1} must have @type 'ListItem'")
                        result['valid'] = False
                    
                    if 'position' not in item:
                        result['errors'].append(f"Breadcrumb item {i+1} missing position")
                        result['valid'] = False
                    
                    if 'name' not in item:
                        result['errors'].append(f"Breadcrumb item {i+1} missing name")
                        result['valid'] = False
        
        return result
    
    def validate_faq_schema(self, schema: Dict) -> Dict:
        """Validate an FAQ schema"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_type': 'FAQPage'
        }
        
        # Check schema type
        if schema.get('@type') != 'FAQPage':
            result['errors'].append("Schema type must be 'FAQPage'")
            result['valid'] = False
        
        # Check mainEntity
        if 'mainEntity' not in schema:
            result['errors'].append("Missing required field: mainEntity")
            result['valid'] = False
        else:
            entities = schema['mainEntity']
            if not isinstance(entities, list) or len(entities) == 0:
                result['errors'].append("mainEntity must be a non-empty list")
                result['valid'] = False
            else:
                # Validate each FAQ item
                for i, entity in enumerate(entities):
                    if not isinstance(entity, dict):
                        result['errors'].append(f"FAQ item {i+1} must be an object")
                        result['valid'] = False
                        continue
                    
                    if entity.get('@type') != 'Question':
                        result['errors'].append(f"FAQ item {i+1} must have @type 'Question'")
                        result['valid'] = False
                    
                    if 'name' not in entity:
                        result['errors'].append(f"FAQ item {i+1} missing question name")
                        result['valid'] = False
                    
                    if 'acceptedAnswer' not in entity:
                        result['errors'].append(f"FAQ item {i+1} missing acceptedAnswer")
                        result['valid'] = False
                    else:
                        answer = entity['acceptedAnswer']
                        if not isinstance(answer, dict):
                            result['errors'].append(f"FAQ item {i+1} acceptedAnswer must be an object")
                            result['valid'] = False
                        elif answer.get('@type') != 'Answer':
                            result['errors'].append(f"FAQ item {i+1} acceptedAnswer must have @type 'Answer'")
                            result['valid'] = False
                        elif 'text' not in answer:
                            result['errors'].append(f"FAQ item {i+1} acceptedAnswer missing text")
                            result['valid'] = False
        
        return result
    
    def analyze_existing_structured_data(self, url: str) -> Dict:
        """Analyze existing structured data on a webpage"""
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find JSON-LD scripts
            json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            existing_schemas = []
            
            for script in json_scripts:
                try:
                    if script.string:
                        schema_data = json.loads(script.string.strip())
                        existing_schemas.append(schema_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON-LD script: {e}")
                    continue
            
            # Analyze microdata (basic detection)
            microdata_items = soup.find_all(attrs={"itemscope": True})
            
            # Analyze RDFa (basic detection)
            rdfa_items = soup.find_all(attrs={"typeof": True})
            
            analysis = self._analyze_schema_completeness(existing_schemas)
            
            return {
                "url": url,
                "found_schemas": len(existing_schemas),
                "schemas": existing_schemas,
                "microdata_items": len(microdata_items),
                "rdfa_items": len(rdfa_items),
                "has_product_schema": any(
                    self._get_schema_type(schema) == 'Product' 
                    for schema in existing_schemas
                ),
                "analysis": analysis,
                "timestamp": self._get_current_timestamp()
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return {"error": f"Failed to fetch URL: {e}"}
        except Exception as e:
            logger.error(f"Error analyzing structured data: {e}")
            return {"error": f"Analysis failed: {e}"}
    
    def _validate_offers(self, offers: Any) -> Dict:
        """Validate offers data"""
        
        result = {'valid': True, 'errors': []}
        
        if not isinstance(offers, list):
            offers = [offers]
        
        for i, offer in enumerate(offers):
            if not isinstance(offer, dict):
                result['errors'].append(f"Offer {i+1} must be an object")
                result['valid'] = False
                continue
            
            if offer.get('@type') != 'Offer':
                result['errors'].append(f"Offer {i+1} must have @type 'Offer'")
                result['valid'] = False
            
            # Check required offer fields
            required_offer_fields = ['price', 'priceCurrency', 'availability']
            for field in required_offer_fields:
                if field not in offer:
                    result['errors'].append(f"Offer {i+1} missing required field: {field}")
                    result['valid'] = False
            
            # Validate availability URL
            if 'availability' in offer:
                availability = offer['availability']
                if isinstance(availability, str) and not availability.startswith('https://schema.org/'):
                    result['errors'].append(f"Offer {i+1} availability should use schema.org URL")
                    result['valid'] = False
        
        return result
    
    def _validate_images(self, images: Any) -> Dict:
        """Validate image data"""
        
        result = {'valid': True, 'warnings': []}
        
        if not isinstance(images, list):
            images = [images] if images else []
        
        if len(images) == 0:
            result['warnings'].append("No product images found")
            return result
        
        for i, image in enumerate(images):
            if isinstance(image, str):
                if not self._is_valid_url(image):
                    result['warnings'].append(f"Image {i+1} has invalid URL format")
            elif isinstance(image, dict):
                if '@type' in image and image['@type'] != 'ImageObject':
                    result['warnings'].append(f"Image {i+1} should have @type 'ImageObject'")
                if 'url' not in image:
                    result['warnings'].append(f"Image {i+1} missing URL")
        
        return result
    
    def _analyze_schema_completeness(self, schemas: List[Dict]) -> Dict:
        """Analyze completeness of existing schemas"""
        
        analysis = {
            'has_product': False,
            'has_organization': False,
            'has_breadcrumb': False,
            'has_faq': False,
            'has_review': False,
            'missing_fields': [],
            'schema_types_found': [],
            'total_schemas': len(schemas)
        }
        
        for schema in schemas:
            schema_type = self._get_schema_type(schema)
            if schema_type:
                analysis['schema_types_found'].append(schema_type)
            
            if schema_type == 'Product':
                analysis['has_product'] = True
                # Check for missing product fields
                for field in REQUIRED_PRODUCT_FIELDS:
                    if field not in schema:
                        analysis['missing_fields'].append(f"Product.{field}")
            
            elif schema_type == 'Organization':
                analysis['has_organization'] = True
                # Check for missing organization fields
                for field in REQUIRED_ORGANIZATION_FIELDS:
                    if field not in schema:
                        analysis['missing_fields'].append(f"Organization.{field}")
            
            elif schema_type == 'BreadcrumbList':
                analysis['has_breadcrumb'] = True
            
            elif schema_type == 'FAQPage':
                analysis['has_faq'] = True
            
            elif schema_type in ['Review', 'AggregateRating']:
                analysis['has_review'] = True
        
        return analysis
    
    def _get_schema_type(self, schema: Dict) -> Optional[str]:
        """Extract schema type from schema object"""
        
        if isinstance(schema, dict):
            # Handle single schema
            if '@type' in schema:
                return schema['@type']
            
            # Handle @graph format
            if '@graph' in schema and isinstance(schema['@graph'], list):
                types = []
                for item in schema['@graph']:
                    if isinstance(item, dict) and '@type' in item:
                        types.append(item['@type'])
                return types[0] if types else None
        
        return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL"""
        
        if not url or not isinstance(url, str):
            return False
        
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    def validate_against_google_requirements(self, schema: Dict) -> Dict:
        """Validate schema against Google Rich Results requirements"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'eligible_for_rich_results': True
        }
        
        schema_type = self._get_schema_type(schema)
        
        if schema_type in GOOGLE_RICH_RESULTS_REQUIREMENTS:
            requirements = GOOGLE_RICH_RESULTS_REQUIREMENTS[schema_type]
            
            # Check required fields
            for field in requirements.get('required', []):
                if field not in schema or not schema[field]:
                    result['errors'].append(f"Google requires field: {field}")
                    result['valid'] = False
                    result['eligible_for_rich_results'] = False
            
            # Check recommended fields
            for field in requirements.get('recommended', []):
                if field not in schema or not schema[field]:
                    result['warnings'].append(f"Google recommends field: {field}")
            
            # Special validation for Product images
            if schema_type == 'Product' and 'image' in schema:
                image_reqs = requirements.get('image_requirements', {})
                if image_reqs:
                    result['warnings'].append(
                        f"Ensure images meet Google requirements: "
                        f"min {image_reqs.get('min_width', 160)}x{image_reqs.get('min_height', 90)} pixels"
                    )
        
        return result