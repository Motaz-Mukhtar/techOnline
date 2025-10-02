from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from modules.Products.product import Product
from modules.Order.order_item import OrderItem


class StockManager:
    """
    Comprehensive stock management system for e-commerce inventory.
    
    This class handles inventory tracking, stock validation, low stock alerts,
    and stock movement logging for products in the system.
    """
    
    # Stock level thresholds
    LOW_STOCK_THRESHOLD = 10
    CRITICAL_STOCK_THRESHOLD = 5
    
    def __init__(self, db_session=None):
        """
        Initialize StockManager with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
    
    def check_stock_availability(self, product_id: str, requested_quantity: int) -> Dict:
        """
        Check if requested quantity is available for a product.
        
        Args:
            product_id (str): Product ID to check
            requested_quantity (int): Quantity requested
        
        Returns:
            Dict: Stock availability information
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        product = self.db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            return {
                'available': False,
                'reason': 'Product not found',
                'current_stock': 0,
                'requested_quantity': requested_quantity,
                'can_fulfill': False
            }
        
        current_stock = product.stock_quantity or 0
        can_fulfill = current_stock >= requested_quantity
        
        return {
            'available': can_fulfill,
            'reason': 'Sufficient stock' if can_fulfill else 'Insufficient stock',
            'current_stock': current_stock,
            'requested_quantity': requested_quantity,
            'can_fulfill': can_fulfill,
            'remaining_after_fulfillment': current_stock - requested_quantity if can_fulfill else current_stock,
            'stock_level': self._get_stock_level_status(current_stock)
        }
    
    def check_multiple_products_stock(self, product_quantities: List[Dict]) -> Dict:
        """
        Check stock availability for multiple products.
        
        Args:
            product_quantities (List[Dict]): List of {'product_id': str, 'quantity': int}
        
        Returns:
            Dict: Overall stock check results
        """
        results = []
        all_available = True
        total_value = Decimal('0.00')
        
        for item in product_quantities:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            stock_check = self.check_stock_availability(product_id, quantity)
            
            if stock_check['available']:
                # Get product price for value calculation
                product = self.db_session.query(Product).filter_by(id=product_id).first()
                if product and product.price:
                    item_value = Decimal(str(product.price)) * Decimal(str(quantity))
                    total_value += item_value
                    stock_check['item_value'] = float(item_value)
            else:
                all_available = False
                stock_check['item_value'] = 0.0
            
            results.append(stock_check)
        
        return {
            'all_available': all_available,
            'total_order_value': float(total_value),
            'items': results,
            'unavailable_items': [item for item in results if not item['available']]
        }
    
    def reserve_stock(self, product_id: str, quantity: int, order_id: Optional[str] = None) -> Dict:
        """
        Reserve stock for a product (reduce available quantity).
        
        Args:
            product_id (str): Product ID
            quantity (int): Quantity to reserve
            order_id (str, optional): Associated order ID
        
        Returns:
            Dict: Reservation result
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        # Check availability first
        stock_check = self.check_stock_availability(product_id, quantity)
        
        if not stock_check['available']:
            return {
                'success': False,
                'message': f"Cannot reserve {quantity} units. {stock_check['reason']}",
                'current_stock': stock_check['current_stock']
            }
        
        # Reserve the stock
        product = self.db_session.query(Product).filter_by(id=product_id).first()
        original_stock = product.stock_quantity
        product.stock_quantity -= quantity
        
        try:
            self.db_session.commit()
            
            # Log stock movement
            self._log_stock_movement(
                product_id=product_id,
                movement_type='reserved',
                quantity=-quantity,
                previous_stock=original_stock,
                new_stock=product.stock_quantity,
                order_id=order_id,
                notes=f"Stock reserved for order {order_id}" if order_id else "Stock reserved"
            )
            
            return {
                'success': True,
                'message': f"Successfully reserved {quantity} units",
                'previous_stock': original_stock,
                'current_stock': product.stock_quantity,
                'stock_level': self._get_stock_level_status(product.stock_quantity)
            }
        
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'message': f"Failed to reserve stock: {str(e)}",
                'current_stock': original_stock
            }
    
    def release_stock(self, product_id: str, quantity: int, order_id: Optional[str] = None) -> Dict:
        """
        Release previously reserved stock (increase available quantity).
        
        Args:
            product_id (str): Product ID
            quantity (int): Quantity to release
            order_id (str, optional): Associated order ID
        
        Returns:
            Dict: Release result
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        product = self.db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            return {
                'success': False,
                'message': 'Product not found',
                'current_stock': 0
            }
        
        original_stock = product.stock_quantity or 0
        product.stock_quantity = original_stock + quantity
        
        try:
            self.db_session.commit()
            
            # Log stock movement
            self._log_stock_movement(
                product_id=product_id,
                movement_type='released',
                quantity=quantity,
                previous_stock=original_stock,
                new_stock=product.stock_quantity,
                order_id=order_id,
                notes=f"Stock released from order {order_id}" if order_id else "Stock released"
            )
            
            return {
                'success': True,
                'message': f"Successfully released {quantity} units",
                'previous_stock': original_stock,
                'current_stock': product.stock_quantity,
                'stock_level': self._get_stock_level_status(product.stock_quantity)
            }
        
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'message': f"Failed to release stock: {str(e)}",
                'current_stock': original_stock
            }
    
    def update_stock_quantity(self, product_id: str, new_quantity: int, reason: str = "Manual update") -> Dict:
        """
        Update product stock quantity directly.
        
        Args:
            product_id (str): Product ID
            new_quantity (int): New stock quantity
            reason (str): Reason for the update
        
        Returns:
            Dict: Update result
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        if new_quantity < 0:
            return {
                'success': False,
                'message': 'Stock quantity cannot be negative',
                'current_stock': 0
            }
        
        product = self.db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            return {
                'success': False,
                'message': 'Product not found',
                'current_stock': 0
            }
        
        original_stock = product.stock_quantity or 0
        quantity_change = new_quantity - original_stock
        product.stock_quantity = new_quantity
        
        try:
            self.db_session.commit()
            
            # Log stock movement
            self._log_stock_movement(
                product_id=product_id,
                movement_type='adjustment',
                quantity=quantity_change,
                previous_stock=original_stock,
                new_stock=new_quantity,
                notes=reason
            )
            
            return {
                'success': True,
                'message': f"Stock updated from {original_stock} to {new_quantity}",
                'previous_stock': original_stock,
                'current_stock': new_quantity,
                'quantity_change': quantity_change,
                'stock_level': self._get_stock_level_status(new_quantity)
            }
        
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'message': f"Failed to update stock: {str(e)}",
                'current_stock': original_stock
            }
    
    def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Dict]:
        """
        Get products with low stock levels.
        
        Args:
            threshold (int, optional): Custom low stock threshold
        
        Returns:
            List[Dict]: Products with low stock
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        threshold = threshold or self.LOW_STOCK_THRESHOLD
        
        low_stock_products = self.db_session.query(Product).filter(
            Product.stock_quantity <= threshold,
            Product.stock_quantity > 0
        ).all()
        
        results = []
        for product in low_stock_products:
            results.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'current_stock': product.stock_quantity,
                'stock_level': self._get_stock_level_status(product.stock_quantity),
                'price': float(product.price) if product.price else 0.0,
                'category_id': product.category_id
            })
        
        return results
    
    def get_out_of_stock_products(self) -> List[Dict]:
        """
        Get products that are out of stock.
        
        Returns:
            List[Dict]: Out of stock products
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        out_of_stock_products = self.db_session.query(Product).filter(
            Product.stock_quantity <= 0
        ).all()
        
        results = []
        for product in out_of_stock_products:
            results.append({
                'product_id': product.id,
                'product_name': product.product_name,
                'current_stock': product.stock_quantity or 0,
                'stock_level': 'out_of_stock',
                'price': float(product.price) if product.price else 0.0,
                'category_id': product.category_id
            })
        
        return results
    
    def _get_stock_level_status(self, stock_quantity: int) -> str:
        """
        Get stock level status based on quantity.
        
        Args:
            stock_quantity (int): Current stock quantity
        
        Returns:
            str: Stock level status
        """
        if stock_quantity <= 0:
            return 'out_of_stock'
        elif stock_quantity <= self.CRITICAL_STOCK_THRESHOLD:
            return 'critical'
        elif stock_quantity <= self.LOW_STOCK_THRESHOLD:
            return 'low'
        else:
            return 'normal'
    
    def _log_stock_movement(self, product_id: str, movement_type: str, quantity: int,
                           previous_stock: int, new_stock: int, order_id: Optional[str] = None,
                           notes: Optional[str] = None) -> None:
        """
        Log stock movement for audit purposes.
        
        Args:
            product_id (str): Product ID
            movement_type (str): Type of movement (reserved, released, adjustment)
            quantity (int): Quantity changed
            previous_stock (int): Stock before change
            new_stock (int): Stock after change
            order_id (str, optional): Associated order ID
            notes (str, optional): Additional notes
        """
        # This would typically log to a stock_movements table
        # For now, we'll just print for debugging
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'product_id': product_id,
            'movement_type': movement_type,
            'quantity_change': quantity,
            'previous_stock': previous_stock,
            'new_stock': new_stock,
            'order_id': order_id,
            'notes': notes
        }
        
        # In a production system, this would be saved to a database table
        print(f"Stock Movement Log: {log_entry}")