#!/usr/bin/env python3
"""
Web Application for Shopify Schema Generator
"""

import os
import json
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import traceback

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

try:
    from core.config import SchemaConfig
    from core.generator import SchemaGenerator
    from ai.enhancer import AIEnhancer
    from validation.schema_validator import SchemaValidator
    from utils.exceptions import SchemaGeneratorError, ValidationError
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Configuration
# Use absolute path to ensure consistency regardless of working directory
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
ALLOWED_EXTENSIONS = {'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
print(f"Upload folder: {UPLOAD_FOLDER}")
print(f"Current working directory: {os.getcwd()}")

# Also create a symlink or copy files to the project root uploads folder for compatibility
project_root_uploads = os.path.abspath('uploads')
if not os.path.exists(project_root_uploads):
    os.makedirs(project_root_uploads, exist_ok=True)
print(f"Project root uploads: {project_root_uploads}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate_schemas():
    """Generate structured data schemas"""
    if request.method == 'GET':
        return render_template('generate.html')
    
    try:
        data = request.get_json()
        
        # Extract parameters
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token') or os.getenv('SHOPIFY_ACCESS_TOKEN')
        openai_key = data.get('openai_key') or os.getenv('OPENAI_API_KEY')
        limit = int(data.get('limit', 50))
        include_analysis = data.get('include_analysis', False)
        enable_ai = data.get('enable_ai', False)
        include_reviews = data.get('include_reviews', False)
        
        if not shop_domain:
            return jsonify({'error': 'Shop domain is required'}), 400
        
        if not access_token:
            return jsonify({'error': 'Shopify access token is required'}), 400
        
        # Create configuration
        config = SchemaConfig(
            shop_domain=shop_domain,
            access_token=access_token,
            openai_api_key=openai_key,
            enable_ai_features=enable_ai and bool(openai_key),
            max_products=limit,
            include_analysis=include_analysis,
            include_reviews=include_reviews
        )
        
        # Initialize components
        ai_enhancer = AIEnhancer(openai_key) if config.enable_ai_features and openai_key else None
        generator = SchemaGenerator(config, ai_enhancer)
        
        # Test connection
        shop_info = generator.client.get_shop_info()
        if not shop_info.get('name'):
            return jsonify({'error': 'Unable to connect to Shopify API'}), 400
        
        # Generate schemas
        schemas = generator.generate_complete_schema_package()
        
        # Save to temporary file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"schemas_{shop_domain}_{timestamp}.json"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schemas, f, indent=2, ensure_ascii=False)
        
        # Verify file was created
        if not os.path.exists(filepath):
            return jsonify({'error': 'Failed to save generated schemas'}), 500
        
        print(f"Generated schema file: {filepath}")
        
        response_data = {
            'success': True,
            'message': f'Successfully generated schemas for {shop_info["name"]}',
            'filename': filename,
            'filepath': filepath,
            'stats': {
                'total_schemas': len(schemas.get('products', [])),
                'shop_name': shop_info['name'],
                'generated_at': datetime.now().isoformat()
            }
        }
        
        print(f"Returning response with filename: {filename}")
        return jsonify(response_data)
        
    except SchemaGeneratorError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/analyze', methods=['GET', 'POST'])
def analyze_schemas():
    """Analyze existing structured data"""
    if request.method == 'GET':
        return render_template('analyze.html')
    
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        product_handle = data.get('product_handle')
        detailed = data.get('detailed', False)
        google_check = data.get('google_check', False)
        
        if not shop_domain or not product_handle:
            return jsonify({'error': 'Shop domain and product handle are required'}), 400
        
        product_url = f"https://{shop_domain}.myshopify.com/products/{product_handle}"
        
        validator = SchemaValidator()
        analysis = validator.analyze_existing_structured_data(product_url)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'product_url': product_url,
            'analyzed_at': datetime.now().isoformat()
        })
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/validate', methods=['GET', 'POST'])
def validate_schemas():
    """Validate schema files"""
    if request.method == 'GET':
        return render_template('validate.html')
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a JSON file.'}), 400
        
        # Read and parse JSON
        try:
            schemas = json.load(file)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON file: {str(e)}'}), 400
        
        # Get validation options
        detailed = request.form.get('detailed', 'false').lower() == 'true'
        google_check = request.form.get('google_check', 'false').lower() == 'true'
        strict = request.form.get('strict', 'false').lower() == 'true'
        schema_type = request.form.get('schema_type', 'all')
        
        # Initialize validator
        validator = SchemaValidator()
        
        # Run validation
        validation_results = run_comprehensive_validation(
            schemas, validator, schema_type, google_check, strict
        )
        
        return jsonify({
            'success': True,
            'validation_results': validation_results,
            'validated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

def run_comprehensive_validation(schemas, validator, schema_type, google_check, strict):
    """Run comprehensive validation on schemas"""
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
            'errors': [],
            'warnings': []
        }
    }
    
    # Count total schemas
    if 'organization' in schemas:
        results['file_info']['total_schemas'] += 1
    if 'products' in schemas:
        results['file_info']['total_schemas'] += len(schemas['products'])
    if 'collections' in schemas:
        results['file_info']['total_schemas'] += len(schemas['collections'])
    
    # Validate organization schema
    if schema_type in ['all', 'organization'] and 'organization' in schemas:
        try:
            org_validation = validator.validate_organization_schema(schemas['organization'])
            results['organization'] = org_validation
            results['file_info']['processed_schemas'] += 1
        except Exception as e:
            results['organization'] = {'valid': False, 'errors': [str(e)]}
    
    # Validate product schemas
    if schema_type in ['all', 'product'] and 'products' in schemas:
        for product in schemas['products']:
            try:
                product_validation = validator.validate_product_schema(product)
                results['products'].append(product_validation)
                results['file_info']['processed_schemas'] += 1
            except Exception as e:
                results['products'].append({
                    'valid': False, 
                    'errors': [str(e)],
                    'product_id': product.get('product_id', 'unknown')
                })
    
    # Update summary
    for validation in [results['organization']] + results['products']:
        if validation:
            if validation.get('valid'):
                results['summary']['total_valid'] += 1
            else:
                results['summary']['total_invalid'] += 1
            
            results['summary']['errors'].extend(validation.get('errors', []))
            results['summary']['warnings'].extend(validation.get('warnings', []))
    
    results['summary']['total_warnings'] = len(results['summary']['warnings'])
    
    return results

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated schema file"""
    try:
        # Try multiple possible locations
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], filename),  # Web uploads folder
            os.path.join(os.path.abspath('uploads'), filename),   # Project root uploads
            os.path.join('uploads', filename)                     # Relative uploads
        ]
        
        print(f"Download request for: {filename}")
        print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        
        file_path = None
        for path in possible_paths:
            print(f"Checking path: {path}")
            if os.path.exists(path) and os.path.isfile(path):
                file_path = path
                print(f"Found file at: {file_path}")
                break
        
        if not file_path:
            # List files in all possible directories for debugging
            for path in possible_paths:
                dir_path = os.path.dirname(path)
                if os.path.exists(dir_path):
                    files = os.listdir(dir_path)
                    print(f"Files in {dir_path}: {files}")
            
            return jsonify({'error': f'File not found: {filename}'}), 404
        
        # Log the download attempt
        print(f"Downloading file: {file_path}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    except FileNotFoundError:
        return jsonify({'error': f'File not found: {filename}'}), 404
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/test-download')
def test_download():
    """Test download endpoint"""
    test_file = os.path.join(app.config['UPLOAD_FOLDER'], 'test_schemas.json')
    if os.path.exists(test_file):
        return jsonify({
            'success': True,
            'message': 'Test file exists',
            'filename': 'test_schemas.json',
            'filepath': test_file
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Test file not found',
            'upload_folder': app.config['UPLOAD_FOLDER']
        })

@app.route('/test-download/<filename>')
def test_download_file(filename):
    """Test download with direct file access"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Test download for: {filename}")
        print(f"File path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/uploads')
def debug_uploads():
    """Debug endpoint to list upload directory contents"""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            return jsonify({
                'upload_directory': upload_dir,
                'files': files,
                'file_count': len(files)
            })
        else:
            return jsonify({
                'error': 'Upload directory does not exist',
                'upload_directory': upload_dir
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000) 