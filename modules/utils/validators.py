from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from decimal import Decimal, InvalidOperation
import re
from datetime import datetime
from modules.Products.product import Product
from modules.Customer.customer import Customer

if TYPE_CHECKING:
    from modules.Order.order import Order

# Import models for database validation
try:
    from models.order import Order as ModelOrder
    from models.product import Product as ModelProduct
except ImportError:
    # Handle case where models are not available
    ModelOrder = None
    ModelProduct = None


class ValidationError(Exception):
    """
    Custom exception for validation errors.
    """
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BusinessRuleValidator:
    """
    Comprehensive validation system for business rules and form data.
    
    This class provides validation methods for various business entities
    including products, customers, orders, and general form data.
    """
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Phone regex pattern (flexible format)
    PHONE_PATTERN = re.compile(r'^[\+]?[1-9]?[0-9]{7,15}$')
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Product validation constants
    MIN_PRODUCT_PRICE = Decimal('0.01')
    MAX_PRODUCT_PRICE = Decimal('999999.99')
    MIN_STOCK_QUANTITY = 0
    MAX_STOCK_QUANTITY = 999999
    
    # Order validation constants
    MIN_ORDER_TOTAL = Decimal('0.01')
    MAX_ORDER_TOTAL = Decimal('999999.99')
    MAX_ORDER_ITEMS = 100
    
    # Customer validation constants
    MAX_DAILY_ORDERS = 10
    MAX_MONTHLY_ORDER_VALUE = Decimal('50000.00')
    MIN_CUSTOMER_AGE = 13
    
    # Product validation constants
    MIN_PRODUCT_NAME_LENGTH = 3
    MAX_PRODUCT_NAME_LENGTH = 200
    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 2000
    
    # Business rule constants
    HIGH_VALUE_ORDER_THRESHOLD = Decimal('1000.00')
    BULK_ORDER_QUANTITY_THRESHOLD = 50
    MAX_SAME_PRODUCT_QUANTITY = 100
    
    def __init__(self, db_session=None):
        """
        Initialize validator with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
    
    def validate_email(self, email: str) -> Dict:
        """
        Validate email address format.
        
        Args:
            email (str): Email address to validate
        
        Returns:
            Dict: Validation result
        """
        if not email or not isinstance(email, str):
            return {
                'valid': False,
                'message': 'Email is required and must be a string'
            }
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 limit
            return {
                'valid': False,
                'message': 'Email address is too long (maximum 254 characters)'
            }
        
        if not self.EMAIL_PATTERN.match(email):
            return {
                'valid': False,
                'message': 'Invalid email format'
            }
        
        return {
            'valid': True,
            'normalized_email': email
        }
    
    def validate_phone(self, phone: str) -> Dict:
        """
        Validate phone number format.
        
        Args:
            phone (str): Phone number to validate
        
        Returns:
            Dict: Validation result
        """
        if not phone or not isinstance(phone, str):
            return {
                'valid': False,
                'message': 'Phone number is required and must be a string'
            }
        
        # Remove spaces, dashes, and parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not self.PHONE_PATTERN.match(cleaned_phone):
            return {
                'valid': False,
                'message': 'Invalid phone number format'
            }
        
        return {
            'valid': True,
            'normalized_phone': cleaned_phone
        }
    
    def validate_password(self, password: str) -> Dict:
        """
        Validate password strength and requirements.
        
        Args:
            password (str): Password to validate
        
        Returns:
            Dict: Validation result with strength indicators
        """
        if not password or not isinstance(password, str):
            return {
                'valid': False,
                'message': 'Password is required and must be a string',
                'strength': 'invalid'
            }
        
        errors = []
        warnings = []
        strength_score = 0
        
        # Length check
        if len(password) < self.MIN_PASSWORD_LENGTH:
            errors.append(f'Password must be at least {self.MIN_PASSWORD_LENGTH} characters long')
        elif len(password) >= 12:
            strength_score += 2
        else:
            strength_score += 1
        
        if len(password) > self.MAX_PASSWORD_LENGTH:
            errors.append(f'Password must not exceed {self.MAX_PASSWORD_LENGTH} characters')
        
        # Character variety checks
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_lower:
            warnings.append('Password should contain lowercase letters')
        else:
            strength_score += 1
        
        if not has_upper:
            warnings.append('Password should contain uppercase letters')
        else:
            strength_score += 1
        
        if not has_digit:
            warnings.append('Password should contain numbers')
        else:
            strength_score += 1
        
        if not has_special:
            warnings.append('Password should contain special characters')
        else:
            strength_score += 1
        
        # Common password patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123']
        if password.lower() in common_patterns:
            errors.append('Password is too common')
            strength_score = 0
        
        # Determine strength
        if strength_score >= 6:
            strength = 'strong'
        elif strength_score >= 4:
            strength = 'medium'
        elif strength_score >= 2:
            strength = 'weak'
        else:
            strength = 'very_weak'
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strength': strength,
            'strength_score': strength_score
        }
    
    def validate_price(self, price: Union[str, float, Decimal], field_name: str = 'price') -> Dict:
        """
        Validate price value.
        
        Args:
            price: Price value to validate
            field_name (str): Name of the field for error messages
        
        Returns:
            Dict: Validation result
        """
        if price is None:
            return {
                'valid': False,
                'message': f'{field_name.title()} is required'
            }
        
        try:
            if isinstance(price, str):
                price_decimal = Decimal(price.strip())
            else:
                price_decimal = Decimal(str(price))
        except (InvalidOperation, ValueError):
            return {
                'valid': False,
                'message': f'{field_name.title()} must be a valid number'
            }
        
        if price_decimal < self.MIN_PRODUCT_PRICE:
            return {
                'valid': False,
                'message': f'{field_name.title()} must be at least ${self.MIN_PRODUCT_PRICE}'
            }
        
        if price_decimal > self.MAX_PRODUCT_PRICE:
            return {
                'valid': False,
                'message': f'{field_name.title()} cannot exceed ${self.MAX_PRODUCT_PRICE}'
            }
        
        return {
            'valid': True,
            'normalized_price': float(price_decimal)
        }
    
    def validate_stock_quantity(self, quantity: Union[str, int], field_name: str = 'stock_quantity') -> Dict:
        """
        Validate stock quantity.
        
        Args:
            quantity: Quantity value to validate
            field_name (str): Name of the field for error messages
        
        Returns:
            Dict: Validation result
        """
        if quantity is None:
            return {
                'valid': False,
                'message': f'{field_name.replace("_", " ").title()} is required'
            }
        
        try:
            if isinstance(quantity, str):
                quantity_int = int(quantity.strip())
            else:
                quantity_int = int(quantity)
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': f'{field_name.replace("_", " ").title()} must be a valid integer'
            }
        
        if quantity_int < self.MIN_STOCK_QUANTITY:
            return {
                'valid': False,
                'message': f'{field_name.replace("_", " ").title()} cannot be negative'
            }
        
        if quantity_int > self.MAX_STOCK_QUANTITY:
            return {
                'valid': False,
                'message': f'{field_name.replace("_", " ").title()} cannot exceed {self.MAX_STOCK_QUANTITY:,}'
            }
        
        return {
            'valid': True,
            'normalized_quantity': quantity_int
        }
    
    def validate_product_data(self, product_data: Dict) -> Dict:
        """
        Validate product creation/update data.
        
        Args:
            product_data (Dict): Product data to validate
        
        Returns:
            Dict: Comprehensive validation result
        """
        errors = []
        warnings = []
        normalized_data = {}
        
        # Required fields
        required_fields = ['product_name', 'description', 'price', 'category_id']
        for field in required_fields:
            if not product_data.get(field):
                errors.append(f'{field.replace("_", " ").title()} is required')
        
        # Product name validation
        product_name = product_data.get('product_name', '').strip()
        if product_name:
            if len(product_name) < 2:
                errors.append('Product name must be at least 2 characters long')
            elif len(product_name) > 255:
                errors.append('Product name cannot exceed 255 characters')
            else:
                normalized_data['product_name'] = product_name
        
        # Description validation
        description = product_data.get('description', '').strip()
        if description:
            if len(description) < 10:
                warnings.append('Product description should be at least 10 characters for better SEO')
            elif len(description) > 2000:
                errors.append('Product description cannot exceed 2000 characters')
            normalized_data['description'] = description
        
        # Price validation
        if 'price' in product_data:
            price_validation = self.validate_price(product_data['price'])
            if not price_validation['valid']:
                errors.append(price_validation['message'])
            else:
                normalized_data['price'] = price_validation['normalized_price']
        
        # Stock quantity validation
        if 'stock_quantity' in product_data:
            stock_validation = self.validate_stock_quantity(product_data['stock_quantity'])
            if not stock_validation['valid']:
                errors.append(stock_validation['message'])
            else:
                normalized_data['stock_quantity'] = stock_validation['normalized_quantity']
        
        # Category ID validation
        category_id = product_data.get('category_id')
        if category_id:
            if not isinstance(category_id, str) or len(category_id.strip()) == 0:
                errors.append('Category ID must be a valid string')
            else:
                normalized_data['category_id'] = category_id.strip()
        
        # Check for duplicate product name (if database session available)
        if (self.db_session and product_name and 
            not errors and 'product_id' not in product_data):
            
            existing_product = self.db_session.query(Product).filter_by(
                product_name=product_name
            ).first()
            
            if existing_product:
                errors.append('A product with this name already exists')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized_data': normalized_data
        }
    
    def validate_customer_order_limits(self, customer_id: str, order_total: Decimal) -> Dict:
        """
        Validate customer order limits and restrictions.
        
        Args:
            customer_id (str): Customer ID
            order_total (Decimal): Total order amount
        
        Returns:
            Dict: Validation result with limit checks
        """
        if not self.db_session:
            return {
                'valid': True,
                'warnings': ['Database session not available for limit validation']
            }
        
        errors = []
        warnings = []
        
        try:
            from datetime import datetime, timedelta
            
            # Check daily order limit
            today = datetime.now().date()
            daily_orders = self.db_session.query(ModelOrder).filter(
                ModelOrder.customer_id == customer_id,
                ModelOrder.created_at >= today,
                ModelOrder.order_status != 'cancelled'
            ).count()
            
            if daily_orders >= self.MAX_DAILY_ORDERS:
                errors.append(f'Daily order limit exceeded ({self.MAX_DAILY_ORDERS} orders per day)')
            elif daily_orders >= self.MAX_DAILY_ORDERS - 2:
                warnings.append(f'Approaching daily order limit ({daily_orders}/{self.MAX_DAILY_ORDERS})')
            
            # Check monthly order value limit
            month_start = datetime.now().replace(day=1).date()
            monthly_total = self.db_session.query(ModelOrder).filter(
                ModelOrder.customer_id == customer_id,
                ModelOrder.created_at >= month_start,
                ModelOrder.order_status.in_(['confirmed', 'processing', 'shipped', 'delivered'])
            ).with_entities(ModelOrder.total_amount).all()
            
            current_monthly_total = sum(order.total_amount or 0 for order in monthly_total)
            
            if current_monthly_total + order_total > self.MAX_MONTHLY_ORDER_VALUE:
                errors.append(
                    f'Monthly order value limit exceeded '
                    f'(${current_monthly_total + order_total:.2f} > ${self.MAX_MONTHLY_ORDER_VALUE:.2f})'
                )
            elif current_monthly_total + order_total > self.MAX_MONTHLY_ORDER_VALUE * Decimal('0.8'):
                warnings.append(
                    f'Approaching monthly order limit '
                    f'(${current_monthly_total + order_total:.2f}/${self.MAX_MONTHLY_ORDER_VALUE:.2f})'
                )
            
            # High-value order warning
            if order_total > self.HIGH_VALUE_ORDER_THRESHOLD:
                warnings.append('High-value order requires additional verification')
            
        except Exception as e:
            warnings.append(f'Could not validate customer limits: {str(e)}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_product_business_rules(self, product_data: Dict) -> Dict:
        """
        Validate advanced product business rules.
        
        Args:
            product_data (Dict): Product data to validate
        
        Returns:
            Dict: Validation result with business rule checks
        """
        errors = []
        warnings = []
        
        # Product name length validation
        product_name = product_data.get('product_name', '').strip()
        if product_name:
            if len(product_name) < self.MIN_PRODUCT_NAME_LENGTH:
                errors.append(f'Product name must be at least {self.MIN_PRODUCT_NAME_LENGTH} characters')
            elif len(product_name) > self.MAX_PRODUCT_NAME_LENGTH:
                errors.append(f'Product name cannot exceed {self.MAX_PRODUCT_NAME_LENGTH} characters')
        
        # Description length validation
        description = product_data.get('description', '').strip()
        if description:
            if len(description) < self.MIN_DESCRIPTION_LENGTH:
                warnings.append(f'Product description should be at least {self.MIN_DESCRIPTION_LENGTH} characters for better SEO')
            elif len(description) > self.MAX_DESCRIPTION_LENGTH:
                errors.append(f'Product description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters')
        
        # Price validation with business rules
        price = product_data.get('price')
        if price is not None:
            try:
                price_decimal = Decimal(str(price))
                
                # Check for suspicious pricing
                if price_decimal > Decimal('10000.00'):
                    warnings.append('High-priced product requires manager approval')
                elif price_decimal < Decimal('1.00'):
                    warnings.append('Low-priced product may affect profit margins')
                
            except (InvalidOperation, ValueError):
                pass  # Price validation handled elsewhere
        
        # Stock level validation with business rules
        stock_quantity = product_data.get('stock_quantity')
        min_stock_level = product_data.get('min_stock_level', 5)
        
        if stock_quantity is not None and min_stock_level is not None:
            try:
                stock_int = int(stock_quantity)
                min_stock_int = int(min_stock_level)
                
                if stock_int > 0 and stock_int <= min_stock_int:
                    warnings.append('Initial stock is at or below minimum stock level')
                elif stock_int > 1000:
                    warnings.append('High stock quantity - ensure adequate storage capacity')
                
            except (ValueError, TypeError):
                pass  # Stock validation handled elsewhere
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_inventory_constraints(self, order_items: List[Dict]) -> Dict:
        """
        Validate inventory constraints for order items.
        
        Args:
            order_items (List[Dict]): List of order items with product_id and quantity
        
        Returns:
            Dict: Validation result with inventory checks
        """
        if not self.db_session:
            return {
                'valid': True,
                'warnings': ['Database session not available for inventory validation']
            }
        
        errors = []
        warnings = []
        
        try:
            for item in order_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)
                
                if not product_id:
                    continue
                
                # Get product from database
                product = self.db_session.query(ModelProduct).filter(
                    ModelProduct.product_id == product_id
                ).first()
                
                if not product:
                    errors.append(f'Product {product_id} not found')
                    continue
                
                # Check stock availability
                if product.stock_quantity < quantity:
                    errors.append(
                        f'Insufficient stock for {product.product_name}: '
                        f'requested {quantity}, available {product.stock_quantity}'
                    )
                elif product.stock_quantity - quantity <= product.min_stock_level:
                    warnings.append(
                        f'Order will bring {product.product_name} below minimum stock level'
                    )
                
                # Check for bulk order quantities
                if quantity >= self.BULK_ORDER_QUANTITY_THRESHOLD:
                    warnings.append(
                        f'Bulk order detected for {product.product_name} '
                        f'({quantity} units) - consider volume discount'
                    )
                
                # Check product availability
                if not product.is_active:
                    errors.append(f'Product {product.product_name} is not available for purchase')
                
        except Exception as e:
            warnings.append(f'Could not validate inventory constraints: {str(e)}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_order_items(self, order_items: List[Dict]) -> Dict:
        """
        Validate order items for business rules compliance.
        
        Args:
            order_items (List[Dict]): List of order items
        
        Returns:
            Dict: Validation result with item checks
        """
        errors = []
        warnings = []
        
        if not order_items:
            errors.append('Order must contain at least one item')
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        if len(order_items) > self.MAX_ORDER_ITEMS:
            errors.append(f'Order cannot contain more than {self.MAX_ORDER_ITEMS} items')
        
        total_quantity = 0
        unique_products = set()
        
        for i, item in enumerate(order_items):
            # Check required fields
            if not item.get('product_id'):
                errors.append(f'Item {i+1}: Product ID is required')
            
            quantity = item.get('quantity', 0)
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                errors.append(f'Item {i+1}: Quantity must be a positive number')
            else:
                total_quantity += quantity
                
                # Check for duplicate products
                product_id = item.get('product_id')
                if product_id in unique_products:
                    warnings.append(f'Duplicate product {product_id} in order - consider consolidating')
                else:
                    unique_products.add(product_id)
        
        # Check total order quantity
        if total_quantity > self.BULK_ORDER_QUANTITY_THRESHOLD:
            warnings.append(f'Large order quantity ({total_quantity} items) - verify shipping capacity')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_bulk_operations(self, operation_count: int, operation_type: str = 'update') -> Dict:
        """
        Validate bulk operations for performance and safety.
        
        Args:
            operation_count (int): Number of operations to perform
            operation_type (str): Type of operation (update, delete, create)
        
        Returns:
            Dict: Validation result with bulk operation checks
        """
        errors = []
        warnings = []
        
        max_bulk_operations = {
            'update': 100,
            'delete': 50,
            'create': 200
        }
        
        max_allowed = max_bulk_operations.get(operation_type, 100)
        
        if operation_count > max_allowed:
            errors.append(
                f'Bulk {operation_type} operation exceeds maximum limit '
                f'({operation_count} > {max_allowed})'
            )
        elif operation_count > max_allowed * 0.8:
            warnings.append(
                f'Large bulk {operation_type} operation '
                f'({operation_count} operations) - consider breaking into smaller batches'
            )
        
        if operation_count > 50:
            warnings.append('Large bulk operation may impact system performance')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_customer_data(self, customer_data: Dict) -> Dict:
        """
        Validate customer registration/update data.
        
        Args:
            customer_data (Dict): Customer data to validate
        
        Returns:
            Dict: Comprehensive validation result
        """
        errors = []
        warnings = []
        normalized_data = {}
        
        # Required fields for registration
        if customer_data.get('is_registration', False):
            required_fields = ['first_name', 'last_name', 'email', 'password']
        else:
            required_fields = ['first_name', 'last_name', 'email']
        
        for field in required_fields:
            if not customer_data.get(field):
                errors.append(f'{field.replace("_", " ").title()} is required')
        
        # Name validation
        for name_field in ['first_name', 'last_name']:
            name = customer_data.get(name_field, '').strip()
            if name:
                if len(name) < 2:
                    errors.append(f'{name_field.replace("_", " ").title()} must be at least 2 characters long')
                elif len(name) > 50:
                    errors.append(f'{name_field.replace("_", " ").title()} cannot exceed 50 characters')
                elif not re.match(r'^[a-zA-Z\s\-\']+$', name):
                    errors.append(f'{name_field.replace("_", " ").title()} can only contain letters, spaces, hyphens, and apostrophes')
                else:
                    normalized_data[name_field] = name.title()
        
        # Email validation
        if 'email' in customer_data:
            email_validation = self.validate_email(customer_data['email'])
            if not email_validation['valid']:
                errors.append(email_validation['message'])
            else:
                normalized_data['email'] = email_validation['normalized_email']
                
                # Check for duplicate email (if database session available)
                if (self.db_session and 'customer_id' not in customer_data):
                    existing_customer = self.db_session.query(Customer).filter_by(
                        email=email_validation['normalized_email']
                    ).first()
                    
                    if existing_customer:
                        errors.append('An account with this email already exists')
        
        # Phone validation (optional)
        if customer_data.get('phone'):
            phone_validation = self.validate_phone(customer_data['phone'])
            if not phone_validation['valid']:
                errors.append(phone_validation['message'])
            else:
                normalized_data['phone'] = phone_validation['normalized_phone']
        
        # Password validation (for registration)
        if 'password' in customer_data:
            password_validation = self.validate_password(customer_data['password'])
            if not password_validation['valid']:
                errors.extend(password_validation['errors'])
            else:
                warnings.extend(password_validation['warnings'])
                normalized_data['password'] = customer_data['password']  # Don't normalize password
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized_data': normalized_data
        }
    
    def validate_order_data(self, order_data: Dict) -> Dict:
        """
        Validate order creation/update data.
        
        Args:
            order_data (Dict): Order data to validate
        
        Returns:
            Dict: Comprehensive validation result
        """
        errors = []
        warnings = []
        normalized_data = {}
        
        # Required fields
        required_fields = ['customer_id', 'order_items']
        for field in required_fields:
            if not order_data.get(field):
                errors.append(f'{field.replace("_", " ").title()} is required')
        
        # Customer ID validation
        customer_id = order_data.get('customer_id')
        if customer_id:
            if not isinstance(customer_id, str) or len(customer_id.strip()) == 0:
                errors.append('Customer ID must be a valid string')
            else:
                normalized_data['customer_id'] = customer_id.strip()
        
        # Order items validation
        order_items = order_data.get('order_items', [])
        if order_items:
            if not isinstance(order_items, list):
                errors.append('Order items must be a list')
            elif len(order_items) == 0:
                errors.append('Order must have at least one item')
            elif len(order_items) > self.MAX_ORDER_ITEMS:
                errors.append(f'Order cannot have more than {self.MAX_ORDER_ITEMS} items')
            else:
                validated_items = []
                total_amount = Decimal('0.00')
                
                for i, item in enumerate(order_items):
                    item_errors = []
                    
                    # Validate required item fields
                    if not item.get('product_id'):
                        item_errors.append(f'Item {i+1}: Product ID is required')
                    
                    if not item.get('quantity'):
                        item_errors.append(f'Item {i+1}: Quantity is required')
                    
                    if not item.get('unit_price'):
                        item_errors.append(f'Item {i+1}: Unit price is required')
                    
                    # Validate quantity
                    if item.get('quantity'):
                        quantity_validation = self.validate_stock_quantity(
                            item['quantity'], f'Item {i+1} quantity'
                        )
                        if not quantity_validation['valid']:
                            item_errors.append(quantity_validation['message'])
                        elif quantity_validation['normalized_quantity'] == 0:
                            item_errors.append(f'Item {i+1}: Quantity must be greater than 0')
                    
                    # Validate unit price
                    if item.get('unit_price'):
                        price_validation = self.validate_price(
                            item['unit_price'], f'Item {i+1} unit price'
                        )
                        if not price_validation['valid']:
                            item_errors.append(price_validation['message'])
                        else:
                            item_total = (Decimal(str(price_validation['normalized_price'])) * 
                                        Decimal(str(quantity_validation.get('normalized_quantity', 1))))
                            total_amount += item_total
                    
                    if item_errors:
                        errors.extend(item_errors)
                    else:
                        validated_items.append({
                            'product_id': item['product_id'].strip(),
                            'quantity': quantity_validation['normalized_quantity'],
                            'unit_price': price_validation['normalized_price']
                        })
                
                if not errors:
                    normalized_data['order_items'] = validated_items
                    normalized_data['calculated_total'] = float(total_amount)
                    
                    # Validate total amount
                    if total_amount < self.MIN_ORDER_TOTAL:
                        errors.append(f'Order total must be at least ${self.MIN_ORDER_TOTAL}')
                    elif total_amount > self.MAX_ORDER_TOTAL:
                        errors.append(f'Order total cannot exceed ${self.MAX_ORDER_TOTAL}')
        
        # Shipping address validation (optional)
        if order_data.get('shipping_address'):
            address = order_data['shipping_address']
            if isinstance(address, dict):
                address_validation = self._validate_address(address, 'Shipping')
                if not address_validation['valid']:
                    errors.extend(address_validation['errors'])
                else:
                    normalized_data['shipping_address'] = address_validation['normalized_address']
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized_data': normalized_data
        }
    
    def _validate_address(self, address: Dict, address_type: str = 'Address') -> Dict:
        """
        Validate address data.
        
        Args:
            address (Dict): Address data to validate
            address_type (str): Type of address for error messages
        
        Returns:
            Dict: Address validation result
        """
        errors = []
        normalized_address = {}
        
        required_fields = ['street', 'city', 'state', 'zip_code', 'country']
        for field in required_fields:
            value = address.get(field, '').strip()
            if not value:
                errors.append(f'{address_type} {field.replace("_", " ")} is required')
            else:
                normalized_address[field] = value
        
        # ZIP code format validation (basic)
        zip_code = address.get('zip_code', '').strip()
        if zip_code and not re.match(r'^[0-9]{5}(-[0-9]{4})?$', zip_code):
            errors.append(f'{address_type} ZIP code format is invalid')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'normalized_address': normalized_address
        }
    
    def validate_form_data(self, form_data: Dict, validation_rules: Dict) -> Dict:
        """
        Generic form data validation based on rules.
        
        Args:
            form_data (Dict): Form data to validate
            validation_rules (Dict): Validation rules for each field
        
        Returns:
            Dict: Validation result
        """
        errors = []
        warnings = []
        normalized_data = {}
        
        for field_name, rules in validation_rules.items():
            field_value = form_data.get(field_name)
            
            # Required field check
            if rules.get('required', False) and not field_value:
                errors.append(f'{field_name.replace("_", " ").title()} is required')
                continue
            
            if field_value is not None:
                # Type validation
                expected_type = rules.get('type')
                if expected_type and not isinstance(field_value, expected_type):
                    errors.append(f'{field_name.replace("_", " ").title()} must be of type {expected_type.__name__}')
                    continue
                
                # String validations
                if isinstance(field_value, str):
                    field_value = field_value.strip()
                    
                    # Length validations
                    min_length = rules.get('min_length')
                    max_length = rules.get('max_length')
                    
                    if min_length and len(field_value) < min_length:
                        errors.append(f'{field_name.replace("_", " ").title()} must be at least {min_length} characters long')
                    
                    if max_length and len(field_value) > max_length:
                        errors.append(f'{field_name.replace("_", " ").title()} cannot exceed {max_length} characters')
                    
                    # Pattern validation
                    pattern = rules.get('pattern')
                    if pattern and not re.match(pattern, field_value):
                        pattern_message = rules.get('pattern_message', 'Invalid format')
                        errors.append(f'{field_name.replace("_", " ").title()}: {pattern_message}')
                
                # Numeric validations
                if isinstance(field_value, (int, float, Decimal)):
                    min_value = rules.get('min_value')
                    max_value = rules.get('max_value')
                    
                    if min_value is not None and field_value < min_value:
                        errors.append(f'{field_name.replace("_", " ").title()} must be at least {min_value}')
                    
                    if max_value is not None and field_value > max_value:
                        errors.append(f'{field_name.replace("_", " ").title()} cannot exceed {max_value}')
                
                # Custom validator
                custom_validator = rules.get('validator')
                if custom_validator and callable(custom_validator):
                    try:
                        validation_result = custom_validator(field_value)
                        if isinstance(validation_result, dict):
                            if not validation_result.get('valid', True):
                                errors.append(validation_result.get('message', f'Invalid {field_name}'))
                            else:
                                field_value = validation_result.get('value', field_value)
                    except Exception as e:
                        errors.append(f'Validation error for {field_name}: {str(e)}')
                
                normalized_data[field_name] = field_value
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized_data': normalized_data
        }