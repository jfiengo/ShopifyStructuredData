# src/ai/enhancer.py
"""
AI-powered enhancement features for schema generation using OpenAI
"""

import json
import logging
from typing import Dict, List, Optional, Any
import openai
from openai import OpenAI
import time
import re

from utils.constants import AI_PROMPTS, CATEGORY_MAPPING
from utils.helpers import clean_html, truncate_text
from utils.exceptions import AIEnhancementError

logger = logging.getLogger(__name__)

class AIEnhancer:
    """AI-powered content enhancement using OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_retries: int = 3):
        """
        Initialize AI enhancer
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.)
            max_retries: Maximum number of retries for failed requests
        """
        if not api_key:
            raise AIEnhancementError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        logger.info(f"AI Enhancer initialized with model: {model}")
    
    def enhance_description(self, description: str, product: Dict, max_length: int = 200) -> str:
        """
        Enhance product description for SEO and user experience
        
        Args:
            description: Original product description
            product: Product data dictionary
            max_length: Maximum length for enhanced description
            
        Returns:
            Enhanced product description
        """
        if not description or len(description.strip()) < 10:
            # If description is too short, generate from product data
            return self._generate_description_from_product(product, max_length)
        
        try:
            # Clean the original description
            clean_desc = clean_html(description)
            
            # Prepare context
            context = {
                'title': product.get('title', ''),
                'description': truncate_text(clean_desc, 300),
                'category': product.get('product_type', ''),
                'vendor': product.get('vendor', ''),
                'tags': ', '.join(product.get('tags', [])[:5])
            }
            
            prompt = AI_PROMPTS['DESCRIPTION_ENHANCEMENT'].format(**context)
            
            response = self._make_openai_request(prompt, max_tokens=250)
            
            if response:
                enhanced = response.strip()
                # Ensure it's not too long
                enhanced = truncate_text(enhanced, max_length)
                
                # Fallback to original if enhancement seems invalid
                if len(enhanced) < 20 or "I cannot" in enhanced:
                    return truncate_text(clean_desc, max_length)
                
                return enhanced
            
        except Exception as e:
            logger.warning(f"Description enhancement failed: {e}")
        
        # Fallback to cleaned original
        return truncate_text(clean_html(description), max_length)
    
    def generate_faq_schema(self, product: Dict) -> Dict:
        """
        Generate FAQ schema using AI
        
        Args:
            product: Product data dictionary
            
        Returns:
            FAQ schema dictionary
        """
        try:
            # Prepare context
            description = clean_html(product.get('body_html', ''))
            context = {
                'title': product.get('title', ''),
                'description': truncate_text(description, 500),
                'category': product.get('product_type', ''),
                'vendor': product.get('vendor', '')
            }
            
            prompt = AI_PROMPTS['FAQ_GENERATION'].format(**context)
            
            response = self._make_openai_request(prompt, max_tokens=400)
            
            if response:
                # Try to parse JSON response
                try:
                    faq_data = json.loads(response)
                    questions = faq_data.get('questions', [])
                    
                    if questions and len(questions) > 0:
                        main_entities = []
                        
                        for q in questions[:5]:  # Limit to 5 questions
                            if isinstance(q, dict) and 'question' in q and 'answer' in q:
                                main_entities.append({
                                    "@type": "Question",
                                    "name": q['question'],
                                    "acceptedAnswer": {
                                        "@type": "Answer",
                                        "text": q['answer']
                                    }
                                })
                        
                        if main_entities:
                            return {
                                "@context": "https://schema.org",
                                "@type": "FAQPage",
                                "mainEntity": main_entities
                            }
                
                except json.JSONDecodeError:
                    logger.warning("Failed to parse FAQ JSON from AI response")
        
        except Exception as e:
            logger.warning(f"AI FAQ generation failed: {e}")
        
        # Fallback to basic FAQ
        return self._generate_basic_faq(product)
    
    def categorize_product(self, product: Dict) -> str:
        """
        Categorize product using AI
        
        Args:
            product: Product data dictionary
            
        Returns:
            Product category string
        """
        try:
            # First try basic mapping
            basic_category = self._basic_categorization(product)
            if basic_category != 'Other':
                return basic_category
            
            # Use AI for unknown categories
            description = clean_html(product.get('body_html', ''))
            
            prompt = f"""
            Categorize this product into one of these categories:
            {', '.join(set(CATEGORY_MAPPING.values()))}
            
            Product: {product.get('title', '')}
            Type: {product.get('product_type', '')}
            Description: {truncate_text(description, 200)}
            Tags: {', '.join(product.get('tags', [])[:5])}
            
            Return only the category name, nothing else.
            """
            
            response = self._make_openai_request(prompt, max_tokens=50)
            
            if response:
                category = response.strip()
                # Validate it's one of our known categories
                valid_categories = set(CATEGORY_MAPPING.values())
                if category in valid_categories:
                    return category
        
        except Exception as e:
            logger.warning(f"AI categorization failed: {e}")
        
        # Fallback to basic categorization
        return self._basic_categorization(product)
    
    def extract_product_attributes(self, product: Dict) -> Dict:
        """
        Extract structured attributes from product description using AI
        
        Args:
            product: Product data dictionary
            
        Returns:
            Dictionary of extracted attributes
        """
        try:
            description = clean_html(product.get('body_html', ''))
            if len(description) < 50:
                return {}
            
            prompt = AI_PROMPTS['ATTRIBUTE_EXTRACTION'].format(description=description)
            
            response = self._make_openai_request(prompt, max_tokens=300)
            
            if response:
                try:
                    attributes = json.loads(response)
                    # Clean up empty values
                    return {k: v for k, v in attributes.items() if v}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse attributes JSON from AI response")
        
        except Exception as e:
            logger.warning(f"AI attribute extraction failed: {e}")
        
        return {}
    
    def generate_keywords(self, product: Dict, max_keywords: int = 15) -> List[str]:
        """
        Generate relevant SEO keywords using AI
        
        Args:
            product: Product data dictionary
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of relevant keywords
        """
        try:
            description = clean_html(product.get('body_html', ''))
            
            context = {
                'title': product.get('title', ''),
                'description': truncate_text(description, 300),
                'category': product.get('product_type', '')
            }
            
            prompt = AI_PROMPTS['KEYWORD_EXTRACTION'].format(**context)
            
            response = self._make_openai_request(prompt, max_tokens=200)
            
            if response:
                # Parse comma-separated keywords
                keywords = [k.strip().lower() for k in response.split(',')]
                keywords = [k for k in keywords if k and len(k) > 2]
                return keywords[:max_keywords]
        
        except Exception as e:
            logger.warning(f"AI keyword generation failed: {e}")
        
        # Fallback to basic keyword extraction
        return self._extract_basic_keywords(product, max_keywords)
    
    def optimize_title_for_seo(self, product: Dict, max_length: int = 60) -> str:
        """
        Optimize product title for SEO
        
        Args:
            product: Product data dictionary
            max_length: Maximum title length
            
        Returns:
            SEO-optimized title
        """
        original_title = product.get('title', '')
        
        if len(original_title) <= max_length:
            return original_title
        
        try:
            vendor = product.get('vendor', '')
            product_type = product.get('product_type', '')
            
            prompt = f"""
            Optimize this product title for SEO. Keep it under {max_length} characters.
            Include the most important keywords while maintaining readability.
            
            Original title: {original_title}
            Brand: {vendor}
            Category: {product_type}
            
            Return only the optimized title, nothing else.
            """
            
            response = self._make_openai_request(prompt, max_tokens=100)
            
            if response and len(response.strip()) <= max_length:
                return response.strip()
        
        except Exception as e:
            logger.warning(f"AI title optimization failed: {e}")
        
        # Fallback to truncated original
        return truncate_text(original_title, max_length)
    
    def _make_openai_request(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """
        Make a request to OpenAI API with rate limiting and error handling
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0-1)
            
        Returns:
            Response text or None if failed
        """
        # Rate limiting
        self._wait_for_rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful SEO and e-commerce expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        return content.strip()
                
            except openai.RateLimitError:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"OpenAI rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            except openai.APIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise AIEnhancementError(f"OpenAI API failed after {self.max_retries} attempts")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(1)
        
        return None
    
    def _wait_for_rate_limit(self):
        """Ensure minimum interval between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _generate_description_from_product(self, product: Dict, max_length: int = 200) -> str:
        """Generate description from product data when none exists"""
        
        title = product.get('title', '')
        vendor = product.get('vendor', '')
        product_type = product.get('product_type', '')
        tags = product.get('tags', [])
        
        try:
            prompt = f"""
            Write a compelling product description for this product:
            
            Name: {title}
            Brand: {vendor}
            Category: {product_type}
            Features: {', '.join(tags[:5])}
            
            Make it {max_length} characters or less. Focus on benefits and key features.
            Return only the description, nothing else.
            """
            
            response = self._make_openai_request(prompt, max_tokens=150)
            
            if response and len(response) >= 20:
                return truncate_text(response, max_length)
        
        except Exception as e:
            logger.warning(f"Failed to generate description from product data: {e}")
        
        # Simple fallback
        parts = []
        if vendor and vendor.lower() not in title.lower():
            parts.append(vendor)
        parts.append(title)
        if product_type and product_type.lower() not in title.lower():
            parts.append(f"in {product_type}")
        
        return ' '.join(parts)[:max_length]
    
    def _generate_basic_faq(self, product: Dict) -> Dict:
        """Generate basic FAQ without AI as fallback"""
        
        title = product.get('title', '')
        description = clean_html(product.get('body_html', ''))
        
        basic_questions = []
        
        # Basic question about what the product is
        if title:
            basic_questions.append({
                "@type": "Question",
                "name": f"What is {title}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": truncate_text(description, 200) if description else f"{title} is available in our store."
                }
            })
        
        # Basic shipping question
        basic_questions.append({
            "@type": "Question", 
            "name": "Do you offer shipping?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Yes, we offer shipping. Please check our shipping policy for details on delivery times and costs."
            }
        })
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": basic_questions
        }
    
    def _basic_categorization(self, product: Dict) -> str:
        """Basic categorization without AI"""
        
        product_type = product.get('product_type', '').lower()
        tags = [tag.lower() for tag in product.get('tags', [])]
        title = product.get('title', '').lower()
        
        # Combine all text for matching
        text_to_match = f"{product_type} {' '.join(tags)} {title}"
        
        # Check category mapping
        for key, category in CATEGORY_MAPPING.items():
            if key in text_to_match:
                return category
        
        return 'Other'
    
    def _extract_basic_keywords(self, product: Dict, max_keywords: int = 15) -> List[str]:
        """Extract basic keywords without AI"""
        
        keywords = set()
        
        # Add from title
        title_words = re.findall(r'\b\w{3,}\b', product.get('title', '').lower())
        keywords.update(title_words)
        
        # Add from product type
        if product.get('product_type'):
            type_words = re.findall(r'\b\w{3,}\b', product.get('product_type', '').lower())
            keywords.update(type_words)
        
        # Add from tags
        for tag in product.get('tags', []):
            tag_words = re.findall(r'\b\w{3,}\b', tag.lower())
            keywords.update(tag_words)
        
        # Add vendor
        if product.get('vendor'):
            keywords.add(product.get('vendor', '').lower())
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'they', 'you', 'are', 'was', 'will', 'have', 'has', 'had'}
        keywords = [k for k in keywords if k not in stop_words and len(k) > 2]
        
        return list(keywords)[:max_keywords]
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics (placeholder for monitoring)"""
        return {
            "model": self.model,
            "max_retries": self.max_retries,
            "min_request_interval": self.min_request_interval,
            "last_request_time": self.last_request_time
        }
