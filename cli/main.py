# cli/main.py
#!/usr/bin/env python3
"""
Command Line Interface for Shopify Schema Generator
"""

import click
from .commands.generate import generate
from .commands.analyze import analyze
from .commands.validate import validate
from .commands.setup import setup

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Shopify Structured Data Generator CLI
    
    Generate, validate, and analyze structured data schemas for Shopify stores.
    """
    pass

# Add commands to CLI group
cli.add_command(generate)
cli.add_command(analyze)
cli.add_command(validate)
cli.add_command(setup)

if __name__ == '__main__':
    cli()