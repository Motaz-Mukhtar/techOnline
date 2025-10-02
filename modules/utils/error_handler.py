from typing import Dict, List, Optional, Any, Union
from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import traceback
import logging
from datetime import datetime


class APIErrorHandler:
    """
    Standardized error response handler for consistent API responses.
    
    This class provides methods to create consistent error responses
    across all API endpoints, including validation errors, business logic errors,
    and system errors.
    """
    
    # Standard HTTP status codes
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    
    # Error categories
    ERROR_VALIDATION = 'validation_error'
    ERROR_BUSINESS_RULE = 'business_rule_error'
    ERROR_AUTHENTICATION = 'authentication_error'
    ERROR_AUTHORIZATION = 'authorization_error'
    ERROR_NOT_FOUND = 'not_found_error'
    ERROR_CONFLICT = 'conflict_error'
    ERROR_SYSTEM = 'system_error'
    ERROR_FILE_UPLOAD = 'file_upload_error'
    ERROR_STOCK = 'stock_error'
    ERROR_PAYMENT = 'payment_error'
    
    def __init__(self, logger=None):
        """
        Initialize error handler with optional logger.
        
        Args:
            logger: Python logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def success_response(self, data: Any = None, message: str = 'Success', 
                        status_code: int = HTTP_200_OK, 
                        meta: Optional[Dict] = None) -> tuple:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message (str): Success message
            status_code (int): HTTP status code
            meta (Dict, optional): Additional metadata
        
        Returns:
            tuple: (response_dict, status_code)
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': self._get_request_id()
        }
        
        if meta:
            response['meta'] = meta
        
        return jsonify(response), status_code
    
    def error_response(self, message: str, error_type: str = ERROR_SYSTEM,
                      status_code: int = HTTP_400_BAD_REQUEST,
                      errors: Optional[List[str]] = None,
                      data: Optional[Dict] = None,
                      meta: Optional[Dict] = None) -> tuple:
        """
        Create a standardized error response.
        
        Args:
            message (str): Main error message
            error_type (str): Type of error
            status_code (int): HTTP status code
            errors (List[str], optional): List of detailed errors
            data (Dict, optional): Additional error data
            meta (Dict, optional): Additional metadata
        
        Returns:
            tuple: (response_dict, status_code)
        """
        response = {
            'success': False,
            'message': message,
            'error_type': error_type,
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': self._get_request_id()
        }
        
        if errors:
            response['errors'] = errors
        
        if data:
            response['data'] = data
        
        if meta:
            response['meta'] = meta
        
        # Log error for debugging
        self.logger.error(f"API Error: {error_type} - {message}", extra={
            'status_code': status_code,
            'errors': errors,
            'request_id': self._get_request_id()
        })
        
        return jsonify(response), status_code
    
    def validation_error_response(self, message: str = 'Validation failed',
                                 errors: Optional[List[str]] = None,
                                 field_errors: Optional[Dict[str, List[str]]] = None) -> tuple:
        """
        Create a validation error response.
        
        Args:
            message (str): Main validation error message
            errors (List[str], optional): List of validation errors
            field_errors (Dict, optional): Field-specific validation errors
        
        Returns:
            tuple: (response_dict, status_code)
        """
        data = {}
        if field_errors:
            data['field_errors'] = field_errors
        
        return self.error_response(
            message=message,
            error_type=self.ERROR_VALIDATION,
            status_code=self.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
            data=data if data else None
        )
    
    def business_rule_error_response(self, message: str, 
                                   rule_violations: Optional[List[str]] = None) -> tuple:
        """
        Create a business rule violation error response.
        
        Args:
            message (str): Main business rule error message
            rule_violations (List[str], optional): List of rule violations
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_BUSINESS_RULE,
            status_code=self.HTTP_400_BAD_REQUEST,
            errors=rule_violations
        )
    
    def not_found_error_response(self, resource: str = 'Resource') -> tuple:
        """
        Create a not found error response.
        
        Args:
            resource (str): Name of the resource that was not found
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=f'{resource} not found',
            error_type=self.ERROR_NOT_FOUND,
            status_code=self.HTTP_404_NOT_FOUND
        )
    
    def conflict_error_response(self, message: str, 
                               conflicting_data: Optional[Dict] = None) -> tuple:
        """
        Create a conflict error response.
        
        Args:
            message (str): Conflict error message
            conflicting_data (Dict, optional): Information about the conflict
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_CONFLICT,
            status_code=self.HTTP_409_CONFLICT,
            data=conflicting_data
        )
    
    def authentication_error_response(self, message: str = 'Authentication required') -> tuple:
        """
        Create an authentication error response.
        
        Args:
            message (str): Authentication error message
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_AUTHENTICATION,
            status_code=self.HTTP_401_UNAUTHORIZED
        )
    
    def authorization_error_response(self, message: str = 'Access denied') -> tuple:
        """
        Create an authorization error response.
        
        Args:
            message (str): Authorization error message
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_AUTHORIZATION,
            status_code=self.HTTP_403_FORBIDDEN
        )
    
    def file_upload_error_response(self, message: str, 
                                  file_errors: Optional[List[str]] = None) -> tuple:
        """
        Create a file upload error response.
        
        Args:
            message (str): File upload error message
            file_errors (List[str], optional): List of file-specific errors
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_FILE_UPLOAD,
            status_code=self.HTTP_400_BAD_REQUEST,
            errors=file_errors
        )
    
    def stock_error_response(self, message: str, 
                           stock_info: Optional[Dict] = None) -> tuple:
        """
        Create a stock-related error response.
        
        Args:
            message (str): Stock error message
            stock_info (Dict, optional): Stock availability information
        
        Returns:
            tuple: (response_dict, status_code)
        """
        return self.error_response(
            message=message,
            error_type=self.ERROR_STOCK,
            status_code=self.HTTP_400_BAD_REQUEST,
            data=stock_info
        )
    
    def system_error_response(self, message: str = 'Internal server error',
                             error_details: Optional[str] = None,
                             include_traceback: bool = False) -> tuple:
        """
        Create a system error response.
        
        Args:
            message (str): System error message
            error_details (str, optional): Additional error details
            include_traceback (bool): Whether to include traceback in response
        
        Returns:
            tuple: (response_dict, status_code)
        """
        data = {}
        
        if error_details:
            data['error_details'] = error_details
        
        if include_traceback:
            data['traceback'] = traceback.format_exc()
        
        # Log system error with full details
        self.logger.error(f"System Error: {message}", extra={
            'error_details': error_details,
            'traceback': traceback.format_exc(),
            'request_id': self._get_request_id()
        })
        
        return self.error_response(
            message=message,
            error_type=self.ERROR_SYSTEM,
            status_code=self.HTTP_500_INTERNAL_SERVER_ERROR,
            data=data if data else None
        )
    
    def handle_exception(self, exception: Exception, 
                        include_traceback: bool = False) -> tuple:
        """
        Handle any exception and return appropriate error response.
        
        Args:
            exception (Exception): The exception to handle
            include_traceback (bool): Whether to include traceback
        
        Returns:
            tuple: (response_dict, status_code)
        """
        if isinstance(exception, HTTPException):
            return self.error_response(
                message=exception.description or str(exception),
                error_type=self.ERROR_SYSTEM,
                status_code=exception.code
            )
        
        # Handle custom validation errors
        if hasattr(exception, 'field') and hasattr(exception, 'message'):
            return self.validation_error_response(
                message=str(exception),
                field_errors={exception.field: [exception.message]} if exception.field else None
            )
        
        # Generic exception handling
        return self.system_error_response(
            message='An unexpected error occurred',
            error_details=str(exception),
            include_traceback=include_traceback
        )
    
    def paginated_response(self, data: List[Any], page: int, per_page: int,
                          total: int, message: str = 'Success') -> tuple:
        """
        Create a paginated success response.
        
        Args:
            data (List): Paginated data
            page (int): Current page number
            per_page (int): Items per page
            total (int): Total number of items
            message (str): Success message
        
        Returns:
            tuple: (response_dict, status_code)
        """
        total_pages = (total + per_page - 1) // per_page
        
        meta = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        return self.success_response(
            data=data,
            message=message,
            meta=meta
        )
    
    def _get_request_id(self) -> Optional[str]:
        """
        Get request ID from Flask request context.
        
        Returns:
            str or None: Request ID if available
        """
        try:
            # Try to get request ID from headers or generate one
            if hasattr(request, 'headers'):
                return request.headers.get('X-Request-ID')
        except RuntimeError:
            # Outside of request context
            pass
        return None
    
    def create_field_errors_dict(self, validation_result: Dict) -> Optional[Dict[str, List[str]]]:
        """
        Convert validation errors to field-specific error dictionary.
        
        Args:
            validation_result (Dict): Validation result from BusinessRuleValidator
        
        Returns:
            Dict or None: Field-specific errors
        """
        if not validation_result.get('errors'):
            return None
        
        field_errors = {}
        
        for error in validation_result['errors']:
            # Try to extract field name from error message
            if ':' in error:
                field_part, message_part = error.split(':', 1)
                field_name = field_part.strip().lower().replace(' ', '_')
                message = message_part.strip()
                
                if field_name not in field_errors:
                    field_errors[field_name] = []
                field_errors[field_name].append(message)
            else:
                # General error
                if 'general' not in field_errors:
                    field_errors['general'] = []
                field_errors['general'].append(error)
        
        return field_errors if field_errors else None


# Global error handler instance
error_handler = APIErrorHandler()


def handle_api_error(func):
    """
    Decorator to automatically handle API errors in Flask routes.
    
    Args:
        func: Flask route function
    
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return error_handler.handle_exception(e)
    
    wrapper.__name__ = func.__name__
    return wrapper