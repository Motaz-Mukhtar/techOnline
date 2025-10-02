#!/usr/bin/env python3
"""
Utility modules for TechOnline e-commerce platform.

This package contains various utility functions and classes for:
- File handling and image processing
- Data validation and sanitization
- Common helper functions
"""

from .file_handler import (
    FileHandler,
    file_handler,
    allowed_file,
    save_uploaded_file,
    delete_uploaded_file
)
from .pricing_calculator import PricingCalculator
from .stock_manager import StockManager
from .order_workflow import OrderWorkflowManager, OrderStatus
from .validators import BusinessRuleValidator, ValidationError
from .error_handler import APIErrorHandler, error_handler, handle_api_error

__all__ = [
    'file_handler',
    'save_uploaded_file',
    'delete_uploaded_file',
    'get_file_url',
    'validate_file',
    'PricingCalculator',
    'StockManager',
    'OrderWorkflowManager',
    'OrderStatus',
    'BusinessRuleValidator',
    'ValidationError',
    'APIErrorHandler',
    'error_handler',
    'handle_api_error'
]