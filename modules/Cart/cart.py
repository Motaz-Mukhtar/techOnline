#!/usr/bin/env python3
"""Create Cart Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Cart(BaseModel, Base):
    """
    Cart Class for Shopping Cart Management
    
    This model represents a shopping cart that belongs to a customer
    and contains multiple products through the CartItem junction table.
    
    Attributes:
        total_price (float): Total price of all items in cart (USD), calculated automatically
        customer_id (str): Foreign key reference to Customer.id
        
    Relationships:
        cart_items: List of CartItem objects associated with this cart
        customer: Back reference to the Customer model
    """
    __tablename__ = 'carts'
    total_price = Column(Float, default=0.0)
    customer_id = Column(String(60), ForeignKey("customers.id"), nullable=False)
    
    # Relationships
    cart_items = relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')
    
    def calculate_total_price(self):
        """
        Calculate and update the total price of all items in the cart.
        
        Iterates through all cart items, ensures their subtotals are current,
        and sums them to get the total cart price in USD.
        
        Returns:
            float: The calculated total price in USD
        """
        total = 0.0
        
        for cart_item in self.cart_items:
            # Ensure subtotal is calculated
            cart_item.calculate_subtotal()
            total += cart_item.subtotal
        
        self.total_price = round(total, 2)  # Round to 2 decimal places for currency
        return self.total_price
    
    def add_product(self, product_id, quantity=1):
        """
        Add a product to the cart or update quantity if it already exists.
        
        Args:
            product_id (str): ID of the product to add
            quantity (int): Quantity to add (default: 1)
            
        Returns:
            CartItem: The created or updated cart item
            
        Raises:
            ValueError: If product doesn't exist or quantity is invalid
        """
        from modules.Products.product import Product
        from modules.Cart.cart_item import CartItem
        from modules import storage
        
        # Validate product exists
        product = storage.get(Product, product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        # Check if product already exists in cart
        existing_item = None
        for cart_item in self.cart_items:
            if cart_item.product_id == product_id:
                existing_item = cart_item
                break
        
        if existing_item:
            # Update existing item quantity
            existing_item.quantity += quantity
            existing_item.calculate_subtotal()
            cart_item_result = existing_item
        else:
            # Create new cart item
            new_cart_item = CartItem(
                cart_id=self.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price
            )
            new_cart_item.calculate_subtotal()
            self.cart_items.append(new_cart_item)
            cart_item_result = new_cart_item
        
        # Recalculate total price
        self.calculate_total_price()
        
        return cart_item_result
    
    def remove_product(self, product_id):
        """
        Remove a product completely from the cart.
        
        Args:
            product_id (str): ID of the product to remove
            
        Returns:
            bool: True if product was removed, False if not found
        """
        from modules import storage
        
        for cart_item in self.cart_items:
            if cart_item.product_id == product_id:
                storage.delete(cart_item)
                self.calculate_total_price()
                return True
        return False
    
    def update_product_quantity(self, product_id, new_quantity):
        """
        Update the quantity of a specific product in the cart.
        
        Args:
            product_id (str): ID of the product to update
            new_quantity (int): New quantity for the product
            
        Returns:
            CartItem: The updated cart item
            
        Raises:
            ValueError: If product not found in cart or invalid quantity
        """
        if new_quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        for cart_item in self.cart_items:
            if cart_item.product_id == product_id:
                cart_item.update_quantity(new_quantity)
                self.calculate_total_price()
                return cart_item
        
        raise ValueError(f"Product with ID {product_id} not found in cart")
    
    def clear_cart(self):
        """
        Remove all items from the cart and reset total price.
        """
        from modules import storage
        
        # Clear all cart items
        for item in self.cart_items[:]:
            storage.delete(item)
        self.total_price = 0.0
    
    def get_item_count(self):
        """
        Get the total number of individual items in the cart.
        
        Returns:
            int: Total quantity of all items in cart
        """
        return sum(cart_item.quantity for cart_item in self.cart_items)
    
    @property
    def products(self):
        """
        Get all products in the cart through cart items.
        
        Returns:
            list: List of Product objects in the cart
        """
        from modules.Products.product import Product
        from modules import storage
        
        products = []
        for cart_item in self.cart_items:
            product = storage.get(Product, cart_item.product_id)
            if product:
                products.append(product)
        return products
    
    def to_dict(self):
        """
        Convert Cart instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing cart data including items
        """
        cart_dict = super().to_dict()
        cart_dict.update({
            'total_price': self.total_price,
            'customer_id': self.customer_id,
            'item_count': self.get_item_count(),
            'cart_items': [item.to_dict() for item in self.cart_items]
        })
        return cart_dict
