# Shopify Structured Data Generator - Web Application

A modern web interface for the Shopify Structured Data Generator, providing an intuitive way to generate, validate, and analyze structured data schemas for your Shopify store.

## Features

- **Generate Schemas**: Create comprehensive structured data for your Shopify products and store
- **Analyze Existing**: Analyze existing structured data on your product pages
- **Validate Schemas**: Validate generated schemas for compliance and completeness
- **AI Enhancement**: Optional AI-powered content enhancement using OpenAI
- **Modern UI**: Clean, responsive interface built with Bootstrap 5
- **Real-time Feedback**: Live progress indicators and detailed results

## Quick Start

1. **Install Dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Application**:
   ```bash
   python web/app.py
   ```

3. **Access the Application**:
   Open your browser and navigate to `http://localhost:5000`

## Usage

### Generate Schemas

1. Navigate to the "Generate" page
2. Enter your Shopify store domain (without .myshopify.com)
3. Provide your Shopify Admin API access token
4. Optionally add your OpenAI API key for AI enhancements
5. Configure generation options (product limit, analysis, reviews)
6. Click "Generate Schemas"
7. Download the generated JSON file

### Analyze Existing Data

1. Navigate to the "Analyze" page
2. Enter your shop domain and product handle
3. Choose analysis options (detailed, Google check)
4. Click "Analyze Product"
5. Review the analysis results and recommendations

### Validate Schemas

1. Navigate to the "Validate" page
2. Upload a JSON file containing your schemas
3. Choose validation options (schema type, detailed, Google check, strict mode)
4. Click "Validate Schemas"
5. Review validation results and fix any issues

## Configuration

### Environment Variables

You can set these environment variables for convenience:

- `SHOPIFY_ACCESS_TOKEN`: Your default Shopify Admin API access token
- `OPENAI_API_KEY`: Your OpenAI API key for AI enhancements
- `SECRET_KEY`: Flask secret key (for production)

### File Structure

```
web/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── index.html      # Dashboard page
│   ├── generate.html   # Schema generation page
│   ├── analyze.html    # Analysis page
│   └── validate.html   # Validation page
├── uploads/            # Generated schema files (auto-created)
└── README.md           # This file
```

## API Endpoints

- `GET /` - Dashboard page
- `GET /generate` - Schema generation page
- `POST /generate` - Generate schemas
- `GET /analyze` - Analysis page
- `POST /analyze` - Analyze existing data
- `GET /validate` - Validation page
- `POST /validate` - Validate schemas
- `GET /download/<filename>` - Download generated files
- `GET /api/health` - Health check endpoint

## Development

### Running in Development Mode

The application runs in debug mode by default when executed directly:

```bash
python web/app.py
```

### Production Deployment

For production deployment:

1. Set a proper `SECRET_KEY` environment variable
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
   ```
3. Set up a reverse proxy (nginx) for SSL termination
4. Configure proper file upload limits and security headers

### Customization

- **Styling**: Modify the CSS in `templates/base.html`
- **Templates**: Edit HTML templates in the `templates/` directory
- **Functionality**: Extend the Flask routes in `app.py`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **File Upload Issues**: Check that the `uploads/` directory exists and is writable
3. **API Connection Errors**: Verify your Shopify access token and domain
4. **AI Enhancement Errors**: Ensure your OpenAI API key is valid and has credits

### Logs

The application logs to stdout/stderr. For production, consider using a proper logging configuration.

## Security Notes

- Never commit API keys or access tokens to version control
- Use environment variables for sensitive configuration
- Validate all user inputs and file uploads
- Implement proper authentication for production use
- Set appropriate file upload limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Shopify Structured Data Generator. See the main project license for details. 