#!/usr/bin/env python3
"""Create Product Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Product(BaseModel, Base):
    """
    Product Class for E-commerce Product Management
    
    This model represents products in the e-commerce system that can be
    added to shopping carts and purchased by customers.
    
    Attributes:
        product_name (str): Name of the product
        description (str): Detailed description of the product
        price (float): Price of the product in USD
        rate (float): Average rating of the product (0.0-5.0)
        product_image (str): Base64 encoded product image data
        customer_id (str): Foreign key reference to the customer who created this product
        category_id (str): Foreign key reference to product category (commented out)
        
    Relationships:
        cart_items: List of CartItem objects that reference this product
        customer: Back reference to the Customer who created this product
    """
    __tablename__ = "products"
    product_name = Column(String(60))
    description = Column(String(1024))
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    price = Column(Float)
    rate = Column(Float, default=0.0)
    # Store image file path/URL instead of Base64 data
    product_image = Column(String(255))  # Store file path or URL
    product_image_filename = Column(String(255))  # Store original filename for management
    category_id = Column(String(60), ForeignKey('categories.id'), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    is_available = Column(String(5), nullable=False, default='True')
    min_stock_level = Column(Integer, nullable=False, default=5)
    
    # Relationships
    cart_items = relationship('CartItem', back_populates='product', cascade='all, delete-orphan')
    order_items = relationship("OrderItem", back_populates="product")
    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product", cascade='all, delete-orphan')
    
    def check_stock_availability(self, requested_quantity=1):
        """
        Check if the requested quantity is available in stock.
        
        Args:
            requested_quantity (int): Quantity to check availability for
            
        Returns:
            bool: True if stock is available, False otherwise
        """
        return (self.is_available == 'True' and 
                self.stock_quantity >= requested_quantity)
    
    def update_stock(self, quantity_change):
        """
        Update the stock quantity by the specified amount.
        
        Args:
            quantity_change (int): Positive for restocking, negative for sales
            
        Raises:
            ValueError: If the operation would result in negative stock
        """
        new_quantity = self.stock_quantity + quantity_change
        
        if new_quantity < 0:
            raise ValueError(f"Insufficient stock. Available: {self.stock_quantity}, Requested: {abs(quantity_change)}")
        
        self.stock_quantity = new_quantity
        
        # Auto-disable product if stock is zero
        if self.stock_quantity == 0:
            self.is_available = 'False'
        elif self.stock_quantity > 0 and self.is_available == 'False':
            self.is_available = 'True'
    
    def is_low_stock(self):
        """
        Check if the product stock is below minimum level.
        
        Returns:
            bool: True if stock is low, False otherwise
        """
        return self.stock_quantity <= self.min_stock_level
    
    def get_stock_status(self):
        """
        Get a descriptive stock status.
        
        Returns:
            str: Stock status description
        """
        if self.stock_quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock():
            return "Low Stock"
        else:
            return "In Stock"
    
    def calculate_average_rating(self):
        """
        Calculate and update the average rating for this product based on approved reviews.
        
        Returns:
            tuple: (average_rating, total_reviews)
        """
        from modules.Review.review import Review
        
        # Get average rating using the Review model's static method
        average_rating, total_reviews = Review.get_average_rating_for_product(self.id)
        
        # Update the product's rate field
        self.rate = average_rating
        self.save()
        
        return average_rating, total_reviews
    
    def get_review_summary(self):
        """
        Get a summary of reviews for this product.
        
        Returns:
            dict: Review summary including average rating, total reviews, and distribution
        """
        from modules.Review.review import Review
        
        average_rating, total_reviews = Review.get_average_rating_for_product(self.id)
        rating_distribution = Review.get_rating_distribution_for_product(self.id)
        
        return {
            'average_rating': average_rating,
            'total_reviews': total_reviews,
            'rating_distribution': rating_distribution,
            'has_reviews': total_reviews > 0
        }
    
    def get_recent_reviews(self, limit=5):
        """
        Get recent approved reviews for this product.
        
        Args:
            limit (int): Maximum number of reviews to return
            
        Returns:
            list: List of recent Review objects
        """
        from modules import storage
        from modules.Review.review import Review
        
        # Get all approved reviews for this product
        all_reviews = storage.all(Review)
        product_reviews = [
            review for review in all_reviews.values()
            if review.product_id == self.id and review.is_approved == 1
        ]
        
        # Sort by creation date (most recent first) and limit
        product_reviews.sort(key=lambda x: x.created_at, reverse=True)
        return product_reviews[:limit]
    
    def has_customer_reviewed(self, customer_id):
        """
        Check if a specific customer has already reviewed this product.
        
        Args:
            customer_id (str): The customer ID to check
            
        Returns:
            bool: True if customer has reviewed this product, False otherwise
        """
        from modules import storage
        from modules.Review.review import Review
        
        all_reviews = storage.all(Review)
        customer_reviews = [
            review for review in all_reviews.values()
            if review.product_id == self.id and review.customer_id == customer_id
        ]
        
        return len(customer_reviews) > 0
    
    def to_dict(self):
        """
        Convert Product instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all Product attributes and review summary
        """
        product_dict = super().to_dict()
        
        # Get review summary
        review_summary = self.get_review_summary()
        
        product_dict.update({
            'product_name': self.product_name,
            'description': self.description,
            'price': self.price,
            'rate': self.rate,
            'product_image': self.product_image,
            'customer_id': self.customer_id,
            'category_id': self.category_id,
            'stock_quantity': self.stock_quantity,
            'is_available': self.is_available,
            'min_stock_level': self.min_stock_level,
            'stock_status': self.get_stock_status(),
            'is_low_stock': self.is_low_stock(),
            # Review information
            'average_rating': review_summary['average_rating'],
            'total_reviews': review_summary['total_reviews'],
            'rating_distribution': review_summary['rating_distribution'],
            'has_reviews': review_summary['has_reviews']
        })
        
        return product_dict