# src/core/config.py
"""
Configuration management for Shopify Schema Generator
"""

import os
import yaml
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class SchemaConfig:
    """Configuration for schema generation"""
    
    # Shopify settings
    shop_domain: str
    access_token: str
    api_version: str = "2023-10"
    
    # AI settings
    openai_api_key: Optional[str] = None
    enable_ai_features: bool = False
    
    # Generation settings
    max_products: int = 250
    include_variants: bool = True
    include_collections: bool = True
    include_faq: bool = True
    include_reviews: bool = False
    
    # Output settings
    output_format: str = "json"  # json, yaml, xml
    include_analysis: bool = False
    validate_schemas: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'SchemaConfig':
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)
    
    @classmethod
    def from_env(cls) -> 'SchemaConfig':
        """Load configuration from environment variables"""
        return cls(
            shop_domain=os.getenv('SHOPIFY_SHOP_DOMAIN', ''),
            access_token=os.getenv('SHOPIFY_ACCESS_TOKEN', ''),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            enable_ai_features=os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true',
            max_products=int(os.getenv('MAX_PRODUCTS', '250')),
        )
    
    def to_file(self, config_path: str):
        """Save configuration to YAML file"""
        with open(config_path, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
    
    @property
    def base_url(self) -> str:
        return f"https://{self.shop_domain}.myshopify.com/admin/api/{self.api_version}"