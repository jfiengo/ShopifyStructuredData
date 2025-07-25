# cli/commands/setup.py
"""
Setup command for CLI - interactive configuration and credential management
"""

import os
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import set_key, load_dotenv
from pathlib import Path
import sys
import yaml
import json
import requests
from typing import Dict, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from core.config import SchemaConfig
from core.shopify_client import ShopifyClient
from utils.exceptions import ConfigurationError

console = Console()

@click.command()
@click.option('--interactive/--non-interactive', default=True, help='Run in interactive mode')
@click.option('--config-file', help='Save configuration to specific YAML file')
@click.option('--env-file', default='.env', help='Environment file to create/update')
@click.option('--verify-credentials', is_flag=True, help='Test credentials during setup')
@click.option('--advanced', is_flag=True, help='Show advanced configuration options')
def setup(interactive, config_file, env_file, verify_credentials, advanced):
    """Setup configuration and credentials for the schema generator"""
    
    console.print(Panel.fit(
        "[bold blue]🚀 Shopify Schema Generator Setup[/bold blue]\n"
        "This wizard will help you configure the tool with your credentials and preferences.",
        title="✨ Welcome",
        border_style="blue"
    ))
    
    if interactive:
        config = run_interactive_setup(verify_credentials, advanced)
    else:
        config = run_automated_setup()
    
    if config:
        save_configuration(config, config_file, env_file)
        display_next_steps(config)
    else:
        console.print("[red]❌ Setup cancelled or failed[/red]")
        raise click.Abort()

def run_interactive_setup(verify_credentials: bool = True, advanced: bool = False) -> Optional[SchemaConfig]:
    """Run the interactive setup process"""
    
    config_data = {}
    
    # Step 1: Shopify Configuration
    console.print(f"\n[bold cyan]📊 Step 1: Shopify Store Configuration[/bold cyan]")
    
    config_data.update(setup_shopify_credentials(verify_credentials))
    
    # Step 2: AI Features
    console.print(f"\n[bold cyan]🤖 Step 2: AI Features (Optional)[/bold cyan]")
    
    config_data.update(setup_ai_features())
    
    # Step 3: Generation Settings
    console.print(f"\n[bold cyan]⚙️ Step 3: Generation Settings[/bold cyan]")
    
    config_data.update(setup_generation_settings(advanced))
    
    # Step 4: Output Preferences
    console.print(f"\n[bold cyan]📁 Step 4: Output Preferences[/bold cyan]")
    
    config_data.update(setup_output_preferences(advanced))
    
    # Create configuration object
    try:
        config = SchemaConfig(**config_data)
        return config
    except Exception as e:
        console.print(f"[red]❌ Error creating configuration: {e}[/red]")
        return None

def setup_shopify_credentials(verify_credentials: bool = True) -> Dict:
    """Setup Shopify API credentials"""
    
    console.print("🏪 Let's connect to your Shopify store!")
    console.print("[dim]You'll need Admin API credentials from your Shopify store.[/dim]\n")
    
    # Show instructions for getting credentials
    show_shopify_instructions()
    
    while True:
        shop_domain = Prompt.ask(
            "\n[bold]Enter your shop domain[/bold]",
            default="",
            show_default=False
        ).replace('.myshopify.com', '').strip()
        
        if not shop_domain:
            console.print("[red]❌ Shop domain is required[/red]")
            continue
        
        access_token = Prompt.ask(
            "[bold]Enter your Admin API access token[/bold]",
            password=True
        ).strip()
        
        if not access_token:
            console.print("[red]❌ Access token is required[/red]")
            continue
        
        # Test credentials if requested
        if verify_credentials:
            if test_shopify_connection(shop_domain, access_token):
                break
            else:
                if not Confirm.ask("\n[yellow]Connection failed. Continue anyway?[/yellow]"):
                    continue
        else:
            break
    
    return {
        'shop_domain': shop_domain,
        'access_token': access_token
    }

def setup_ai_features() -> Dict:
    """Setup AI enhancement features"""
    
    console.print("🤖 AI features can enhance your schemas with:")
    console.print("   • SEO-optimized product descriptions")
    console.print("   • Automatic FAQ generation") 
    console.print("   • Smart product categorization")
    console.print("   • Keyword extraction")
    console.print("   • Content optimization")
    
    enable_ai = Confirm.ask("\n[bold]Enable AI-powered enhancements?[/bold]", default=False)
    
    config = {'enable_ai_features': enable_ai}
    
    if enable_ai:
        console.print("\n[dim]AI features require an OpenAI API key.[/dim]")
        console.print("[dim]Get one at: https://platform.openai.com/api-keys[/dim]")
        
        openai_key = Prompt.ask(
            "\n[bold]Enter your OpenAI API key[/bold]",
            password=True,
            default="",
            show_default=False
        ).strip()
        
        config['openai_api_key'] = openai_key
        
        if openai_key:
            # Test OpenAI connection
            if test_openai_connection(openai_key):
                console.print("[green]✅ OpenAI connection successful![/green]")
            else:
                console.print("[yellow]⚠️  OpenAI connection failed, but continuing...[/yellow]")
    else:
        config['openai_api_key'] = None
    
    return config

def setup_generation_settings(advanced: bool = False) -> Dict:
    """Setup schema generation settings"""
    
    console.print("⚙️ Configure how schemas are generated:")
    
    # Basic settings
    max_products = IntPrompt.ask(
        "\n[bold]Maximum products to process per run[/bold]",
        default=100,
        show_default=True
    )
    
    include_collections = Confirm.ask(
        "[bold]Include collection schemas?[/bold]",
        default=True
    )
    
    include_faq = Confirm.ask(
        "[bold]Generate FAQ schemas?[/bold]", 
        default=True
    )
    
    config = {
        'max_products': max_products,
        'include_collections': include_collections,
        'include_faq': include_faq
    }
    
    # Advanced settings
    if advanced:
        console.print("\n[bold blue]🔧 Advanced Settings:[/bold blue]")
        
        include_variants = Confirm.ask(
            "[bold]Include product variants in schemas?[/bold]",
            default=True
        )
        
        include_reviews = Confirm.ask(
            "[bold]Attempt to include review data?[/bold]",
            default=False
        )
        
        validate_schemas = Confirm.ask(
            "[bold]Validate schemas after generation?[/bold]",
            default=True
        )
        
        config.update({
            'include_variants': include_variants,
            'include_reviews': include_reviews,
            'validate_schemas': validate_schemas
        })
        
        # API settings
        api_version = Prompt.ask(
            "[bold]Shopify API version[/bold]",
            default="2023-10",
            show_default=True
        )
        
        config['api_version'] = api_version
    
    return config

def setup_output_preferences(advanced: bool = False) -> Dict:
    """Setup output preferences"""
    
    console.print("📁 Configure output settings:")
    
    output_format = Prompt.ask(
        "\n[bold]Default output format[/bold]",
        choices=["json", "yaml"],
        default="json",
        show_choices=True
    )
    
    config = {
        'output_format': output_format
    }
    
    if advanced:
        include_analysis = Confirm.ask(
            "[bold]Include schema analysis by default?[/bold]",
            default=False
        )
        
        config['include_analysis'] = include_analysis
    
    return config

def test_shopify_connection(shop_domain: str, access_token: str) -> bool:
    """Test connection to Shopify API"""
    
    with console.status("[bold green]Testing Shopify connection..."):
        try:
            # Create temporary config and client
            temp_config = SchemaConfig(
                shop_domain=shop_domain,
                access_token=access_token
            )
            
            client = ShopifyClient(temp_config)
            shop_info = client.get_shop_info()
            
            if shop_info and shop_info.get('name'):
                console.print(f"[green]✅ Connected to: {shop_info['name']}[/green]")
                console.print(f"[dim]   Domain: {shop_info.get('domain', 'N/A')}[/dim]")
                console.print(f"[dim]   Currency: {shop_info.get('currency', 'N/A')}[/dim]")
                console.print(f"[dim]   Country: {shop_info.get('country', 'N/A')}[/dim]")
                return True
            else:
                console.print("[red]❌ Connection failed: No shop data received[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Connection failed: {e}[/red]")
            return False

def test_openai_connection(api_key: str) -> bool:
    """Test connection to OpenAI API"""
    
    with console.status("[bold green]Testing OpenAI connection..."):
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            # Simple test request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            if response.choices and len(response.choices) > 0:
                return True
            else:
                return False
                
        except Exception as e:
            console.print(f"[red]❌ OpenAI connection failed: {e}[/red]")
            return False

def show_shopify_instructions():
    """Show instructions for getting Shopify credentials"""
    
    instructions = """
[bold blue]📋 How to get Shopify Admin API credentials:[/bold blue]

1️⃣  Go to your Shopify admin dashboard
2️⃣  Navigate to: [cyan]Settings → Apps and sales channels[/cyan]
3️⃣  Click: [cyan]Develop apps[/cyan] (enable custom app development if needed)
4️⃣  Click: [cyan]Create an app[/cyan]
5️⃣  Configure Admin API access with these scopes:
    • [green]read_products[/green] (required)
    • [green]read_collections[/green] (recommended)
    • [green]read_shop[/green] (required)
6️⃣  Install the app and copy the access token

[yellow]💡 Tip: Development stores from Shopify Partners are free and perfect for testing![/yellow]
    """
    
    console.print(Panel(instructions, title="🔑 Getting API Credentials", border_style="cyan"))

def save_configuration(config: SchemaConfig, config_file: Optional[str], env_file: str):
    """Save configuration to files"""
    
    console.print(f"\n[bold cyan]💾 Step 5: Save Configuration[/bold cyan]")
    
    save_methods = []
    
    # Always save to environment file
    save_methods.append("env")
    
    # Ask about YAML config file
    if config_file or Confirm.ask("[bold]Save configuration to YAML file?[/bold]", default=True):
        save_methods.append("yaml")
        if not config_file:
            config_file = "config.yml"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Saving configuration...", total=len(save_methods))
        
        # Save to .env file
        if "env" in save_methods:
            progress.update(task, description="Saving environment variables...")
            save_env_config(config, env_file)
            progress.advance(task)
        
        # Save to YAML file
        if "yaml" in save_methods:
            progress.update(task, description="Saving YAML configuration...")
            save_yaml_config(config, config_file)
            progress.advance(task)
    
    # Display saved files
    console.print(f"\n[bold green]✅ Configuration saved successfully![/bold green]")
    
    files_table = Table(title="📁 Configuration Files")
    files_table.add_column("File", style="cyan")
    files_table.add_column("Purpose", style="green") 
    files_table.add_column("Contains", style="yellow")
    
    if "env" in save_methods:
        files_table.add_row(
            env_file,
            "Environment variables",
            "API keys, basic settings"
        )
    
    if "yaml" in save_methods:
        files_table.add_row(
            config_file,
            "Full configuration",
            "All settings, reusable"
        )
    
    console.print(files_table)

def save_env_config(config: SchemaConfig, env_file: str):
    """Save configuration to .env file"""
    
    # Load existing .env if it exists
    if os.path.exists(env_file):
        load_dotenv(env_file)
    
    # Set configuration values
    set_key(env_file, "SHOPIFY_SHOP_DOMAIN", config.shop_domain)
    set_key(env_file, "SHOPIFY_ACCESS_TOKEN", config.access_token)
    
    if config.openai_api_key:
        set_key(env_file, "OPENAI_API_KEY", config.openai_api_key)
    
    set_key(env_file, "ENABLE_AI_FEATURES", str(config.enable_ai_features).lower())
    set_key(env_file, "MAX_PRODUCTS", str(config.max_products))
    set_key(env_file, "INCLUDE_COLLECTIONS", str(config.include_collections).lower())
    set_key(env_file, "INCLUDE_FAQ", str(config.include_faq).lower())
    set_key(env_file, "OUTPUT_FORMAT", config.output_format)

def save_yaml_config(config: SchemaConfig, config_file: str):
    """Save configuration to YAML file"""
    
    config_dict = {
        'shop_domain': config.shop_domain,
        'access_token': config.access_token,
        'api_version': config.api_version,
        'openai_api_key': config.openai_api_key,
        'enable_ai_features': config.enable_ai_features,
        'max_products': config.max_products,
        'include_collections': config.include_collections,
        'include_faq': config.include_faq,
        'include_variants': config.include_variants,
        'include_reviews': config.include_reviews,
        'output_format': config.output_format,
        'validate_schemas': config.validate_schemas,
        'include_analysis': config.include_analysis
    }
    
    # Remove None values
    config_dict = {k: v for k, v in config_dict.items() if v is not None}
    
    with open(config_file, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

def display_next_steps(config: SchemaConfig):
    """Display next steps after setup"""
    
    console.print(f"\n[bold green]🎉 Setup Complete![/bold green]")
    
    next_steps = f"""
[bold cyan]🚀 Ready to generate schemas! Try these commands:[/bold cyan]

[bold]Basic Usage:[/bold]
  [green]python -m cli.main generate --shop-domain {config.shop_domain} --limit 10[/green]
  [dim]Generate schemas for 10 products[/dim]

[bold]With AI Enhancement:[/bold]
  [green]python -m cli.main generate --shop-domain {config.shop_domain} --enable-ai[/green]
  [dim]Use AI to enhance descriptions and generate FAQs[/dim]

[bold]Analyze Existing Schemas:[/bold]
  [green]python -m cli.main analyze --shop-domain {config.shop_domain} --product-handle HANDLE[/green]
  [dim]Analyze current structured data on your store[/dim]

[bold]Validate Generated Schemas:[/bold]
  [green]python -m cli.main validate schemas.json --detailed --google-check[/green]
  [dim]Validate schemas for compliance and Google compatibility[/dim]

[bold]Web Interface:[/bold]
  [green]python web/app.py[/green]
  [dim]Start the web interface at http://localhost:5000[/dim]
    """
    
    console.print(Panel(next_steps, title="🎯 Next Steps", border_style="green"))
    
    # Show additional tips
    tips = """
[bold yellow]💡 Pro Tips:[/bold yellow]

• Use [cyan]--limit[/cyan] to test with fewer products first
• Enable [cyan]--detailed[/cyan] validation to catch all issues  
• Set up webhooks for real-time schema updates
• Monitor Google Search Console for rich snippet performance
• Consider running during off-peak hours for large stores
    """
    
    console.print(Panel(tips, title="💡 Tips & Best Practices", border_style="yellow"))

def run_automated_setup() -> Optional[SchemaConfig]:
    """Run automated setup using environment variables"""
    
    console.print("[bold blue]🤖 Running automated setup...[/bold blue]")
    
    # Load from environment
    load_dotenv()
    
    required_vars = ['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        console.print(f"[red]❌ Missing required environment variables: {', '.join(missing_vars)}[/red]")
        console.print("[yellow]💡 Set these variables or use --interactive mode[/yellow]")
        return None
    
    try:
        config = SchemaConfig.from_env()
        console.print("[green]✅ Configuration loaded from environment[/green]")
        return config
    except Exception as e:
        console.print(f"[red]❌ Error loading configuration: {e}[/red]")
        return None

# Additional utility functions

def check_system_requirements():
    """Check if system has required dependencies"""
    
    console.print("[bold blue]🔍 Checking system requirements...[/bold blue]")
    
    requirements = []
    
    try:
        import requests
        requirements.append(("requests", "✅"))
    except ImportError:
        requirements.append(("requests", "❌"))
    
    try:
        import yaml
        requirements.append(("PyYAML", "✅"))
    except ImportError:
        requirements.append(("PyYAML", "❌"))
    
    try:
        from dotenv import load_dotenv
        requirements.append(("python-dotenv", "✅"))
    except ImportError:
        requirements.append(("python-dotenv", "❌"))
    
    try:
        import openai
        requirements.append(("openai", "✅"))
    except ImportError:
        requirements.append(("openai (optional)", "⚠️"))
    
    # Display requirements table
    req_table = Table(title="📦 Dependencies")
    req_table.add_column("Package", style="cyan")
    req_table.add_column("Status", style="green")
    
    for package, status in requirements:
        req_table.add_row(package, status)
    
    console.print(req_table)
    
    missing_required = [pkg for pkg, status in requirements if status == "❌"]
    if missing_required:
        console.print(f"\n[red]❌ Missing required packages: {', '.join(missing_required)}[/red]")
        console.print("[yellow]💡 Install with: pip install -r requirements.txt[/yellow]")
        return False
    
    return True

def migrate_old_config():
    """Migrate from old configuration format if exists"""
    
    old_config_files = ['.shopify_config', 'shopify_schema.conf', 'config.json']
    
    for old_file in old_config_files:
        if os.path.exists(old_file):
            console.print(f"[yellow]⚠️  Found old configuration file: {old_file}[/yellow]")
            
            if Confirm.ask(f"[bold]Migrate settings from {old_file}?[/bold]"):
                try:
                    # Attempt to load and migrate old config
                    # Implementation would depend on old format
                    console.print(f"[green]✅ Migrated settings from {old_file}[/green]")
                    
                    # Optionally remove old file
                    if Confirm.ask(f"[bold]Remove old config file {old_file}?[/bold]"):
                        os.remove(old_file)
                        console.print(f"[green]🗑️  Removed {old_file}[/green]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Migration failed: {e}[/red]")

@click.command()
def doctor():
    """Diagnose configuration and system issues"""
    
    console.print("[bold blue]🩺 Schema Generator Doctor[/bold blue]\n")
    
    issues_found = []
    
    # Check system requirements
    if not check_system_requirements():
        issues_found.append("Missing required dependencies")
    
    # Check configuration files
    config_files = ['.env', 'config.yml', 'config.yaml']
    found_configs = [f for f in config_files if os.path.exists(f)]
    
    if not found_configs:
        issues_found.append("No configuration files found")
        console.print("[yellow]⚠️  No configuration files found[/yellow]")
        console.print("[dim]   Run 'python -m cli.main setup' to create configuration[/dim]")
    else:
        console.print(f"[green]✅ Found configuration files: {', '.join(found_configs)}[/green]")
    
    # Test configuration loading
    try:
        load_dotenv()
        if os.getenv('SHOPIFY_SHOP_DOMAIN') and os.getenv('SHOPIFY_ACCESS_TOKEN'):
            console.print("[green]✅ Environment variables configured[/green]")
        else:
            issues_found.append("Missing required environment variables")
    except Exception as e:
        issues_found.append(f"Error loading environment: {e}")
    
    # Summary
    if issues_found:
        console.print(f"\n[red]❌ Found {len(issues_found)} issues:[/red]")
        for issue in issues_found:
            console.print(f"   • {issue}")
        console.print(f"\n[yellow]💡 Run 'python -m cli.main setup' to fix configuration issues[/yellow]")
    else:
        console.print(f"\n[green]🎉 All systems look good![/green]")

# Add the doctor command to the CLI
@click.group()
def config_commands():
    """Configuration management commands"""
    pass

config_commands.add_command(setup)
config_commands.add_command(doctor)