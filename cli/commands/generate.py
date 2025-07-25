# cli/commands/generate.py
"""
Generate command for CLI
"""

import os
import json
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from core.config import SchemaConfig
from core.generator import SchemaGenerator
from ai.enhancer import AIEnhancer
# from integrations.reviews.detector import ReviewDetector
from utils.exceptions import SchemaGeneratorError

load_dotenv()
console = Console()

@click.command()
@click.option('--shop-domain', required=True, help='Shopify shop domain (without .myshopify.com)')
@click.option('--access-token', help='Shopify Admin API access token')
@click.option('--openai-key', help='OpenAI API key for AI enhancements')
@click.option('--output', '-o', default='schemas.json', help='Output file path')
@click.option('--limit', '-l', default=50, help='Maximum number of products to process')
@click.option('--include-analysis', is_flag=True, help='Include existing schema analysis')
@click.option('--enable-ai', is_flag=True, help='Enable AI-powered enhancements')
@click.option('--include-reviews', is_flag=True, help='Include review data in schemas')
@click.option('--config-file', help='Path to configuration file')
def generate(shop_domain, access_token, openai_key, output, limit, include_analysis, 
             enable_ai, include_reviews, config_file):
    """Generate structured data schemas for a Shopify store"""
    
    try:
        # Load configuration
        if config_file:
            config = SchemaConfig.from_file(config_file)
        else:
            # Get credentials from environment if not provided
            access_token = access_token or os.getenv('SHOPIFY_ACCESS_TOKEN')
            openai_key = openai_key or os.getenv('OPENAI_API_KEY')
            
            if not access_token:
                console.print("[red]Error: Shopify access token is required[/red]")
                console.print("Provide via --access-token or set SHOPIFY_ACCESS_TOKEN environment variable")
                raise click.Abort()
            
            config = SchemaConfig(
                shop_domain=shop_domain,
                access_token=access_token,
                openai_api_key=openai_key,
                enable_ai_features=enable_ai and bool(openai_key),
                max_products=limit,
                include_analysis=include_analysis,
                include_reviews=include_reviews
            )
        
        # Display configuration
        _display_config(config)
        
        # Initialize components
        ai_enhancer = AIEnhancer(openai_key) if config.enable_ai_features and openai_key else None
        # review_integrator = ReviewDetector() if config.include_reviews else None
        
        generator = SchemaGenerator(config, ai_enhancer)
        
        # Generate schemas with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            
            main_task = progress.add_task("Generating schemas...", total=100)
            
            try:
                # Test connection first
                progress.update(main_task, description="Testing connection...")
                shop_info = generator.client.get_shop_info()
                progress.update(main_task, advance=10)
                
                if not shop_info.get('name'):
                    console.print("[red]Error: Unable to connect to Shopify API[/red]")
                    raise click.Abort()
                
                console.print(f"[green]✓ Connected to {shop_info['name']}[/green]")
                
                # Generate schemas
                progress.update(main_task, description="Generating schemas...")
                schemas = generator.generate_complete_schema_package()
                progress.update(main_task, advance=80)
                
                # Save results
                progress.update(main_task, description="Saving results...")
                with open(output, 'w') as f:
                    json.dump(schemas, f, indent=2)
                progress.update(main_task, advance=10)
                
                progress.update(main_task, description="Complete!", completed=100)
                
            except Exception as e:
                progress.stop()
                console.print(f"[red]Error during generation: {e}[/red]")
                raise click.Abort()
        
        # Display results
        _display_results(schemas, output)
        
    except SchemaGeneratorError as e:
        console.print(f"[red]Schema Generator Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise click.Abort()

def _display_config(config: SchemaConfig):
    """Display current configuration"""
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Shop Domain", config.shop_domain)
    config_table.add_row("Max Products", str(config.max_products))
    config_table.add_row("AI Features", "✓" if config.enable_ai_features else "✗")
    config_table.add_row("Include Reviews", "✓" if config.include_reviews else "✗")
    config_table.add_row("Include Analysis", "✓" if config.include_analysis else "✗")
    
    console.print(config_table)
    console.print()

def _display_results(schemas: dict, output_file: str):
    """Display generation results"""
    
    console.print("\n[bold green]✓ Schema generation complete![/bold green]")
    
    # Create results table
    table = Table(title="Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Shop Domain", schemas.get('shop_domain', 'Unknown'))
    table.add_row("Total Products", str(schemas.get('total_products', 0)))
    table.add_row("Products Processed", str(len(schemas.get('products', []))))
    table.add_row("Collections", str(len(schemas.get('collections', []))))
    table.add_row("Output File", output_file)
    table.add_row("Generated At", schemas.get('generated_at', 'Unknown'))
    
    if config_info := schemas.get('config'):
        table.add_row("AI Enhanced", "✓" if config_info.get('ai_enabled') else "✗")
    
    console.print(table)
    
    # Show sample schema info
    if schemas.get('products'):
        sample_product = schemas['products'][0]
        console.print(f"\n[bold blue]Sample Product:[/bold blue] {sample_product.get('title', 'Unknown')}")
        console.print(f"[blue]Schemas generated:[/blue] {', '.join(sample_product.get('schemas', {}).keys())}")
    
    # Show file size
    try:
        file_size = os.path.getsize(output_file)
        console.print(f"[blue]File size:[/blue] {file_size:,} bytes")
    except:
        pass