# cli/commands/validate.py
"""
Validate command for CLI - comprehensive schema validation
"""

import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.json import JSON
from rich.text import Text
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from validation.schema_validator import SchemaValidator
from utils.constants import REQUIRED_PRODUCT_FIELDS, REQUIRED_ORGANIZATION_FIELDS, GOOGLE_RICH_RESULTS_REQUIREMENTS
from utils.exceptions import ValidationError

console = Console()

@click.command()
@click.argument('schema_file', type=click.Path(exists=True))
@click.option('--detailed', is_flag=True, help='Show detailed validation results')
@click.option('--google-check', is_flag=True, help='Validate against Google Rich Results requirements')
@click.option('--output', '-o', help='Save validation report to file')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'text']), default='table', help='Output format')
@click.option('--strict', is_flag=True, help='Strict validation mode (warnings become errors)')
@click.option('--schema-type', type=click.Choice(['all', 'product', 'organization', 'breadcrumb', 'faq']), default='all', help='Validate specific schema types only')
def validate(schema_file, detailed, google_check, output, output_format, strict, schema_type):
    """Validate generated schemas for compliance and completeness"""
    
    console.print(f"[bold blue]🔍 Validating schemas from {schema_file}[/bold blue]\n")
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid JSON file: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Error reading file: {e}[/red]")
        raise click.Abort()
    
    # Initialize validator
    validator = SchemaValidator()
    
    # Run validation
    validation_results = run_comprehensive_validation(
        schemas, validator, schema_type, google_check, strict
    )
    
    # Display results based on format
    if output_format == 'table':
        display_validation_table(validation_results, detailed)
    elif output_format == 'json':
        display_validation_json(validation_results)
    else:  # text
        display_validation_text(validation_results, detailed)
    
    # Show summary
    display_validation_summary(validation_results, google_check)
    
    # Save report if requested
    if output:
        save_validation_report(validation_results, output, output_format)
    
    # Exit code based on results
    if has_validation_errors(validation_results, strict):
        console.print(f"\n[red]❌ Validation failed![/red]")
        raise click.Abort()
    else:
        console.print(f"\n[green]✅ Validation passed![/green]")

def run_comprehensive_validation(
    schemas: Dict, 
    validator: SchemaValidator, 
    schema_type: str, 
    google_check: bool,
    strict: bool
) -> Dict:
    """Run comprehensive validation on all schemas"""
    
    results = {
        'file_info': {
            'total_schemas': 0,
            'processed_schemas': 0,
            'validation_time': None
        },
        'organization': None,
        'products': [],
        'collections': [],
        'summary': {
            'total_valid': 0,
            'total_invalid': 0,
            'total_warnings': 0,
            'total_errors': 0
        },
        'google_compatibility': []
    }
    
    from datetime import datetime
    start_time = datetime.now()
    
    # Count total schemas
    total_count = 0
    if 'organization' in schemas and (schema_type in ['all', 'organization']):
        total_count += 1
    if 'products' in schemas and (schema_type in ['all', 'product']):
        total_count += len(schemas['products'])
    if 'collections' in schemas and (schema_type in ['all', 'collection']):
        total_count += len(schemas['collections'])
    
    results['file_info']['total_schemas'] = total_count
    
    # Validate organization schema
    if 'organization' in schemas and schema_type in ['all', 'organization']:
        console.print("🏢 Validating organization schema...")
        org_result = validator.validate_organization_schema(schemas['organization'])
        org_result['schema_data'] = schemas['organization']
        results['organization'] = org_result
        
        _update_summary(results['summary'], org_result, strict)
        
        # Google validation for organization
        if google_check:
            google_result = validator.validate_against_google_requirements(schemas['organization'])
            google_result['schema_type'] = 'Organization'
            google_result['schema_name'] = schemas['organization'].get('name', 'Organization')
            results['google_compatibility'].append(google_result)
    
    # Validate product schemas
    if 'products' in schemas and schema_type in ['all', 'product']:
        products = schemas['products']
        
        for product in track(products, description="Validating products..."):
            product_result = {
                'product_id': product.get('product_id'),
                'title': product.get('title', 'Unknown Product'),
                'handle': product.get('handle', ''),
                'schemas': {}
            }
            
            # Validate each schema type in the product
            product_schemas = product.get('schemas', {})
            
            # Product schema
            if 'product' in product_schemas:
                schema_data = product_schemas['product']
                validation = validator.validate_product_schema(schema_data)
                validation['schema_data'] = schema_data
                product_result['schemas']['product'] = validation
                _update_summary(results['summary'], validation, strict)
                
                # Google validation
                if google_check:
                    google_result = validator.validate_against_google_requirements(schema_data)
                    google_result['schema_type'] = 'Product'
                    google_result['schema_name'] = product.get('title', 'Product')
                    results['google_compatibility'].append(google_result)
            
            # Breadcrumb schema
            if 'breadcrumb' in product_schemas and schema_type in ['all', 'breadcrumb']:
                schema_data = product_schemas['breadcrumb']
                validation = validator.validate_breadcrumb_schema(schema_data)
                validation['schema_data'] = schema_data
                product_result['schemas']['breadcrumb'] = validation
                _update_summary(results['summary'], validation, strict)
            
            # FAQ schema
            if 'faq' in product_schemas and schema_type in ['all', 'faq']:
                schema_data = product_schemas['faq']
                validation = validator.validate_faq_schema(schema_data)
                validation['schema_data'] = schema_data
                product_result['schemas']['faq'] = validation
                _update_summary(results['summary'], validation, strict)
            
            results['products'].append(product_result)
    
    # Validate collection schemas
    if 'collections' in schemas and schema_type in ['all', 'collection']:
        collections = schemas.get('collections', [])
        
        for collection in track(collections, description="Validating collections..."):
            # Handle both old format (direct schema) and new format (with metadata)
            if collection.get('@type') == 'CollectionPage':
                # Old format: collection is the schema directly
                schema_data = collection
                collection_result = {
                    'collection_id': None,
                    'title': collection.get('name', 'Unknown Collection'),
                    'handle': None,
                    'valid': True,
                    'errors': [],
                    'warnings': []
                }
            else:
                # New format: collection has metadata with schema field
                collection_result = {
                    'collection_id': collection.get('collection_id'),
                    'title': collection.get('title', 'Unknown Collection'),
                    'handle': collection.get('handle', ''),
                    'valid': True,
                    'errors': [],
                    'warnings': []
                }
                schema_data = collection.get('schema', {})
            
            # Basic collection schema validation
            if schema_data:
                if schema_data.get('@type') != 'CollectionPage':
                    collection_result['errors'].append("Schema type should be 'CollectionPage'")
                    collection_result['valid'] = False
                
                if not schema_data.get('name'):
                    collection_result['errors'].append("Missing collection name")
                    collection_result['valid'] = False
            else:
                collection_result['errors'].append("No schema data found")
                collection_result['valid'] = False
            
            collection_result['schema_data'] = schema_data
            results['collections'].append(collection_result)
            _update_summary(results['summary'], collection_result, strict)
    
    # Calculate validation time
    end_time = datetime.now()
    results['file_info']['validation_time'] = (end_time - start_time).total_seconds()
    results['file_info']['processed_schemas'] = (
        (1 if results['organization'] else 0) +
        len(results['products']) +
        len(results['collections'])
    )
    
    return results

def display_validation_table(results: Dict, detailed: bool = False):
    """Display validation results in table format"""
    
    # Main results table
    table = Table(title="📋 Schema Validation Results")
    table.add_column("Schema Type", style="cyan", min_width=12)
    table.add_column("Name", style="blue", min_width=20)
    table.add_column("Status", style="green", min_width=8)
    table.add_column("Errors", style="red", min_width=6)
    table.add_column("Warnings", style="yellow", min_width=8)
    
    # Organization
    if results['organization']:
        org = results['organization']
        status = "✅ Valid" if org['valid'] else "❌ Invalid"
        table.add_row(
            "Organization",
            org.get('schema_data', {}).get('name', 'Organization')[:20],
            status,
            str(len(org.get('errors', []))),
            str(len(org.get('warnings', [])))
        )
    
    # Products
    for product in results['products']:
        for schema_type, validation in product['schemas'].items():
            status = "✅ Valid" if validation['valid'] else "❌ Invalid"
            product_name = product['title'][:20] + ("..." if len(product['title']) > 20 else "")
            
            table.add_row(
                f"Product ({schema_type})",
                product_name,
                status,
                str(len(validation.get('errors', []))),
                str(len(validation.get('warnings', [])))
            )
    
    # Collections
    for collection in results['collections']:
        status = "✅ Valid" if collection['valid'] else "❌ Invalid"
        collection_name = collection['title'][:20] + ("..." if len(collection['title']) > 20 else "")
        
        table.add_row(
            "Collection",
            collection_name,
            status,
            str(len(collection.get('errors', []))),
            str(len(collection.get('warnings', [])))
        )
    
    console.print(table)
    
    # Detailed error display
    if detailed:
        display_detailed_errors(results)

def display_detailed_errors(results: Dict):
    """Display detailed error information"""
    
    console.print(f"\n[bold blue]📝 Detailed Validation Issues[/bold blue]")
    
    # Organization errors
    if results['organization'] and (results['organization'].get('errors') or results['organization'].get('warnings')):
        console.print(f"\n[bold cyan]🏢 Organization Schema Issues:[/bold cyan]")
        _display_schema_issues(results['organization'])
    
    # Product errors
    for product in results['products']:
        has_issues = any(
            schema.get('errors') or schema.get('warnings') 
            for schema in product['schemas'].values()
        )
        
        if has_issues:
            console.print(f"\n[bold cyan]📦 Product: {product['title']}[/bold cyan]")
            for schema_type, validation in product['schemas'].items():
                if validation.get('errors') or validation.get('warnings'):
                    console.print(f"  [blue]{schema_type.title()} Schema:[/blue]")
                    _display_schema_issues(validation, indent="    ")
    
    # Collection errors
    for collection in results['collections']:
        if collection.get('errors') or collection.get('warnings'):
            console.print(f"\n[bold cyan]📁 Collection: {collection['title']}[/bold cyan]")
            _display_schema_issues(collection)

def _display_schema_issues(validation: Dict, indent: str = "  "):
    """Display errors and warnings for a schema"""
    
    for error in validation.get('errors', []):
        console.print(f"{indent}[red]❌ {error}[/red]")
    
    for warning in validation.get('warnings', []):
        console.print(f"{indent}[yellow]⚠️  {warning}[/yellow]")

def display_validation_json(results: Dict):
    """Display validation results in JSON format"""
    
    # Create a clean JSON structure for output
    clean_results = {
        'summary': results['summary'],
        'file_info': results['file_info'],
        'validation_results': {}
    }
    
    if results['organization']:
        clean_results['validation_results']['organization'] = {
            'valid': results['organization']['valid'],
            'errors': results['organization'].get('errors', []),
            'warnings': results['organization'].get('warnings', [])
        }
    
    clean_results['validation_results']['products'] = []
    for product in results['products']:
        product_result = {
            'title': product['title'],
            'handle': product['handle'],
            'schemas': {}
        }
        
        for schema_type, validation in product['schemas'].items():
            product_result['schemas'][schema_type] = {
                'valid': validation['valid'],
                'errors': validation.get('errors', []),
                'warnings': validation.get('warnings', [])
            }
        
        clean_results['validation_results']['products'].append(product_result)
    
    if results['google_compatibility']:
        clean_results['google_compatibility'] = results['google_compatibility']
    
    console.print(JSON.from_data(clean_results))

def display_validation_text(results: Dict, detailed: bool = False):
    """Display validation results in plain text format"""
    
    console.print("SCHEMA VALIDATION REPORT")
    console.print("=" * 50)
    
    # Summary
    summary = results['summary']
    console.print(f"Total Valid: {summary['total_valid']}")
    console.print(f"Total Invalid: {summary['total_invalid']}")
    console.print(f"Total Errors: {summary['total_errors']}")
    console.print(f"Total Warnings: {summary['total_warnings']}")
    console.print()
    
    # Individual results
    if results['organization']:
        org = results['organization']
        status = "VALID" if org['valid'] else "INVALID"
        console.print(f"Organization Schema: {status}")
        if detailed and (org.get('errors') or org.get('warnings')):
            for error in org.get('errors', []):
                console.print(f"  ERROR: {error}")
            for warning in org.get('warnings', []):
                console.print(f"  WARNING: {warning}")
        console.print()
    
    # Products
    for product in results['products']:
        console.print(f"Product: {product['title']}")
        for schema_type, validation in product['schemas'].items():
            status = "VALID" if validation['valid'] else "INVALID"
            console.print(f"  {schema_type.title()} Schema: {status}")
            if detailed and (validation.get('errors') or validation.get('warnings')):
                for error in validation.get('errors', []):
                    console.print(f"    ERROR: {error}")
                for warning in validation.get('warnings', []):
                    console.print(f"    WARNING: {warning}")
        console.print()

def display_validation_summary(results: Dict, google_check: bool):
    """Display validation summary"""
    
    summary = results['summary']
    file_info = results['file_info']
    
    # Create summary panel
    summary_text = f"""
[bold green]✅ Valid Schemas:[/bold green] {summary['total_valid']}
[bold red]❌ Invalid Schemas:[/bold red] {summary['total_invalid']}
[bold yellow]⚠️  Total Warnings:[/bold yellow] {summary['total_warnings']}
[bold red]🚨 Total Errors:[/bold red] {summary['total_errors']}

[dim]Processed {file_info['processed_schemas']} schemas in {file_info['validation_time']:.2f}s[/dim]
    """.strip()
    
    console.print(Panel(summary_text, title="📊 Validation Summary", border_style="blue"))
    
    # Google compatibility summary
    if google_check and results['google_compatibility']:
        google_eligible = sum(1 for g in results['google_compatibility'] if g.get('eligible_for_rich_results', False))
        total_google_checked = len(results['google_compatibility'])
        
        google_text = f"""
[bold green]🎯 Rich Results Eligible:[/bold green] {google_eligible}/{total_google_checked}
[dim]Schemas that meet Google's Rich Results requirements[/dim]
        """.strip()
        
        console.print(Panel(google_text, title="🔍 Google Rich Results Compatibility", border_style="green"))

def save_validation_report(results: Dict, output_path: str, output_format: str):
    """Save validation report to file"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format == 'json':
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            else:
                # Save as text report
                f.write("SHOPIFY SCHEMA VALIDATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                # Write summary
                summary = results['summary']
                f.write(f"SUMMARY:\n")
                f.write(f"  Valid Schemas: {summary['total_valid']}\n")
                f.write(f"  Invalid Schemas: {summary['total_invalid']}\n")
                f.write(f"  Total Errors: {summary['total_errors']}\n")
                f.write(f"  Total Warnings: {summary['total_warnings']}\n\n")
                
                # Write detailed results
                if results['organization']:
                    org = results['organization']
                    f.write(f"ORGANIZATION SCHEMA:\n")
                    f.write(f"  Status: {'VALID' if org['valid'] else 'INVALID'}\n")
                    for error in org.get('errors', []):
                        f.write(f"  ERROR: {error}\n")
                    for warning in org.get('warnings', []):
                        f.write(f"  WARNING: {warning}\n")
                    f.write("\n")
                
                # Write product results
                for product in results['products']:
                    f.write(f"PRODUCT: {product['title']}\n")
                    for schema_type, validation in product['schemas'].items():
                        f.write(f"  {schema_type.upper()} SCHEMA: {'VALID' if validation['valid'] else 'INVALID'}\n")
                        for error in validation.get('errors', []):
                            f.write(f"    ERROR: {error}\n")
                        for warning in validation.get('warnings', []):
                            f.write(f"    WARNING: {warning}\n")
                    f.write("\n")
        
        console.print(f"[green]💾 Validation report saved to {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error saving report: {e}[/red]")

def _update_summary(summary: Dict, validation: Dict, strict: bool):
    """Update summary statistics"""
    
    if validation.get('valid'):
        summary['total_valid'] += 1
    else:
        summary['total_invalid'] += 1
    
    summary['total_errors'] += len(validation.get('errors', []))
    summary['total_warnings'] += len(validation.get('warnings', []))
    
    # In strict mode, warnings count as errors
    if strict:
        summary['total_errors'] += len(validation.get('warnings', []))

def has_validation_errors(results: Dict, strict: bool) -> bool:
    """Check if there are validation errors"""
    
    summary = results['summary']
    
    if summary['total_invalid'] > 0 or summary['total_errors'] > 0:
        return True
    
    # In strict mode, warnings are also errors
    if strict and summary['total_warnings'] > 0:
        return True
    
    return False

# Additional utility functions for specific validations

def validate_schema_completeness(schemas: Dict) -> List[str]:
    """Check for missing schema types"""
    
    recommendations = []
    
    if 'organization' not in schemas:
        recommendations.append("Consider adding Organization schema for better brand recognition")
    
    if 'products' not in schemas or len(schemas['products']) == 0:
        recommendations.append("No product schemas found - this is essential for e-commerce")
    
    # Check if products have all recommended schema types
    if 'products' in schemas:
        products_with_breadcrumbs = sum(1 for p in schemas['products'] if 'breadcrumb' in p.get('schemas', {}))
        products_with_faq = sum(1 for p in schemas['products'] if 'faq' in p.get('schemas', {}))
        total_products = len(schemas['products'])
        
        if products_with_breadcrumbs < total_products:
            recommendations.append(f"Only {products_with_breadcrumbs}/{total_products} products have breadcrumb schemas")
        
        if products_with_faq < total_products * 0.5:  # Less than 50% have FAQs
            recommendations.append(f"Only {products_with_faq}/{total_products} products have FAQ schemas")
    
    return recommendations

def check_google_requirements(schemas: Dict) -> Dict:
    """Check specific Google Rich Results requirements"""
    
    issues = []
    
    if 'products' in schemas:
        for product in schemas['products']:
            product_schema = product.get('schemas', {}).get('product', {})
            
            if not product_schema:
                continue
            
            # Check for required Google fields
            if not product_schema.get('image'):
                issues.append(f"Product '{product.get('title')}' missing images (required for Google)")
            
            offers = product_schema.get('offers', [])
            if not offers:
                issues.append(f"Product '{product.get('title')}' missing offers (required for Google)")
            else:
                for offer in offers if isinstance(offers, list) else [offers]:
                    if not offer.get('availability'):
                        issues.append(f"Product '{product.get('title')}' missing availability in offers")
    
    return {
        'google_ready': len(issues) == 0,
        'issues': issues,
        'total_issues': len(issues)
    }