#!/usr/bin/env python3
"""
Test runner for Shopify Schema Generator
Provides easy commands to run different types of tests with proper reporting
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Optional
import json

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text: str, color: str = Colors.ENDC):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text: str):
    """Print a header with formatting"""
    print_colored("=" * 60, Colors.HEADER)
    print_colored(f"  {text}", Colors.HEADER + Colors.BOLD)
    print_colored("=" * 60, Colors.HEADER)

def print_success(text: str):
    """Print success message"""
    print_colored(f"✅ {text}", Colors.OKGREEN)

def print_error(text: str):
    """Print error message"""
    print_colored(f"❌ {text}", Colors.FAIL)

def print_warning(text: str):
    """Print warning message"""
    print_colored(f"⚠️  {text}", Colors.WARNING)

def print_info(text: str):
    """Print info message"""
    print_colored(f"ℹ️  {text}", Colors.OKBLUE)

class TestRunner:
    """Main test runner class"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / 'tests'
        self.src_dir = self.project_root / 'src'
        
        # Ensure src is in Python path
        sys.path.insert(0, str(self.src_dir))
        
        # Test categories and their descriptions
        self.categories = {
            'all': 'Run all tests',
            'unit': 'Run unit tests only (fast)',
            'integration': 'Run integration tests',
            'performance': 'Run performance tests',
            'cli': 'Run CLI command tests',
            'web': 'Run web application tests',
            'ai': 'Run AI-related tests',
            'validation': 'Run schema validation tests',
            'fast': 'Run fast tests only (exclude slow ones)',
            'slow': 'Run slow tests only',
            'core': 'Run core functionality tests (config, client, generator)',
            'coverage': 'Run tests with coverage report'
        }
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print_info("Checking test dependencies...")
        
        required_packages = [
            'pytest',
            'pytest-cov',
            'pytest-mock',
            'requests',
            'rich',
            'click'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print_colored(f"  ✓ {package}", Colors.OKGREEN)
            except ImportError:
                missing_packages.append(package)
                print_colored(f"  ✗ {package}", Colors.FAIL)
        
        if missing_packages:
            print_error("Missing required packages!")
            print_info("Install them with:")
            print(f"  pip install {' '.join(missing_packages)}")
            return False
        
        print_success("All dependencies are installed!")
        return True
    
    def build_pytest_command(self, category: str, extra_args: List[str] = None) -> List[str]:
        """Build pytest command based on category"""
        
        base_cmd = [
            sys.executable, '-m', 'pytest',
            str(self.tests_dir),
            '-v',
            '--tb=short',
            '--color=yes',
            '--strict-markers'
        ]
        
        # Add coverage for certain categories
        if category in ['all', 'coverage', 'core']:
            try:
                import pytest_cov
                base_cmd.extend([
                    '--cov=src',
                    '--cov-report=term-missing',
                    '--cov-report=html:htmlcov',
                    '--cov-fail-under=70'
                ])
            except ImportError:
                print_warning("pytest-cov not available, skipping coverage")
        
        # Category-specific arguments
        category_args = {
            'unit': ['-m', 'unit'],
            'integration': ['-m', 'integration'],
            'performance': ['-m', 'performance'],
            'cli': ['tests/test_cli.py'],
            'web': ['tests/test_web_app.py'],
            'ai': ['-m', 'ai'],
            'validation': ['tests/test_validation.py'],
            'fast': ['-m', 'not slow'],
            'slow': ['-m', 'slow'],
            'core': ['tests/test_config.py', 'tests/test_shopify_client.py', 'tests/test_generator.py'],
            'coverage': []  # Already handled above
        }
        
        if category in category_args:
            base_cmd.extend(category_args[category])
        
        # Add extra arguments
        if extra_args:
            base_cmd.extend(extra_args)
        
        return base_cmd
    
    def run_tests(self, category: str = 'all', extra_args: List[str] = None, 
                  verbose: bool = False, failfast: bool = False) -> int:
        """Run tests for specified category"""
        
        print_header(f"Running {category} tests")
        
        if not self.check_dependencies():
            return 1
        
        # Build command
        cmd = self.build_pytest_command(category, extra_args)
        
        if verbose:
            cmd.append('-vv')
        
        if failfast:
            cmd.append('-x')
        
        print_info(f"Command: {' '.join(cmd)}")
        print()
        
        # Run tests
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            exit_code = result.returncode
        except KeyboardInterrupt:
            print_warning("Tests interrupted by user")
            return 130
        except Exception as e:
            print_error(f"Error running tests: {e}")
            return 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print results
        print()
        print_colored("-" * 60, Colors.HEADER)
        
        if exit_code == 0:
            print_success(f"All {category} tests passed!")
            print_success(f"Completed in {duration:.2f} seconds")
            
            # Show coverage info if available
            if category in ['all', 'coverage', 'core'] and (self.project_root / 'htmlcov').exists():
                print_info("Coverage report generated: htmlcov/index.html")
        else:
            print_error(f"Tests failed with exit code {exit_code}")
            print_error(f"Failed after {duration:.2f} seconds")
            
            # Provide helpful suggestions
            if exit_code == 1:
                print_info("Try running with --verbose for more details")
                print_info("Or run specific test files: python run_tests.py unit")
        
        return exit_code
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> int:
        """Run a specific test file or test function"""
        
        print_header(f"Running specific test: {test_path}")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short',
            '--color=yes'
        ]
        
        if verbose:
            cmd.append('-vv')
        
        print_info(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except Exception as e:
            print_error(f"Error running test: {e}")
            return 1
    
    def list_tests(self, category: str = None):
        """List available tests"""
        
        print_header("Available Tests")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.tests_dir),
            '--collect-only',
            '-q'
        ]
        
        if category and category != 'all':
            category_args = {
                'unit': ['-m', 'unit'],
                'integration': ['-m', 'integration'],
                'performance': ['-m', 'performance'],
                'fast': ['-m', 'not slow'],
                'slow': ['-m', 'slow']
            }
            if category in category_args:
                cmd.extend(category_args[category])
        
        try:
            subprocess.run(cmd, cwd=self.project_root)
        except Exception as e:
            print_error(f"Error listing tests: {e}")
    
    def clean_artifacts(self):
        """Clean test artifacts and cache files"""
        
        print_header("Cleaning test artifacts")
        
        # Directories and files to clean
        cleanup_items = [
            '.pytest_cache',
            '__pycache__',
            '.coverage',
            'htmlcov',
            '*.pyc',
            '*.pyo',
            '*/__pycache__'
        ]
        
        for item in cleanup_items:
            if item.startswith('*.'):
                # Handle glob patterns
                import glob
                for file_path in glob.glob(f"**/{item}", recursive=True):
                    try:
                        os.remove(file_path)
                        print_info(f"Removed file: {file_path}")
                    except Exception as e:
                        print_warning(f"Could not remove {file_path}: {e}")
            else:
                # Handle directories
                item_path = self.project_root / item
                if item_path.exists():
                    import shutil
                    try:
                        if item_path.is_dir():
                            shutil.rmtree(item_path)
                            print_info(f"Removed directory: {item}")
                        else:
                            item_path.unlink()
                            print_info(f"Removed file: {item}")
                    except Exception as e:
                        print_warning(f"Could not remove {item}: {e}")
        
        print_success("Cleanup completed!")
    
    def show_help(self):
        """Show help information"""
        
        print_header("Shopify Schema Generator Test Runner")
        
        print_colored("USAGE:", Colors.BOLD)
        print("  python run_tests.py [CATEGORY] [OPTIONS]")
        print()
        
        print_colored("CATEGORIES:", Colors.BOLD)
        for category, description in self.categories.items():
            print(f"  {category:<12} {description}")
        print()
        
        print_colored("OPTIONS:", Colors.BOLD)
        print("  --verbose, -v     Verbose output")
        print("  --failfast, -x    Stop on first failure")
        print("  --list, -l        List available tests")
        print("  --clean           Clean test artifacts")
        print("  --help, -h        Show this help")
        print()
        
        print_colored("EXAMPLES:", Colors.BOLD)
        print("  python run_tests.py                    # Run all tests")
        print("  python run_tests.py unit               # Run unit tests only")
        print("  python run_tests.py fast --verbose     # Run fast tests with verbose output")
        print("  python run_tests.py core --failfast    # Run core tests, stop on first failure")
        print("  python run_tests.py --list unit        # List unit tests")
        print("  python run_tests.py --clean            # Clean test artifacts")
        print()
        
        print_colored("SPECIFIC TESTS:", Colors.BOLD)
        print("  python run_tests.py tests/test_generator.py")
        print("  python run_tests.py tests/test_cli.py::test_generate_command")
        print()
        
        print_colored("COVERAGE:", Colors.BOLD)
        print("  Coverage reports are automatically generated for 'all', 'coverage', and 'core' categories")
        print("  View HTML report: open htmlcov/index.html")
        print()

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Test runner for Shopify Schema Generator",
        add_help=False
    )
    
    parser.add_argument('category', nargs='?', default='all',
                       help='Test category to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List available tests')
    parser.add_argument('--clean', action='store_true',
                       help='Clean test artifacts')
    parser.add_argument('--help', '-h', action='store_true',
                       help='Show help')
    
    # Parse known args to handle pytest arguments
    args, extra_args = parser.parse_known_args()
    
    runner = TestRunner()
    
    # Handle special commands
    if args.help:
        runner.show_help()
        return 0
    
    if args.clean:
        runner.clean_artifacts()
        return 0
    
    if args.list:
        runner.list_tests(args.category)
        return 0
    
    # Validate category
    if args.category not in runner.categories and not args.category.startswith('tests/'):
        print_error(f"Unknown category: {args.category}")
        print_info("Available categories:")
        for category in runner.categories:
            print(f"  {category}")
        return 1
    
    # Run specific test file
    if args.category.startswith('tests/'):
        return runner.run_specific_test(args.category, args.verbose)
    
    # Run category tests
    return runner.run_tests(
        category=args.category,
        extra_args=extra_args,
        verbose=args.verbose,
        failfast=args.failfast
    )

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)