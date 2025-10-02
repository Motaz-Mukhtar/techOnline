#!/usr/bin/env python3
"""
Search Engine for TechOnline e-commerce platform.

This module provides comprehensive search functionality including:
- Product search by name, description, and category
- Advanced filtering by price range, category, availability
- Search result ranking and sorting
"""
import modules
from modules.Products.product import Product
from modules.Category.category import Category
from sqlalchemy import and_, or_


class Search:
    """
    Advanced search engine for products and other entities.
    
    Provides methods for searching products with various filters
    and sorting options.
    """
    
    @staticmethod
    def search_products_by_name(search_term, limit=None):
        """
        Search products by name with case-insensitive matching.
        
        Args:
            search_term (str): The search term to match against product names
            limit (int, optional): Maximum number of results to return
            
        Returns:
            list: List of Product objects matching the search term
        """
        if not search_term or not search_term.strip():
            return []
            
        modules.storage.reload()
        
        try:
            query = modules.storage._DBStorage__session.query(Product).filter(
                Product.product_name.ilike(f'%{search_term.strip()}%')
            )
            
            if limit:
                query = query.limit(limit)
                
            result = query.all()
            return result
            
        except Exception as e:
            print(f"Error in search_products_by_name: {e}")
            return []
        finally:
            modules.storage._DBStorage__session.close()
    
    @staticmethod
    def search_products_advanced(search_term=None, category_id=None, min_price=None, 
                               max_price=None, in_stock_only=True, limit=None, sort_by='name'):
        """
        Advanced product search with multiple filters.
        
        Args:
            search_term (str, optional): Search term for product name/description
            category_id (str, optional): Filter by category ID
            min_price (float, optional): Minimum price filter
            max_price (float, optional): Maximum price filter
            in_stock_only (bool): Only return products in stock
            limit (int, optional): Maximum number of results
            sort_by (str): Sort results by 'name', 'price', 'created_at'
            
        Returns:
            list: List of Product objects matching the criteria
        """
        modules.storage.reload()
        
        try:
            query = modules.storage._DBStorage__session.query(Product)
            
            # Apply filters
            filters = []
            
            # Search term filter (name and description)
            if search_term and search_term.strip():
                term = f"%{search_term.strip()}%"
                filters.append(
                    or_(
                        Product.product_name.ilike(term),
                        Product.description.ilike(term)
                    )
                )
            
            # Category filter
            if category_id:
                filters.append(Product.category_id == category_id)
            
            # Price range filters
            if min_price is not None:
                filters.append(Product.price >= min_price)
            if max_price is not None:
                filters.append(Product.price <= max_price)
            
            # Stock availability filter
            if in_stock_only:
                filters.append(Product.stock_quantity > 0)
                filters.append(Product.is_available == True)
            
            # Apply all filters
            if filters:
                query = query.filter(and_(*filters))
            
            # Apply sorting
            if sort_by == 'price':
                query = query.order_by(Product.price)
            elif sort_by == 'created_at':
                query = query.order_by(Product.created_at.desc())
            else:  # default to name
                query = query.order_by(Product.product_name)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            result = query.all()
            return result
            
        except Exception as e:
            print(f"Error in search_products_advanced: {e}")
            return []
        finally:
            modules.storage._DBStorage__session.close()
    
    @staticmethod
    def search_by_category(category_name, limit=None):
        """
        Search products by category name.
        
        Args:
            category_name (str): Name of the category to search for
            limit (int, optional): Maximum number of results
            
        Returns:
            list: List of Product objects in the specified category
        """
        if not category_name or not category_name.strip():
            return []
            
        modules.storage.reload()
        
        try:
            # First find the category
            category = modules.storage._DBStorage__session.query(Category).filter(
                Category.name.ilike(f'%{category_name.strip()}%')
            ).first()
            
            if not category:
                return []
            
            # Then find products in that category
            query = modules.storage._DBStorage__session.query(Product).filter(
                Product.category_id == category.id
            )
            
            if limit:
                query = query.limit(limit)
                
            result = query.all()
            return result
            
        except Exception as e:
            print(f"Error in search_by_category: {e}")
            return []
        finally:
            modules.storage._DBStorage__session.close()
    
    @staticmethod
    def get_search_suggestions(search_term, limit=5):
        """
        Get search suggestions based on partial input.
        
        Args:
            search_term (str): Partial search term
            limit (int): Maximum number of suggestions
            
        Returns:
            list: List of suggested product names
        """
        if not search_term or len(search_term.strip()) < 2:
            return []
            
        modules.storage.reload()
        
        try:
            products = modules.storage._DBStorage__session.query(Product.product_name).filter(
                Product.product_name.ilike(f'%{search_term.strip()}%')
            ).limit(limit).all()
            
            suggestions = [product.product_name for product in products]
            return suggestions
            
        except Exception as e:
            print(f"Error in get_search_suggestions: {e}")
            return []
        finally:
            modules.storage._DBStorage__session.close()
    
    @staticmethod
    def search_query_by_id(obj_class, obj_id):
        """
        Search for an object by its ID.
        
        Args:
            obj_class: The class of the object to search for
            obj_id (str): ID of the object
            
        Returns:
            object or None: The found object or None if not found
        """
        modules.storage.reload()
        
        try:
            result = modules.storage._DBStorage__session.query(obj_class).filter(
                obj_class.id == obj_id
            ).first()
            return result
            
        except Exception as e:
            print(f"Error in search_query_by_id: {e}")
            return None
        finally:
            modules.storage._DBStorage__session.close()