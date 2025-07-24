"""
Analyze command for the CLI
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from core.config import SchemaConfig
from validation.schema_validator import SchemaValidator
from utils.exceptions import ValidationError

console = Console()

@click.command()
@click.option('--shop-domain', required=True, help='Shopify shop domain')
@click.option('--product-handle', required=True, help='Product handle to analyze')
@click.option('--detailed', is_flag=True, help='Show detailed analysis')
@click.option('--google-check', is_flag=True, help='Check Google Rich Results compatibility')
@click.option('--output', help='Save analysis to file')
def analyze(shop_domain, product_handle, detailed, google_check, output):
    """Analyze existing structured data for a specific product"""
    
    product_url = f"https://{shop_domain}.myshopify.com/products/{product_handle}"
    
    with console.status("[bold green]Analyzing existing structured data..."):
        try:
            validator = SchemaValidator()
            analysis = validator.analyze_existing_structured_data(product_url)
            
        except ValidationError as e:
            console.print(f"[red]Validation error: {e}[/red]")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]Error during analysis: {e}[/red]")
            raise click.Abort()
    
    # Display results
    _display_analysis(analysis, product_url, detailed, google_check)
    
    # Save to file if requested
    if output:
        _save_analysis(analysis, output)

def _display_analysis(analysis: dict, product_url: str, detailed: bool = False, google_check: bool = False):
    """Display comprehensive analysis results"""
    
    console.print(f"\n[bold blue]Schema Analysis Report[/bold blue]")
    console.print(f"[blue]URL:[/blue] {product_url}")
    console.print(f"[blue]Analyzed at:[/blue] {analysis.get('timestamp', 'Unknown')}\n")
    
    if 'error' in analysis:
        console.print(Panel(f"[red]{analysis['error']}[/red]", title="Error", border_style="red"))
        return
    
    # Summary statistics
    _display_summary_stats(analysis)
    
    # Schema type breakdown
    _display_schema_breakdown(analysis)
    
    # Missing elements analysis
    _display_missing_elements(analysis)
    
    # Detailed schema information
    if detailed:
        _display_detailed_schemas(analysis)
    
    # Google Rich Results check
    if google_check:
        _display_google_compatibility(analysis)
    
    # Recommendations
    _display_recommendations(analysis)

def _display_summary_stats(analysis: dict):
    """Display summary statistics"""
    
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")
    
    # Basic stats
    schema_count = analysis.get('found_schemas', 0)
    table.add_row("JSON-LD Schemas Found", str(schema_count), "✓" if schema_count > 0 else "⚠")
    
    microdata_count = analysis.get('microdata_items', 0)
    table.add_row("Microdata Items", str(microdata_count), "✓" if microdata_count > 0 else "○")
    
    rdfa_count = analysis.get('rdfa_items', 0)
    table.add_row("RDFa Items", str(rdfa_count), "✓" if rdfa_count > 0 else "○")
    
    # Schema types
    has_product = analysis.get('has_product_schema', False)
    table.add_row("Product Schema", "Present" if has_product else "Missing", "✓" if has_product else "✗")
    
    console.print(table)

def _display_schema_breakdown(analysis: dict):
    """Display breakdown of schema types found"""
    
    analysis_data = analysis.get('analysis', {})
    schema_types = analysis_data.get('schema_types_found', [])
    
    if not schema_types:
        console.print("\n[yellow]No structured data schemas detected[/yellow]")
        return
    
    console.print(f"\n[bold blue]Schema Types Found:[/bold blue]")
    
    table = Table()
    table.add_column("Schema Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Importance", style="yellow")
    
    # Define importance levels
    importance_map = {
        'Product': 'Critical for e-commerce',
        'Organization': 'Important for brand',
        'BreadcrumbList': 'Good for navigation',
        'FAQPage': 'Helpful for SEO',
        'Review': 'Boosts trust',
        'AggregateRating': 'Improves CTR'
    }
    
    # Check common schema types
    schema_checks = {
        'Product': analysis_data.get('has_product', False),
        'Organization': analysis_data.get('has_organization', False),
        'BreadcrumbList': analysis_data.get('has_breadcrumb', False),
        'FAQPage': analysis_data.get('has_faq', False),
        'Review': analysis_data.get('has_review', False)
    }
    
    for schema_type, present in schema_checks.items():
        status = "✓ Present" if present else "✗ Missing"
        importance = importance_map.get(schema_type, 'Optional')
        table.add_row(schema_type, status, importance)
    
    console.print(table)

def _display_missing_elements(analysis: dict):
    """Display missing required elements"""
    
    analysis_data = analysis.get('analysis', {})
    missing_fields = analysis_data.get('missing_fields', [])
    
    if missing_fields:
        console.print(f"\n[bold yellow]Missing Required Fields:[/bold yellow]")
        for field in missing_fields:
            console.print(f"  [red]✗[/red] {field}")
    else:
        console.print(f"\n[green]✓ All required fields are present[/green]")

def _display_detailed_schemas(analysis: dict):
    """Display detailed schema information"""
    
    schemas = analysis.get('schemas', [])
    
    if not schemas:
        return
    
    console.print(f"\n[bold blue]Detailed Schema Information:[/bold blue]")
    
    for i, schema in enumerate(schemas):
        schema_type = schema.get('@type', 'Unknown')
        console.print(f"\n[blue]Schema {i+1}: {schema_type}[/blue]")
        
        # Create a clean version for display
        display_schema = {}
        for key, value in schema.items():
            if key.startswith('@'):
                display_schema[key] = value
            elif isinstance(value, (str, int, float, bool)):
                display_schema[key] = value
            elif isinstance(value, list):
                display_schema[key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                display_schema[key] = "[object]"
        
        console.print(JSON.from_data(display_schema, indent=2))

def _display_google_compatibility(analysis: dict):
    """Display Google Rich Results compatibility"""
    
    console.print(f"\n[bold blue]Google Rich Results Compatibility:[/bold blue]")
    
    validator = SchemaValidator()
    schemas = analysis.get('schemas', [])
    
    if not schemas:
        console.print("[yellow]No schemas to check[/yellow]")
        return
    
    table = Table()
    table.add_column("Schema", style="cyan")
    table.add_column("Google Compatible", style="green")
    table.add_column("Issues", style="red")
    
    for schema in schemas:
        schema_type = schema.get('@type', 'Unknown')
        google_result = validator.validate_against_google_requirements(schema)
        
        compatible = "✓" if google_result['eligible_for_rich_results'] else "✗"
        issues = len(google_result['errors'])
        issues_text = f"{issues} errors" if issues > 0 else "None"
        
        table.add_row(schema_type, compatible, issues_text)
    
    console.print(table)

def _display_recommendations(analysis: dict):
    """Display actionable recommendations"""
    
    recommendations = _generate_recommendations(analysis)
    
    if not recommendations:
        console.print(f"\n[green]✓ Your structured data looks good![/green]")
        return
    
    console.print(f"\n[bold yellow]Recommendations for Improvement:[/bold yellow]")
    
    for i, rec in enumerate(recommendations, 1):
        priority = rec.get('priority', 'Medium')
        color = {'High': 'red', 'Medium': 'yellow', 'Low': 'blue'}.get(priority, 'white')
        
        console.print(f"  [bold]{i}.[/bold] [{color}][{priority}][/{color}] {rec['message']}")
        
        if rec.get('details'):
            console.print(f"     [dim]{rec['details']}[/dim]")

def _generate_recommendations(analysis: dict) -> list:
    """Generate actionable recommendations based on analysis"""
    
    recommendations = []
    analysis_data = analysis.get('analysis', {})
    
    # Critical recommendations
    if not analysis_data.get('has_product'):
        recommendations.append({
            'priority': 'High',
            'message': 'Add Product schema markup',
            'details': 'Product schema is essential for e-commerce SEO and rich snippets'
        })
    
    if not analysis_data.get('has_organization'):
        recommendations.append({
            'priority': 'Medium',
            'message': 'Add Organization schema',
            'details': 'Helps establish brand authority and enables business rich snippets'
        })
    
    if not analysis_data.get('has_breadcrumb'):
        recommendations.append({
            'priority': 'Medium',
            'message': 'Add BreadcrumbList schema',
            'details': 'Improves navigation understanding and search result appearance'
        })
    
    # Missing fields
    missing_fields = analysis_data.get('missing_fields', [])
    if missing_fields:
        recommendations.append({
            'priority': 'High',
            'message': f'Complete {len(missing_fields)} missing required fields',
            'details': f'Missing: {", ".join(missing_fields[:3])}{"..." if len(missing_fields) > 3 else ""}'
        })
    
    # Enhancement recommendations
    if not analysis_data.get('has_faq'):
        recommendations.append({
            'priority': 'Low',
            'message': 'Consider adding FAQ schema',
            'details': 'FAQ schema can improve search visibility and user experience'
        })
    
    if not analysis_data.get('has_review'):
        recommendations.append({
            'priority': 'Medium',
            'message': 'Add review/rating schema',
            'details': 'Review schema significantly improves click-through rates'
        })
    
    # No structured data at all
    if analysis.get('found_schemas', 0) == 0:
        recommendations.append({
            'priority': 'High',
            'message': 'Implement structured data markup',
            'details': 'No structured data found. This is a major SEO opportunity.'
        })
    
    return recommendations

def _save_analysis(analysis: dict, output_path: str):
    """Save analysis results to file"""
    
    try:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[green]✓ Analysis saved to {output_path}[/green]")
        
    except Exception as e:
        console.print(f"\n[red]Error saving analysis: {e}[/red]")