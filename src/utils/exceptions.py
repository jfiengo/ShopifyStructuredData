# src/utils/exceptions.py
"""
Custom exceptions for the schema generator
"""

class SchemaGeneratorError(Exception):
    """Base exception for schema generator"""
    pass

class ShopifyAPIError(SchemaGeneratorError):
    """Shopify API related errors"""
    pass

class ConfigurationError(SchemaGeneratorError):
    """Configuration related errors"""
    pass

class ValidationError(SchemaGeneratorError):
    """Schema validation errors"""
    pass

class AIEnhancementError(SchemaGeneratorError):
    """AI enhancement related errors"""
    pass

class ReviewIntegrationError(SchemaGeneratorError):
    """Review platform integration errors"""
    pass

class DatabaseError(SchemaGeneratorError):
    """Database operation errors"""
    pass

class RateLimitError(SchemaGeneratorError):
    """Rate limiting errors"""
    pass

class AuthenticationError(SchemaGeneratorError):
    """Authentication related errors"""
    pass

class FileProcessingError(SchemaGeneratorError):
    """File processing errors"""
    pass