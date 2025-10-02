#!/usr/bin/env python3
"""Order Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from modules.utils.pricing_calculator import PricingCalculator
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import Dict, List, Optional
import json


class Order(BaseModel, Base):
    """
    Define Order Class
    
    This class represents customer orders in the e-commerce system,
    linking customers to their purchased products through order items.
    Enhanced with comprehensive pricing calculations including tax, discounts, and shipping.
    
    Attributes:
        customer_id (str): String(60) ForeignKey for customer.id and can't be null
        cart_id (str): String(60) ForeignKey for carts.id (optional)
        
        # Pricing fields
        subtotal (float): Subtotal before discounts, tax, and shipping
        discount_code (str): Applied discount code
        discount_amount (float): Total discount applied
        tax_amount (float): Tax amount calculated
        tax_region (str): Tax region/state for calculation
        tax_exempt (bool): Whether order is tax exempt
        shipping_cost (float): Shipping cost calculated
        shipping_method (str): Shipping method selected
        total_amount (float): Final total amount including all charges
        
        # Order management
        order_status (str): Status of the order (pending, confirmed, processing, shipped, delivered, cancelled)
        shipping_address (str): JSON string of shipping address
        billing_address (str): JSON string of billing address
        order_notes (str): Additional notes for the order
        total_weight (float): Total weight of order items
    
    Relationships:
        order_items: One-to-many relationship with OrderItem
        customer: Back reference to Customer model
        cart: Back reference to Cart model
    """
    __tablename__ = 'orders'
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    cart_id = Column(String(60), ForeignKey('carts.id'))
    
    # Pricing fields
    subtotal = Column(Float, nullable=False, default=0.0)
    discount_code = Column(String(50))
    discount_amount = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    tax_region = Column(String(10), nullable=False, default='DEFAULT')
    tax_exempt = Column(Boolean, nullable=False, default=False)
    shipping_cost = Column(Float, nullable=False, default=0.0)
    shipping_method = Column(String(20), nullable=False, default='standard')
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # Order management
    order_status = Column(String(20), nullable=False, default='pending')
    shipping_address = Column(Text)  # JSON string
    billing_address = Column(Text)   # JSON string
    order_notes = Column(Text)
    total_weight = Column(Float, nullable=False, default=1.0)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        """
        Initialize Order with pricing calculator.
        """
        super().__init__(**kwargs)
        self._pricing_calculator = PricingCalculator()
    
    def get_shipping_address_dict(self) -> Optional[Dict]:
        """
        Get shipping address as dictionary.
        
        Returns:
            Dict or None: Shipping address data
        """
        if self.shipping_address:
            try:
                return json.loads(self.shipping_address)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    
    def set_shipping_address(self, address_dict: Dict) -> None:
        """
        Set shipping address from dictionary.
        
        Args:
            address_dict (Dict): Address information
        """
        if address_dict:
            self.shipping_address = json.dumps(address_dict)
        else:
            self.shipping_address = None
    
    def get_billing_address_dict(self) -> Optional[Dict]:
        """
        Get billing address as dictionary.
        
        Returns:
            Dict or None: Billing address data
        """
        if self.billing_address:
            try:
                return json.loads(self.billing_address)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    
    def set_billing_address(self, address_dict: Dict) -> None:
        """
        Set billing address from dictionary.
        
        Args:
            address_dict (Dict): Address information
        """
        if address_dict:
            self.billing_address = json.dumps(address_dict)
        else:
            self.billing_address = None
    
    def calculate_pricing(self, discount_code: Optional[str] = None,
                         discount_percentage: Optional[float] = None,
                         discount_amount: Optional[float] = None) -> Dict:
        """
        Calculate comprehensive pricing for the order.
        
        Args:
            discount_code (str, optional): Discount code to apply
            discount_percentage (float, optional): Percentage discount
            discount_amount (float, optional): Fixed discount amount
        
        Returns:
            Dict: Complete pricing breakdown
        """
        if not self.order_items:
            raise ValueError("Cannot calculate pricing for order without items")
        
        # Prepare order items data for pricing calculator
        items_data = []
        for item in self.order_items:
            items_data.append({
                'quantity': item.quantity,
                'unit_price': item.unit_price
            })
        
        # Calculate pricing
        pricing_result = self._pricing_calculator.calculate_order_total(
            order_items=items_data,
            discount_code=discount_code or self.discount_code,
            discount_percentage=discount_percentage,
            discount_amount=discount_amount,
            tax_region=self.tax_region,
            tax_exempt=self.tax_exempt,
            shipping_method=self.shipping_method,
            total_weight=self.total_weight,
            shipping_address=self.get_shipping_address_dict()
        )
        
        return pricing_result
    
    def update_pricing(self, discount_code: Optional[str] = None,
                      discount_percentage: Optional[float] = None,
                      discount_amount: Optional[float] = None,
                      save_changes: bool = True) -> Dict:
        """
        Update order pricing and optionally save to database.
        
        Args:
            discount_code (str, optional): Discount code to apply
            discount_percentage (float, optional): Percentage discount
            discount_amount (float, optional): Fixed discount amount
            save_changes (bool): Whether to save changes to database
        
        Returns:
            Dict: Updated pricing breakdown
        """
        pricing_result = self.calculate_pricing(discount_code, discount_percentage, discount_amount)
        
        # Update order fields
        self.subtotal = pricing_result['subtotal']
        self.discount_amount = pricing_result['discount_applied']
        self.tax_amount = pricing_result['tax_amount']
        self.shipping_cost = pricing_result['shipping_cost']
        self.total_amount = pricing_result['final_total']
        
        if discount_code:
            self.discount_code = discount_code
        
        if save_changes:
            self.save()
        
        return pricing_result
    
    def get_order_status_display(self) -> str:
        """
        Get human-readable order status.
        
        Returns:
            str: Formatted order status
        """
        status_map = {
            'pending': 'Pending Payment',
            'confirmed': 'Order Confirmed',
            'processing': 'Processing',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
            'refunded': 'Refunded'
        }
        return status_map.get(self.order_status, self.order_status.title())
    
    def can_cancel(self) -> bool:
        """
        Check if order can be cancelled.
        
        Returns:
            bool: True if order can be cancelled
        """
        return self.order_status in ['pending', 'confirmed']
    
    def can_modify(self) -> bool:
        """
        Check if order can be modified.
        
        Returns:
            bool: True if order can be modified
        """
        return self.order_status in ['pending']
    
    def to_dict(self) -> Dict:
        """
        Convert order to dictionary representation.
        
        Returns:
            Dict: Order data as dictionary
        """
        base_dict = super().to_dict()
        
        # Add computed fields
        base_dict.update({
            'order_status_display': self.get_order_status_display(),
            'can_cancel': self.can_cancel(),
            'can_modify': self.can_modify(),
            'shipping_address_dict': self.get_shipping_address_dict(),
            'billing_address_dict': self.get_billing_address_dict(),
            'order_items_count': len(self.order_items) if self.order_items else 0
        })
        
        return base_dict
    
    def calculate_total_amount(self):
        """
        Calculate the total amount for the order based on order items.
        
        This method uses the comprehensive pricing calculator to determine
        the total amount including tax, discounts, and shipping.
        
        Returns:
            float: The calculated total amount for the order
        """
        if not self.order_items:
            self.total_amount = 0.0
            return 0.0
        
        try:
            pricing_result = self.calculate_pricing()
            self.total_amount = pricing_result['final_total']
            return self.total_amount
        except ValueError:
            # Fallback to simple calculation if pricing fails
            total = 0.0
            for item in self.order_items:
                total += item.subtotal
            self.total_amount = total
            return total
    
    def add_order_item(self, product_id, quantity, unit_price):
        """
        Add an item to this order.
        
        Args:
            product_id (str): ID of the product to add
            quantity (int): Quantity of the product
            unit_price (float): Price per unit
            
        Returns:
            OrderItem: The created order item
            
        Raises:
            ValueError: If product_id is invalid or quantity/price are not positive
        """
        from modules.Order.order_item import OrderItem
        from modules.Products.product import Product
        from modules import storage
        
        # Validate product exists
        product = storage.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Validate quantity and price
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        
        if not isinstance(unit_price, (int, float)) or unit_price <= 0:
            raise ValueError("Unit price must be a positive number")
        
        # Create order item
        order_item = OrderItem(
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=float(unit_price)
        )
        order_item.save()
        
        # Update total amount
        self.calculate_total_amount()
        
        return order_item
    
    def remove_order_item(self, product_id):
        """
        Remove an item from this order.
        
        Args:
            product_id (str): ID of the product to remove
            
        Returns:
            bool: True if item was removed, False if not found
        """
        from modules import storage
        
        for item in self.order_items:
            if item.product_id == product_id:
                storage.delete(item)
                self.calculate_total_amount()
                return True
        
        return False
    
    def update_order_status(self, new_status):
        """
        Update the status of this order.
        
        Args:
            new_status (str): New status for the order
            
        Raises:
            ValueError: If new_status is not valid
        """
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        self.order_status = new_status
    
    @property
    def products(self):
        """
        Get all products in this order.
        
        Returns:
            list: List of Product objects in this order
        """
        return [item.product for item in self.order_items if item.product]
    
    def get_item_count(self):
        """
        Get the total number of items in this order.
        
        Returns:
            int: Total quantity of all items
        """
        return sum(item.quantity for item in self.order_items)
    
    def to_dict(self):
        """
        Convert Order instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all Order attributes and related data
        """
        order_dict = super().to_dict()
        
        # Add order items
        order_dict['order_items'] = [item.to_dict() for item in self.order_items]
        order_dict['item_count'] = self.get_item_count()
        
        return order_dict


