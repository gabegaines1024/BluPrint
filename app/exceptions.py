"""Custom exception classes for the application."""


class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        """Initialize the exception.
        
        Args:
            message: Error message to display.
            status_code: HTTP status code for the error.
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str):
        """Initialize validation error with 400 status code.
        
        Args:
            message: Validation error message.
        """
        super().__init__(message, status_code=400)


class NotFoundError(AppError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        """Initialize not found error with 404 status code.
        
        Args:
            message: Error message.
        """
        super().__init__(message, status_code=404)

