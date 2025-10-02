#!/usr/bin/python3
"""
OrderItem module - Junction table for Order-Product many-to-many relationship

This module defines the OrderItem class that serves as a junction table
between orders and products, allowing tracking of which products are in
which orders along with quantities and pricing information.
"""

from modules.baseModel import BaseModel, Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship


class OrderItem(BaseModel, Base):
    """
    OrderItem class - Junction table for Order-Product relationship.
    
    This class represents individual items within an order, storing the
    relationship between orders and products along with quantity and pricing.
    
    Attributes:
        order_id (str): Foreign key to the Order table
        product_id (str): Foreign key to the Product table
        quantity (int): Number of units of the product in the order
        unit_price (float): Price per unit at the time of order
        subtotal (float): Total price for this item (quantity * unit_price)
    
    Relationships:
        order: Back reference to the Order model
        product: Back reference to the Product model
    """
    
    __tablename__ = 'order_items'
    
    order_id = Column(String(60), ForeignKey('orders.id'), nullable=False)
    product_id = Column(String(60), ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False, default=0.0)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    def __init__(self, *args, **kwargs):
        """
        Initialize OrderItem instance.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments including:
                - order_id (str): ID of the order
                - product_id (str): ID of the product
                - quantity (int): Quantity of the product
                - unit_price (float): Price per unit
        """
        super().__init__(*args, **kwargs)
        
        # Calculate subtotal if not provided
        if hasattr(self, 'quantity') and hasattr(self, 'unit_price'):
            self.calculate_subtotal()
    
    def calculate_subtotal(self):
        """
        Calculate and update the subtotal for this order item.
        
        The subtotal is calculated as quantity * unit_price.
        """
        if self.quantity and self.unit_price:
            self.subtotal = float(self.quantity * self.unit_price)
        else:
            self.subtotal = 0.0
    
    def update_quantity(self, new_quantity):
        """
        Update the quantity of this order item and recalculate subtotal.
        
        Args:
            new_quantity (int): New quantity for the item
            
        Raises:
            ValueError: If new_quantity is not a positive integer
        """
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        
        self.quantity = new_quantity
        self.calculate_subtotal()
    
    def to_dict(self):
        """
        Convert OrderItem instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all OrderItem attributes and related data
        """
        order_item_dict = super().to_dict()
        
        # Add product information if available
        if hasattr(self, 'product') and self.product:
            order_item_dict['product'] = {
                'id': self.product.id,
                'product_name': self.product.product_name,
                'description': self.product.description,
                'price': self.product.price
            }
        
        return order_item_dict
    
    def __str__(self):
        """
        String representation of OrderItem.
        
        Returns:
            str: Human-readable string representation
        """
        return f"OrderItem(order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity}, subtotal=${self.subtotal:.2f})"
    
    def __repr__(self):
        """
        Official string representation of OrderItem.
        
        Returns:
            str: Official string representation for debugging
        """
        return f"<OrderItem {self.id}: Order {self.order_id}, Product {self.product_id}, Qty {self.quantity}>"