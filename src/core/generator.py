# src/core/generator.py
"""
Main schema generation logic
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from .shopify_client import ShopifyClient
from .config import SchemaConfig
from ..utils.helpers import clean_html, generate_price_valid_until
from ..utils.constants import CATEGORY_MAPPING, REQUIRED_PRODUCT_FIELDS

logger = logging.getLogger(__name__)

class SchemaGenerator:
    """Main class for generating structured data schemas from Shopify stores"""
    
    def __init__(self, config: SchemaConfig, ai_enhancer=None, review_integrator=None):
        self.config = config
        self.client = ShopifyClient(config)
        self.ai_enhancer = ai_enhancer
        self.review_integrator = review_integrator
    
    def generate_complete_schema_package(self) -> Dict:
        """Generate complete schema package for entire shop"""
        
        logger.info("Starting complete schema generation...")
        start_time = datetime.now()
        
        # Fetch all required data
        shop_info = self.client.get_shop_info()
        collections = self.client.get_collections() if self.config.include_collections else []
        
        # Initialize result structure
        schemas = {
            "organization": self.generate_organization_schema(shop_info),
            "products": [],
            "collections": [],
            "generated_at": start_time.isoformat(),
            "shop_domain": self.config.shop_domain,
            "total_products": 0,
            "config": {
                "ai_enabled": self.config.enable_ai_features,
                "include_faq": self.config.include_faq,
                "include_reviews": self.config.include_reviews
            }
        }
        
        # Process products
        product_count = 0
        for product in self.client.get_products(self.config.max_products):
            logger.info(f"Processing product {product_count + 1}: {product['title']}")
            
            product_schemas = self._generate_product_package(product, shop_info, collections)
            schemas["products"].append(product_schemas)
            
            product_count += 1
        
        # Process collections
        if self.config.include_collections:
            for collection in collections:
                collection_schema = self._generate_collection_schema(collection, shop_info)
                schemas["collections"].append(collection_schema)
        
        schemas["total_products"] = product_count
        
        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Schema generation complete! Processed {product_count} products in {generation_time:.2f} seconds")
        
        return schemas
    
    def _generate_product_package(self, product: Dict, shop_info: Dict, collections: List[Dict]) -> Dict:
        """Generate complete schema package for a single product"""
        
        product_schemas = {
            "product_id": product['id'],
            "handle": product['handle'],
            "title": product['title'],
            "schemas": {
                "product": self.generate_product_schema(product, shop_info),
                "breadcrumb": self.generate_breadcrumb_schema(product, collections)
            }
        }
        
        # Add FAQ schema if enabled
        if self.config.include_faq:
            product_schemas["schemas"]["faq"] = self.generate_faq_schema(product)
        
        # Add review schema if enabled and available
        if self.config.include_reviews and self.review_integrator:
            review_schema = self.generate_review_schema(product)
            if review_schema:
                product_schemas["schemas"]["review"] = review_schema
        
        return product_schemas
    
    def generate_product_schema(self, product: Dict, shop_info: Dict) -> Dict:
        """Generate comprehensive Product schema markup"""
        
        # Clean and prepare basic data
        clean_description = clean_html(product.get('body_html', ''))
        images = [img['src'] for img in product.get('images', [])]
        variants = product.get('variants', [])
        
        # Enhance description with AI if available
        if self.ai_enhancer and self.config.enable_ai_features:
            try:
                clean_description = self.ai_enhancer.enhance_description(clean_description, product)
            except Exception as e:
                logger.warning(f"AI description enhancement failed: {e}")
        
        # Base schema structure
        schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product['title'],
            "description": clean_description,
            "image": images,
            "url": f"https://{self.config.shop_domain}.myshopify.com/products/{product['handle']}",
            "brand": {
                "@type": "Brand",
                "name": product.get('vendor', shop_info.get('name', 'Unknown'))
            },
            "sku": variants[0].get('sku', product['handle']) if variants else product['handle'],
            "offers": self._generate_offers(variants, shop_info),
            "category": self._categorize_product(product)
        }
        
        # Add aggregate rating if available
        if rating_data := self._get_product_rating(product):
            schema["aggregateRating"] = rating_data
        
        # Add variant information for variable products
        if len(variants) > 1:
            schema["hasVariant"] = self._generate_variant_schemas(variants)
        
        # Add additional properties
        schema.update(self._extract_product_properties(product))
        
        return schema
    
    def generate_organization_schema(self, shop_info: Dict) -> Dict:
        """Generate Organization schema for the shop"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": shop_info.get('name', ''),
            "url": f"https://{shop_info.get('domain', self.config.shop_domain + '.myshopify.com')}",
            "description": clean_html(shop_info.get('description', '')),
        }
        
        # Add contact information
        if contact_info := self._extract_contact_info(shop_info):
            schema["contactPoint"] = contact_info
        
        # Add address if available
        if address := self._extract_address(shop_info):
            schema["address"] = address
        
        # Add social media links
        if social_links := self._extract_social_links(shop_info):
            schema["sameAs"] = social_links
        
        return schema
    
    def generate_breadcrumb_schema(self, product: Dict, collections: List[Dict]) -> Dict:
        """Generate BreadcrumbList schema for product navigation"""
        
        breadcrumbs = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": f"https://{self.config.shop_domain}.myshopify.com"
            }
        ]
        
        # Add collection breadcrumbs if product belongs to collections
        product_collection_ids = [coll['id'] for coll in product.get('collections', [])]
        if product_collection_ids and collections:
            # Find the first matching collection
            for collection in collections:
                if collection['id'] in product_collection_ids:
                    breadcrumbs.append({
                        "@type": "ListItem",
                        "position": len(breadcrumbs) + 1,
                        "name": collection['title'],
                        "item": f"https://{self.config.shop_domain}.myshopify.com/collections/{collection['handle']}"
                    })
                    break
        
        # Add product
        breadcrumbs.append({
            "@type": "ListItem",
            "position": len(breadcrumbs) + 1,
            "name": product['title'],
            "item": f"https://{self.config.shop_domain}.myshopify.com/products/{product['handle']}"
        })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumbs
        }
    
    def generate_faq_schema(self, product: Dict) -> Dict:
        """Generate FAQ schema"""
        
        if self.ai_enhancer and self.config.enable_ai_features:
            try:
                return self.ai_enhancer.generate_faq_schema(product)
            except Exception as e:
                logger.warning(f"AI FAQ generation failed: {e}")
        
        # Fallback to basic FAQ
        return self._generate_basic_faq(product)
    
    def generate_review_schema(self, product: Dict) -> Optional[Dict]:
        """Generate review schema using review integrator"""
        
        if not self.review_integrator:
            return None
        
        try:
            reviews_data = self.review_integrator.get_product_reviews(
                product['id'], 
                self.config.shop_domain
            )
            
            if reviews_data and reviews_data.get('total_reviews', 0) > 0:
                return {
                    "@context": "https://schema.org",
                    "@type": "AggregateRating",
                    "ratingValue": str(reviews_data.get('average_rating', 0)),
                    "reviewCount": str(reviews_data.get('total_reviews', 0)),
                    "bestRating": "5",
                    "worstRating": "1"
                }
        except Exception as e:
            logger.warning(f"Review schema generation failed: {e}")
        
        return None
    
    # Helper methods
    def _generate_offers(self, variants: List[Dict], shop_info: Dict) -> List[Dict]:
        """Generate offer schemas for product variants"""
        offers = []
        
        for variant in variants:
            offer = {
                "@type": "Offer",
                "price": variant.get('price', '0'),
                "priceCurrency": shop_info.get('currency', 'USD'),
                "availability": (
                    "https://schema.org/InStock" 
                    if variant.get('inventory_quantity', 0) > 0 
                    else "https://schema.org/OutOfStock"
                ),
                "sku": variant.get('sku', ''),
                "priceValidUntil": generate_price_valid_until(),
                "seller": {
                    "@type": "Organization",
                    "name": shop_info.get('name', 'Store')
                }
            }
            offers.append(offer)
        
        return offers
    
    def _categorize_product(self, product: Dict) -> str:
        """Categorize product using mapping or AI"""
        
        if self.ai_enhancer and self.config.enable_ai_features:
            try:
                return self.ai_enhancer.categorize_product(product)
            except Exception as e:
                logger.warning(f"AI categorization failed: {e}")
        
        # Fallback to basic mapping
        product_type = product.get('product_type', '').lower()
        tags = [tag.lower() for tag in product.get('tags', [])]
        
        # Check product type first
        for key, category in CATEGORY_MAPPING.items():
            if key in product_type:
                return category
        
        # Check tags
        for tag in tags:
            for key, category in CATEGORY_MAPPING.items():
                if key in tag:
                    return category
        
        return 'Other'
    
    def _extract_product_properties(self, product: Dict) -> Dict:
        """Extract additional product properties"""
        properties = {}
        
        # Add weight if available
        variants = product.get('variants', [])
        if variants and variants[0].get('weight'):
            properties["weight"] = {
                "@type": "QuantitativeValue",
                "value": variants[0]['weight'],
                "unitCode": variants[0].get('weight_unit', 'g')
            }
        
        return properties
    
    def _get_product_rating(self, product: Dict) -> Optional[Dict]:
        """Get product rating data"""
        # This would integrate with review systems
        return None
    
    def _generate_variant_schemas(self, variants: List[Dict]) -> List[Dict]:
        """Generate schemas for product variants"""
        variant_schemas = []
        
        for variant in variants:
            variant_schema = {
                "@type": "ProductModel",
                "name": variant.get('title', ''),
                "sku": variant.get('sku', ''),
                "offers": {
                    "@type": "Offer",
                    "price": variant.get('price', '0'),
                    "availability": (
                        "https://schema.org/InStock" 
                        if variant.get('inventory_quantity', 0) > 0 
                        else "https://schema.org/OutOfStock"
                    )
                }
            }
            variant_schemas.append(variant_schema)
        
        return variant_schemas
    
    def _extract_contact_info(self, shop_info: Dict) -> Optional[Dict]:
        """Extract contact information from shop data"""
        contact = {}
        
        if phone := shop_info.get('phone'):
            contact["telephone"] = phone
        
        if email := shop_info.get('email'):
            contact["email"] = email
        
        if contact:
            contact["@type"] = "ContactPoint"
            contact["contactType"] = "customer service"
            return contact
        
        return None
    
    def _extract_address(self, shop_info: Dict) -> Optional[Dict]:
        """Extract address information from shop data"""
        address_fields = ['address1', 'city', 'province', 'zip', 'country']
        
        if any(shop_info.get(field) for field in address_fields):
            return {
                "@type": "PostalAddress",
                "streetAddress": shop_info.get('address1', ''),
                "addressLocality": shop_info.get('city', ''),
                "addressRegion": shop_info.get('province', ''),
                "postalCode": shop_info.get('zip', ''),
                "addressCountry": shop_info.get('country', '')
            }
        
        return None
    
    def _extract_social_links(self, shop_info: Dict) -> List[str]:
        """Extract social media links"""
        social_links = []
        
        # Extract from shop info if available
        social_fields = ['twitter', 'facebook', 'instagram', 'linkedin']
        for field in social_fields:
            if value := shop_info.get(field):
                if field == 'twitter':
                    social_links.append(f"https://twitter.com/{value}")
                elif field == 'facebook':
                    social_links.append(f"https://facebook.com/{value}")
                elif field == 'instagram':
                    social_links.append(f"https://instagram.com/{value}")
                elif field == 'linkedin':
                    social_links.append(f"https://linkedin.com/company/{value}")
        
        return social_links
    
    def _generate_basic_faq(self, product: Dict) -> Dict:
        """Generate basic FAQ without AI"""
        description = clean_html(product.get('body_html', ''))
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"What is {product['title']}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": description[:200] + "..." if len(description) > 200 else description
                    }
                }
            ]
        }
    
    def _generate_collection_schema(self, collection: Dict, shop_info: Dict) -> Dict:
        """Generate schema for collection pages"""
        return {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": collection['title'],
            "description": clean_html(collection.get('body_html', '')),
            "url": f"https://{self.config.shop_domain}.myshopify.com/collections/{collection['handle']}",
            "isPartOf": {
                "@type": "WebSite",
                "name": shop_info.get('name', ''),
                "url": f"https://{self.config.shop_domain}.myshopify.com"
            }
        }