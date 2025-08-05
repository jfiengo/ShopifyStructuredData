# tests/test_ai_enhancer.py
"""
Tests for AI enhancer
"""

import pytest
from unittest.mock import Mock, patch
import json
from src.ai.enhancer import AIEnhancer
from src.utils.exceptions import AIEnhancementError

class TestAIEnhancer:
    """Test AIEnhancer class"""
    
    def test_enhancer_initialization(self):
        """Test AI enhancer initialization"""
        enhancer = AIEnhancer("test-api-key")
        
        assert enhancer.model == "gpt-3.5-turbo"
        assert enhancer.max_retries == 3
        assert enhancer.min_request_interval == 1.0
    
    def test_enhancer_initialization_without_key(self):
        """Test initialization without API key raises error"""
        # Test that the exception is raised with the correct message
        with pytest.raises(AIEnhancementError) as exc_info:
            AIEnhancer("")
        assert "OpenAI API key is required" in str(exc_info.value)
    
    @patch('src.ai.enhancer.OpenAI')
    def test_enhance_description_success(self, mock_openai, sample_product):
        """Test successful description enhancement"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Enhanced SEO-optimized product description"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create enhancer after setting up the mock
        enhancer = AIEnhancer("test-key")
        
        # Test with a simple description to avoid HTML processing issues
        enhanced = enhancer.enhance_description(
            "This is a test product description.", 
            sample_product
        )
        
        assert enhanced == "Enhanced SEO-optimized product description"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.ai.enhancer.OpenAI')
    def test_enhance_description_with_empty_input(self, mock_openai, sample_product):
        """Test description enhancement with empty input"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated description from product data"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        enhancer = AIEnhancer("test-key")
        enhanced = enhancer.enhance_description("", sample_product)
        
        # Should generate description from product data
        assert len(enhanced) > 0
        assert enhanced != ""
    
    @patch('src.ai.enhancer.OpenAI')
    def test_generate_faq_schema_success(self, mock_openai, sample_product):
        """Test successful FAQ schema generation"""
        mock_client = Mock()
        mock_response = Mock()
        faq_json = {
            "questions": [
                {
                    "question": "What is this product?",
                    "answer": "This is a test product."
                },
                {
                    "question": "How do I use it?",
                    "answer": "Follow the instructions included."
                }
            ]
        }
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(faq_json)
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        enhancer = AIEnhancer("test-key")
        faq_schema = enhancer.generate_faq_schema(sample_product)
        
        assert faq_schema['@context'] == "https://schema.org"
        assert faq_schema['@type'] == "FAQPage"
        assert len(faq_schema['mainEntity']) == 2
        
        first_question = faq_schema['mainEntity'][0]
        assert first_question['@type'] == "Question"
        assert first_question['name'] == "What is this product?"
        assert first_question['acceptedAnswer']['@type'] == "Answer"
        assert first_question['acceptedAnswer']['text'] == "This is a test product."
    
    @patch('src.ai.enhancer.OpenAI')
    def test_generate_faq_schema_invalid_json(self, mock_openai, sample_product):
        """Test FAQ generation with invalid JSON response"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        enhancer = AIEnhancer("test-key")
        faq_schema = enhancer.generate_faq_schema(sample_product)
        
        # Should fall back to basic FAQ
        assert faq_schema['@context'] == "https://schema.org"
        assert faq_schema['@type'] == "FAQPage"
        assert len(faq_schema['mainEntity']) >= 1
    
    @patch('src.ai.enhancer.OpenAI')
    def test_categorize_product_ai(self, mock_openai, sample_product):
        """Test AI-powered product categorization"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Electronics"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Product that doesn't match basic categorization
        product = {
            'title': 'Weird Gadget',
            'product_type': 'unknown',
            'body_html': '<p>Some electronic device</p>',
            'tags': ['gadget', 'device']
        }
        
        enhancer = AIEnhancer("test-key")
        category = enhancer.categorize_product(product)
        
        # Mocked openai response returns "Electronics" because electronic is in the body_html and therefore included in the AI 
        assert category == "Electronics"
    
    @patch('src.ai.enhancer.OpenAI')
    def test_generate_keywords(self, mock_openai, sample_product):
        """Test keyword generation"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "test product, sample item, quality goods, affordable price, best seller"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        enhancer = AIEnhancer("test-key")
        keywords = enhancer.generate_keywords(sample_product)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 15  # Should respect max limit
        # Check for keywords from mocked openai response
        assert 'test product' in keywords
        assert 'sample item' in keywords
    
    @patch('src.ai.enhancer.OpenAI')
    def test_openai_rate_limit_handling(self, mock_openai, sample_product):
        """Test OpenAI rate limit handling"""
        from openai import RateLimitError
        
        mock_client = Mock()
        # First call raises rate limit, second succeeds
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=Mock(), body=""),
            Mock(choices=[Mock(message=Mock(content="Success after retry"))])
        ]
        mock_openai.return_value = mock_client
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            enhancer = AIEnhancer("test-key")
            result = enhancer._make_openai_request("test prompt")
        
        assert result == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2
    
    def test_basic_fallback_methods(self, sample_product):
        """Test fallback methods when AI is not available"""
        enhancer = AIEnhancer("test-key")
        
        # Test basic categorization
        category = enhancer._basic_categorization(sample_product)
        assert isinstance(category, str)
        
        # Test basic keyword extraction
        keywords = enhancer._extract_basic_keywords(sample_product)
        assert isinstance(keywords, list)
        assert len(keywords) <= 15
        
        # Test basic FAQ generation
        faq = enhancer._generate_basic_faq(sample_product)
        assert faq['@type'] == 'FAQPage'
        assert len(faq['mainEntity']) >= 1