#!/usr/bin/env python3
"""
Wishlist Model for TechOnline e-commerce platform.

This module defines the Wishlist model that represents a customer's
wishlist containing their favorite products.
"""

import modules
from modules.baseModel import BaseModel, Base
from modules.Products.product import Product
from modules.Customer.customer import Customer
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Wishlist(BaseModel, Base):
    """
    Wishlist Class
    
    Represents a customer's wishlist item containing a favorite product.
    
    Attributes:
        customer_id (str): Foreign key to Customer
        product_id (str): Foreign key to Product
        added_at (datetime): When the item was added to wishlist
    """
    __tablename__ = 'wishlists'
    
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    product_id = Column(String(60), ForeignKey('products.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship('Customer', backref='wishlist_items')
    product = relationship('Product', backref='wishlist_items')
    
    def to_dict(self):
        """
        Convert wishlist item to dictionary representation.
        
        Returns:
            dict: Dictionary containing wishlist item data with product details
        """
        wishlist_dict = super().to_dict()
        
        # Include product details if available
        if self.product:
            wishlist_dict['product'] = {
                'id': self.product.id,
                'name': self.product.name,
                'description': self.product.description,
                'price': float(self.product.price),
                'product_image': self.product.product_image,
                'stock_quantity': self.product.stock_quantity,
                'is_available': self.product.is_available,
                'category_id': self.product.category_id
            }
        
        return wishlist_dict