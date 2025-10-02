#!/usr/bin/python3
"""
Category module for product categorization

This module defines the Category class that represents product categories
in the e-commerce system, allowing products to be organized and filtered.
"""

from modules.baseModel import BaseModel, Base
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship


class Category(BaseModel, Base):
    """
    Category class for organizing products.
    
    This class represents product categories in the e-commerce system,
    providing a way to organize and filter products by type, brand, or other criteria.
    
    Attributes:
        name (str): Name of the category (required, max 100 characters)
        description (str): Detailed description of the category (optional)
        slug (str): URL-friendly version of the category name (required, unique)
        parent_id (str): Foreign key to parent category for hierarchical structure (optional)
        is_active (bool): Whether the category is active and visible (default: True)
    
    Relationships:
        products: One-to-many relationship with Product
        subcategories: One-to-many relationship with child categories
        parent: Many-to-one relationship with parent category
    """
    
    __tablename__ = 'categories'
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(120), nullable=False, unique=True)
    parent_id = Column(String(60), nullable=True)  # For hierarchical categories
    is_active = Column(String(5), nullable=False, default='True')  # Using string for consistency
    
    # Relationships
    products = relationship("Product", back_populates="category")
    
    def __init__(self, *args, **kwargs):
        """
        Initialize Category instance.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments including:
                - name (str): Category name
                - description (str): Category description
                - slug (str): URL-friendly slug
                - parent_id (str): Parent category ID
                - is_active (str): Active status
        """
        super().__init__(*args, **kwargs)
        
        # Auto-generate slug from name if not provided
        if hasattr(self, 'name') and not hasattr(self, 'slug'):
            self.slug = self.generate_slug(self.name)
    
    def generate_slug(self, name):
        """
        Generate a URL-friendly slug from the category name.
        
        Args:
            name (str): Category name to convert to slug
            
        Returns:
            str: URL-friendly slug
        """
        import re
        
        if not name:
            return ""
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        return slug
    
    def get_active_products(self):
        """
        Get all active products in this category.
        
        Returns:
            list: List of active Product objects in this category
        """
        return [product for product in self.products if hasattr(product, 'is_active') and product.is_active == 'True']
    
    def get_product_count(self):
        """
        Get the total number of products in this category.
        
        Returns:
            int: Number of products in this category
        """
        return len(self.products) if self.products else 0
    
    def get_active_product_count(self):
        """
        Get the number of active products in this category.
        
        Returns:
            int: Number of active products in this category
        """
        return len(self.get_active_products())
    
    def activate(self):
        """
        Activate this category.
        """
        self.is_active = 'True'
    
    def deactivate(self):
        """
        Deactivate this category.
        """
        self.is_active = 'False'
    
    def is_category_active(self):
        """
        Check if this category is active.
        
        Returns:
            bool: True if category is active, False otherwise
        """
        return self.is_active == 'True'
    
    def to_dict(self):
        """
        Convert Category instance to dictionary representation.
        
        Returns:
            dict: Dictionary containing all Category attributes and related data
        """
        category_dict = super().to_dict()
        
        # Add computed fields
        category_dict['product_count'] = self.get_product_count()
        category_dict['active_product_count'] = self.get_active_product_count()
        category_dict['is_active_bool'] = self.is_category_active()
        
        return category_dict
    
    def __str__(self):
        """
        String representation of Category.
        
        Returns:
            str: Human-readable string representation
        """
        status = "Active" if self.is_category_active() else "Inactive"
        return f"Category(name={self.name}, slug={self.slug}, status={status})"
    
    def __repr__(self):
        """
        Official string representation of Category.
        
        Returns:
            str: Official string representation for debugging
        """
        return f"<Category {self.id}: {self.name} ({self.slug})>"