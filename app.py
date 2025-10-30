"""
Flask Backend for SERP Tracker
Main application file with API endpoints
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import requests
from datetime import datetime
from config import Config
from serp_api import SerpApiClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Validate configuration
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise

# Initialize SerpApi client
serp_client = SerpApiClient(
    api_key=Config.SERPAPI_KEY,
    engine=Config.SERPAPI_ENGINE,
    location=Config.SERPAPI_LOCATION,
    num_results=Config.SERPAPI_RESULTS
)

# ==================== Helper Functions ====================

def verify_recaptcha(token: str) -> bool:
    """
    Verify reCAPTCHA token with Google
    
    Args:
        token: reCAPTCHA response token
        
    Returns:
        Boolean indicating if verification was successful
    """
    if not Config.RECAPTCHA_SECRET_KEY:
        logger.warning("reCAPTCHA secret key not configured, skipping verification")
        return True  # Skip verification if not configured
    
    if not token:
        logger.warning("No reCAPTCHA token provided")
        return False
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': Config.RECAPTCHA_SECRET_KEY,
                'response': token
            },
            timeout=10
        )
        result = response.json()
        
        if not result.get('success', False):
            logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
        
        return result.get('success', False)
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {str(e)}")
        return False

def validate_input(data: dict) -> tuple:
    """
    Validate and sanitize input data
    
    Args:
        data: Request data dictionary
        
    Returns:
        Tuple of (is_valid, error_message, cleaned_data)
    """
    # Check required fields
    if not data:
        return False, "Request body is required", None
    
    # Handle both single keyword and multiple keywords
    keywords = data.get('keywords', [])
    keyword = data.get('keyword', '').strip()
    domain = data.get('domain', '').strip()
    
    # If keywords array is provided, use that; otherwise use single keyword
    if keywords and isinstance(keywords, list):
        keywords = [k.strip() for k in keywords if k and k.strip()]
        if not keywords:
            return False, "At least one keyword is required", None
        if len(keywords) > 10:
            return False, "Maximum 10 keywords allowed", None
    elif keyword:
        keywords = [keyword]
    else:
        return False, "Keyword is required", None
    
    if not domain:
        return False, "Domain is required", None
    
    # Validate keyword lengths
    for kw in keywords:
        if len(kw) > Config.MAX_KEYWORD_LENGTH:
            return False, f"Keyword '{kw[:30]}...' exceeds maximum length of {Config.MAX_KEYWORD_LENGTH} characters", None
    
    if len(domain) > Config.MAX_DOMAIN_LENGTH:
        return False, f"Domain exceeds maximum length of {Config.MAX_DOMAIN_LENGTH} characters", None
    
    # Basic domain validation (allow subdomains, paths, etc.)
    if ' ' in domain or domain.count('.') == 0:
        return False, "Invalid domain format", None
    
    cleaned_data = {
        'keywords': keywords,
        'domain': domain
    }
    
    return True, None, cleaned_data

# ==================== API Routes ====================

@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'SERP Tracker API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    """Detailed health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SERP Tracker API',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'config': {
            'serpapi_configured': bool(Config.SERPAPI_KEY),
            'engine': Config.SERPAPI_ENGINE,
            'location': Config.SERPAPI_LOCATION
        }
    }), 200

@app.route('/api/check-serp', methods=['POST'])
def check_serp():
    """
    Check SERP ranking for a domain and keyword(s)
    
    Request Body:
        {
            "keyword": "search query",  // single keyword (legacy)
            "keywords": ["query1", "query2"],  // multiple keywords
            "domain": "example.com",
            "recaptchaToken": "token"  // optional reCAPTCHA token
        }
    
    Response:
        {
            "success": true,
            "data": {
                "domain": "example.com",
                "results": [
                    {
                        "keyword": "search query",
                        "position": 5,
                        "found": true,
                        "url": "https://example.com/page",
                        "title": "Page Title",
                        "snippet": "Page description...",
                        "top_results": [...],
                        "total_results": 100
                    }
                ],
                "timestamp": "2025-10-14T12:00:00Z"
            }
        }
    """
    try:
        # Get request data
        data = request.get_json()
        logger.info(f"Received SERP check request for {data.get('domain', 'unknown')}")
        
        # Verify reCAPTCHA if token provided
        recaptcha_token = data.get('recaptchaToken')
        if recaptcha_token:
            if not verify_recaptcha(recaptcha_token):
                logger.warning("reCAPTCHA verification failed")
                return jsonify({
                    'success': False,
                    'error': 'reCAPTCHA verification failed. Please try again.'
                }), 400
        
        # Validate input
        is_valid, error_msg, cleaned_data = validate_input(data)
        if not is_valid:
            logger.warning(f"Invalid input: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        keywords = cleaned_data['keywords']
        domain = cleaned_data['domain']
        
        # Perform SERP check for each keyword
        results = []
        for keyword in keywords:
            logger.info(f"Checking SERP for keyword='{keyword}', domain='{domain}'")
            try:
                result = serp_client.find_domain_rank(keyword, domain)
                results.append(result)
            except Exception as e:
                logger.error(f"Error checking keyword '{keyword}': {str(e)}")
                results.append({
                    'keyword': keyword,
                    'domain': domain,
                    'error': str(e),
                    'found': False,
                    'position': None
                })
        
        # Return success response
        response_data = {
            'domain': domain,
            'results': results,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_keywords': len(keywords)
        }
        
        # For backward compatibility with single keyword
        if len(keywords) == 1:
            response_data.update(results[0])
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in check_serp endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ==================== Main ====================

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 8080))  # Use Render's dynamic port if available
    logger.info(f"Starting Flask server on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=Config.DEBUG
    )

