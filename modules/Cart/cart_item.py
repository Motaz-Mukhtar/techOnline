#!/usr/bin/env python3
"""Create CartItem Junction Table Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class CartItem(BaseModel, Base):
    """
    CartItem Junction Table Class for Cart-Product Many-to-Many Relationship
    
    This model represents individual items within a shopping cart,
    allowing multiple products to be associated with a single cart
    with specific quantities and pricing information.
    
    Attributes:
        cart_id (str): Foreign key reference to Cart.id
        product_id (str): Foreign key reference to Product.id
        quantity (int): Number of units of this product in the cart
        unit_price (float): Price per unit at the time of adding to cart (USD)
        subtotal (float): Calculated subtotal for this cart item (quantity * unit_price)
    
    Relationships:
        cart: Back reference to the Cart model
        product: Back reference to the Product model
    """
    __tablename__ = 'cart_items'
    
    cart_id = Column(String(60), ForeignKey('carts.id'), nullable=False)
    product_id = Column(String(60), ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)  # Price in USD at time of adding
    subtotal = Column(Float, default=0.0)  # Calculated field: quantity * unit_price
    
    # Relationships
    cart = relationship('Cart', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')
    
    def calculate_subtotal(self):
        """
        Calculate and update the subtotal for this cart item.
        
        Returns:
            float: The calculated subtotal (quantity * unit_price)
        """
        self.subtotal = self.quantity * self.unit_price
        return self.subtotal
    
    def update_quantity(self, new_quantity):
        """
        Update the quantity of this cart item and recalculate subtotal.
        
        Args:
            new_quantity (int): The new quantity for this cart item
            
        Returns:
            float: The updated subtotal
        """
        from modules.Products.product import Product
        from modules import storage
        
        if new_quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        # Validate product exists
        product = storage.get(Product, self.product_id)
        if not product:
            raise ValueError(f"Product with ID {self.product_id} not found")
        
        self.quantity = new_quantity
        return self.calculate_subtotal()
    
    def to_dict(self):
        """
        Convert CartItem instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing cart item data
        """
        cart_item_dict = super().to_dict()
        cart_item_dict.update({
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal
        })
        return cart_item_dict