"""Main entry point for FastAPI application with uvicorn."""

import os
import uvicorn

if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    reload = os.environ.get('RELOAD', 'true').lower() == 'true'
    log_level = os.environ.get('LOG_LEVEL', 'info').lower()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

