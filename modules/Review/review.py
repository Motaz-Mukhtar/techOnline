#!/usr/bin/env python3
"""
Review Model for TechOnline E-commerce Platform.

This module defines the Review class which handles product reviews and ratings.
Includes validation methods, relationship management, and rating calculations.
"""

from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import String, Column, Float, ForeignKey, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import re


class Review(BaseModel, Base):
    """
    Review Class for managing product reviews and ratings.

    This class handles customer reviews for products, including:
    - Review text and ratings
    - Customer and product relationships
    - Review validation and moderation
    - Rating calculations and statistics

    Attributes:
        text (str): The review text content (max 2048 characters)
        product_id (str): Foreign key to the reviewed product
        customer_id (str): Foreign key to the reviewing customer
        rate (float): Rating score (1.0 to 5.0)
        title (str): Review title/summary
        is_verified (bool): Whether the review is from a verified purchase
        is_approved (bool): Whether the review has been approved by moderation
        helpful_count (int): Number of users who found this review helpful
        created_at (datetime): When the review was created
        updated_at (datetime): When the review was last updated
    """
    __tablename__ = 'reviews'
    
    # Core review fields
    text = Column(Text, nullable=False)  # Changed to Text for longer reviews
    title = Column(String(200), nullable=True)  # Review title
    product_id = Column(String(60), ForeignKey('products.id'), nullable=False)
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    rate = Column(Float, nullable=False, default=5.0)
    
    # Review status and moderation
    is_verified = Column(Integer, default=0)  # 0=False, 1=True (verified purchase)
    is_approved = Column(Integer, default=1)  # 0=False, 1=True (approved by moderation)
    helpful_count = Column(Integer, default=0)  # Number of helpful votes
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    customer = relationship("Customer", back_populates="reviews")
    
    def validate_rating(self, rating):
        """
        Validate the rating value.
        
        Args:
            rating (float): The rating to validate
            
        Returns:
            bool: True if rating is valid, False otherwise
        """
        try:
            rating = float(rating)
            return 1.0 <= rating <= 5.0
        except (ValueError, TypeError):
            return False
    
    def validate_text(self, text):
        """
        Validate the review text content.
        
        Args:
            text (str): The review text to validate
            
        Returns:
            bool: True if text is valid, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
        
        # Remove extra whitespace
        text = text.strip()
        
        # Check minimum length (at least 10 characters)
        if len(text) < 10:
            return False
        
        # Check maximum length (2000 characters)
        if len(text) > 2000:
            return False
        
        # Basic profanity filter (simple implementation)
        profanity_words = ['spam', 'fake', 'scam']  # Add more as needed
        text_lower = text.lower()
        for word in profanity_words:
            if word in text_lower:
                return False
        
        return True
    
    def validate_title(self, title):
        """
        Validate the review title.
        
        Args:
            title (str): The review title to validate
            
        Returns:
            bool: True if title is valid, False otherwise
        """
        if title is None:
            return True  # Title is optional
        
        if not isinstance(title, str):
            return False
        
        title = title.strip()
        return 5 <= len(title) <= 200
    
    def is_valid_review(self):
        """
        Check if the current review instance is valid.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate rating
        if not self.validate_rating(self.rate):
            return False, "Rating must be between 1.0 and 5.0"
        
        # Validate text
        if not self.validate_text(self.text):
            return False, "Review text must be between 10 and 2000 characters and contain appropriate content"
        
        # Validate title if provided
        if not self.validate_title(self.title):
            return False, "Review title must be between 5 and 200 characters if provided"
        
        # Validate required foreign keys
        if not self.product_id or not self.customer_id:
            return False, "Product ID and Customer ID are required"
        
        return True, "Valid review"
    
    def approve_review(self):
        """
        Approve the review for public display.
        """
        self.is_approved = 1
        self.save()
    
    def reject_review(self):
        """
        Reject the review (hide from public display).
        """
        self.is_approved = 0
        self.save()
    
    def mark_as_verified(self):
        """
        Mark the review as from a verified purchase.
        """
        self.is_verified = 1
        self.save()
    
    def add_helpful_vote(self):
        """
        Increment the helpful count for this review.
        """
        self.helpful_count += 1
        self.save()
    
    def get_rating_stars(self):
        """
        Get a string representation of the rating as stars.
        
        Returns:
            str: Star representation of the rating
        """
        full_stars = int(self.rate)
        half_star = 1 if (self.rate - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        return '★' * full_stars + '☆' * half_star + '☆' * empty_stars
    
    def to_dict(self):
        """
        Convert the review instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the review
        """
        review_dict = super().to_dict()
        
        # Add computed fields
        review_dict.update({
            'rating_stars': self.get_rating_stars(),
            'is_verified_purchase': bool(self.is_verified),
            'is_approved_review': bool(self.is_approved),
            'helpful_votes': self.helpful_count,
            'review_length': len(self.text) if self.text else 0
        })
        
        # Add related data if available
        if hasattr(self, 'customer') and self.customer:
            review_dict['customer_name'] = f"{self.customer.first_name} {self.customer.last_name[0]}."
        
        if hasattr(self, 'product') and self.product:
            review_dict['product_name'] = self.product.product_name
        
        return review_dict
    
    @staticmethod
    def get_average_rating_for_product(product_id):
        """
        Calculate the average rating for a specific product.
        
        Args:
            product_id (str): The product ID to calculate rating for
            
        Returns:
            tuple: (average_rating, total_reviews)
        """
        from modules import storage
        
        # Get all approved reviews for the product
        all_reviews = storage.all(Review)
        product_reviews = [
            review for review in all_reviews.values()
            if review.product_id == product_id and review.is_approved == 1
        ]
        
        if not product_reviews:
            return 0.0, 0
        
        total_rating = sum(review.rate for review in product_reviews)
        average_rating = round(total_rating / len(product_reviews), 1)
        
        return average_rating, len(product_reviews)
    
    @staticmethod
    def get_rating_distribution_for_product(product_id):
        """
        Get the rating distribution for a specific product.
        
        Args:
            product_id (str): The product ID to get distribution for
            
        Returns:
            dict: Rating distribution (1-5 stars with counts)
        """
        from modules import storage
        
        # Initialize distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Get all approved reviews for the product
        all_reviews = storage.all(Review)
        product_reviews = [
            review for review in all_reviews.values()
            if review.product_id == product_id and review.is_approved == 1
        ]
        
        # Count ratings
        for review in product_reviews:
            rating_int = int(round(review.rate))
            if 1 <= rating_int <= 5:
                distribution[rating_int] += 1
        
        return distribution
    

