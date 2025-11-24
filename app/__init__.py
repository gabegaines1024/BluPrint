"""Application factory and initialization."""

import logging
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

from config import config
from app.database import db, migrate
from app.cache import cache
from app.exceptions import AppError, AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    import os
    from pathlib import Path
    
    log_level = getattr(app.config, 'LOG_LEVEL', 'INFO')
    log_file = getattr(app.config, 'LOG_FILE', 'app.log')
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    if log_path.parent != Path('.'):
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging with file handler
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application."""
    
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        """Handle application-specific errors."""
        response = jsonify({
            'error': error.message,
            'status_code': error.status_code
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(error: AuthenticationError):
        """Handle authentication errors."""
        response = jsonify({
            'error': error.message,
            'status_code': error.status_code
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error: AuthorizationError):
        """Handle authorization errors."""
        response = jsonify({
            'error': error.message,
            'status_code': error.status_code
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        response = jsonify({
            'error': 'Resource not found',
            'status_code': 404
        })
        response.status_code = 404
        return response
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'Internal error: {error}', exc_info=True)
        response = jsonify({
            'error': 'An internal error occurred',
            'status_code': 500
        })
        response.status_code = 500
        return response
    
    # JWT error handlers
    @app.errorhandler(401)
    def handle_jwt_error(error):
        """Handle JWT authentication errors."""
        response = jsonify({
            'error': 'Authentication required',
            'status_code': 401
        })
        response.status_code = 401
        return response


def create_app(config_name: str = 'default') -> Flask:
    """Create and configure Flask application instance."""
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / 'frontend'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    CORS(app)
    JWTManager(app)
    Bcrypt(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.routes import auth, parts, compatibility, builds, recommendations
    app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
    app.register_blueprint(parts.bp, url_prefix='/api/v1/parts')
    app.register_blueprint(compatibility.bp, url_prefix='/api/v1/compatibility')
    app.register_blueprint(builds.bp, url_prefix='/api/v1/builds')
    app.register_blueprint(recommendations.bp, url_prefix='/api/v1/recommendations')
    
    # Serve frontend files
    @app.route('/')
    def index():
        """Serve the main HTML page."""
        return send_from_directory(str(frontend_dir), 'index.html')
    
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve static files from frontend directory."""
        # Security: prevent directory traversal
        if '..' in path:
            return jsonify({'error': 'Not found'}), 404
        
        file_path = frontend_dir / path
        
        # Check if file exists
        if file_path.exists() and file_path.is_file():
            # Determine parent directory for send_from_directory
            if path.startswith('src/'):
                return send_from_directory(str(frontend_dir / 'src'), path[4:])
            elif path.startswith('assets/'):
                return send_from_directory(str(frontend_dir / 'assets'), path[7:])
            else:
                return send_from_directory(str(frontend_dir), path)
        
        # If not found, try to serve index.html (for SPA routing)
        return send_from_directory(str(frontend_dir), 'index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring."""
        try:
            # Check database connectivity
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            app.logger.error(f'Database health check failed: {e}')
            db_status = 'unhealthy'
        
        status_code = 200 if db_status == 'healthy' else 503
        
        return jsonify({
            'status': 'ok' if db_status == 'healthy' else 'degraded',
            'database': db_status
        }), status_code
    
    return app