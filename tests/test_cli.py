# tests/test_cli.py
"""
Tests for CLI commands
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, mock_open
import json
import tempfile
import os

# Import CLI commands
from cli.main import cli
from cli.commands.generate import generate
from cli.commands.validate import validate
from cli.commands.setup import setup

class TestCLICommands:
    """Test CLI commands"""
    
    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Shopify Structured Data Generator CLI" in result.output
    
    @patch('cli.commands.generate.console')
    @patch('cli.commands.generate.Table')
    @patch('cli.commands.generate.Progress')
    @patch('cli.commands.generate.AIEnhancer')
    @patch('cli.commands.generate.SchemaGenerator')
    @patch('cli.commands.generate.SchemaConfig')
    def test_generate_command_basic(self, mock_config_class, mock_generator_class, mock_ai_enhancer_class, mock_progress, mock_table, mock_console):
        """Test basic generate command"""
        # Mock configuration
        mock_config = Mock()
        mock_config.shop_domain = "test-shop"
        mock_config_class.return_value = mock_config
        
        # Mock generator with client
        mock_generator = Mock()
        mock_client = Mock()
        mock_client.get_shop_info.return_value = {'name': 'Test Shop'}
        mock_generator.client = mock_client
        mock_generator.generate_complete_schema_package.return_value = {
            'total_products': 5,
            'products': [{'title': f'Product {i}'} for i in range(5)],
            'collections': [],
            'generated_at': '2024-01-01T00:00:00'
        }
        mock_generator_class.return_value = mock_generator
        
        # Mock AI enhancer (should not be created since no OpenAI key provided)
        mock_ai_enhancer_class.return_value = None
        
        # Mock progress bar
        mock_progress_instance = Mock()
        mock_progress_instance.__enter__ = Mock(return_value=mock_progress_instance)
        mock_progress_instance.__exit__ = Mock(return_value=None)
        mock_progress_instance.add_task = Mock(return_value=1)
        mock_progress_instance.update = Mock()
        mock_progress_instance.stop = Mock()
        mock_progress.return_value = mock_progress_instance
        
        # Mock rich table
        mock_table_instance = Mock()
        mock_table_instance.add_column = Mock()
        mock_table_instance.add_row = Mock()
        mock_table.return_value = mock_table_instance
        
        # Mock console
        mock_console.print = Mock()
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(generate, [
                '--shop-domain', 'test-shop',
                '--access-token', 'test-token',
                '--limit', '5',
                '--output', 'test_output.json'
            ])
        
        assert result.exit_code == 0
        
        # Check that console.print was called with the success message
        success_calls = [call for call in mock_console.print.call_args_list 
                        if any("Schema generation complete" in str(arg) for arg in call[0])]
        assert len(success_calls) > 0, "Success message not found in console output"
        
        mock_generator.generate_complete_schema_package.assert_called_once()
    
    def test_validate_command_with_valid_schemas(self):
        """Test validate command with valid schemas"""
        valid_schemas = {
            'organization': {
                '@context': 'https://schema.org',
                '@type': 'Organization',
                'name': 'Test Store',
                'url': 'https://test-store.com'
            },
            'products': [
                {
                    'product_id': 1,
                    'title': 'Test Product',
                    'schemas': {
                        'product': {
                            '@context': 'https://schema.org/',
                            '@type': 'Product',
                            'name': 'Test Product',
                            'description': 'Test description',
                            'image': ['https://example.com/image.jpg'],
                            'brand': {
                                '@type': 'Brand',
                                'name': 'Test Brand'
                            },
                            'offers': {
                                '@type': 'Offer',
                                'price': '29.99',
                                'priceCurrency': 'USD',
                                'availability': 'https://schema.org/InStock'
                            }
                        }
                    }
                }
            ]
        }
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            with open('valid_schemas.json', 'w') as f:
                json.dump(valid_schemas, f)
            
            result = runner.invoke(validate, ['valid_schemas.json'])
        
        assert result.exit_code == 0
        assert "Validation passed" in result.output
    
    def test_validate_command_with_invalid_schemas(self):
        """Test validate command with invalid schemas"""
        invalid_schemas = {
            'products': [
                {
                    'product_id': 1,
                    'title': 'Test Product',
                    'schemas': {
                        'product': {
                            '@context': 'https://schema.org/',
                            '@type': 'Product',
                            'name': 'Test Product'
                            # Missing required fields
                        }
                    }
                }
            ]
        }
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            with open('invalid_schemas.json', 'w') as f:
                json.dump(invalid_schemas, f)
            
            result = runner.invoke(validate, ['invalid_schemas.json'])
        
        assert result.exit_code == 1  # Should fail validation
        assert "Validation failed" in result.output
    
    @patch('cli.commands.setup.test_shopify_connection')
    @patch('cli.commands.setup.Confirm.ask')
    @patch('cli.commands.setup.Prompt.ask')
    def test_setup_command_interactive(self, mock_prompt, mock_confirm, mock_test_connection):
        """Test interactive setup command"""
        # Mock user inputs
        mock_prompt.side_effect = [
            'test-shop',  # shop domain
            'test-token',  # access token
            '',  # openai key (empty)
            '50',  # max products
            'json'  # output format
        ]
        
        mock_confirm.side_effect = [
            False,  # enable AI
            True,   # include collections
            True,   # include FAQ
            True    # save to YAML
        ]
        
        mock_test_connection.return_value = True
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(setup, input='\n'.join([
                'test-shop', 'test-token', 'n', '50', 'y', 'y', 'y'
            ]))
        
        # Should complete successfully
        assert "Setup Complete!" in result.output
        
        # Should create .env file
        assert os.path.exists('.env')