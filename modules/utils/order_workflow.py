from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from modules.utils.stock_manager import StockManager

if TYPE_CHECKING:
    from modules.Order.order import Order


class OrderStatus(Enum):
    """
    Enumeration of possible order statuses.
    """
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    FAILED = 'failed'


class OrderWorkflowManager:
    """
    Comprehensive order workflow management system.
    
    This class handles order state transitions, validation of status changes,
    business rules enforcement, and integration with stock management.
    """
    
    # Define valid status transitions
    VALID_TRANSITIONS = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.FAILED},
        OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
        OrderStatus.CANCELLED: set(),  # Terminal state
        OrderStatus.REFUNDED: set(),   # Terminal state
        OrderStatus.FAILED: {OrderStatus.PENDING}  # Can retry
    }
    
    # Statuses that require stock reservation
    STOCK_RESERVED_STATUSES = {OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED}
    
    # Terminal statuses (cannot be changed)
    TERMINAL_STATUSES = {OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED}
    
    def __init__(self, db_session=None):
        """
        Initialize OrderWorkflowManager with database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.stock_manager = StockManager(db_session) if db_session else None
    
    def can_transition_to(self, current_status: str, target_status: str) -> bool:
        """
        Check if an order can transition from current status to target status.
        
        Args:
            current_status (str): Current order status
            target_status (str): Target order status
        
        Returns:
            bool: True if transition is valid
        """
        try:
            current = OrderStatus(current_status)
            target = OrderStatus(target_status)
            return target in self.VALID_TRANSITIONS.get(current, set())
        except ValueError:
            return False
    
    def get_valid_transitions(self, current_status: str) -> List[str]:
        """
        Get list of valid status transitions from current status.
        
        Args:
            current_status (str): Current order status
        
        Returns:
            List[str]: List of valid target statuses
        """
        try:
            current = OrderStatus(current_status)
            valid_statuses = self.VALID_TRANSITIONS.get(current, set())
            return [status.value for status in valid_statuses]
        except ValueError:
            return []
    
    def transition_order_status(self, order_id: str, new_status: str, 
                               reason: Optional[str] = None, 
                               user_id: Optional[str] = None) -> Dict:
        """
        Transition an order to a new status with validation and side effects.
        
        Args:
            order_id (str): Order ID
            new_status (str): Target status
            reason (str, optional): Reason for status change
            user_id (str, optional): User making the change
        
        Returns:
            Dict: Transition result
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        # Import Order here to avoid circular import
        from modules.Order.order import Order
        
        # Get the order
        order = self.db_session.query(Order).filter_by(id=order_id).first()
        if not order:
            return {
                'success': False,
                'message': 'Order not found',
                'current_status': None
            }
        
        current_status = order.order_status
        
        # Validate transition
        if not self.can_transition_to(current_status, new_status):
            return {
                'success': False,
                'message': f'Invalid status transition from {current_status} to {new_status}',
                'current_status': current_status,
                'valid_transitions': self.get_valid_transitions(current_status)
            }
        
        # Perform pre-transition actions
        pre_transition_result = self._handle_pre_transition_actions(
            order, current_status, new_status
        )
        
        if not pre_transition_result['success']:
            return pre_transition_result
        
        # Update order status
        old_status = order.order_status
        order.order_status = new_status
        
        try:
            self.db_session.commit()
            
            # Perform post-transition actions
            post_transition_result = self._handle_post_transition_actions(
                order, old_status, new_status
            )
            
            # Log status change
            self._log_status_change(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
                user_id=user_id
            )
            
            return {
                'success': True,
                'message': f'Order status changed from {old_status} to {new_status}',
                'previous_status': old_status,
                'current_status': new_status,
                'post_transition_actions': post_transition_result
            }
        
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'message': f'Failed to update order status: {str(e)}',
                'current_status': old_status
            }
    
    def bulk_transition_orders(self, order_ids: List[str], new_status: str, 
                              reason: Optional[str] = None, 
                              user_id: Optional[str] = None) -> Dict:
        """
        Transition multiple orders to a new status.
        
        Args:
            order_ids (List[str]): List of order IDs
            new_status (str): Target status
            reason (str, optional): Reason for status change
            user_id (str, optional): User making the change
        
        Returns:
            Dict: Bulk transition results
        """
        results = []
        successful_transitions = 0
        failed_transitions = 0
        
        for order_id in order_ids:
            result = self.transition_order_status(order_id, new_status, reason, user_id)
            results.append({
                'order_id': order_id,
                'result': result
            })
            
            if result['success']:
                successful_transitions += 1
            else:
                failed_transitions += 1
        
        return {
            'total_orders': len(order_ids),
            'successful_transitions': successful_transitions,
            'failed_transitions': failed_transitions,
            'results': results
        }
    
    def get_orders_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get orders filtered by status.
        
        Args:
            status (str): Order status to filter by
            limit (int, optional): Maximum number of orders to return
        
        Returns:
            List[Dict]: Orders with the specified status
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        # Import Order here to avoid circular import
        from modules.Order.order import Order
        
        query = self.db_session.query(Order).filter_by(order_status=status)
        
        if limit:
            query = query.limit(limit)
        
        orders = query.all()
        
        return [{
            'order_id': order.id,
            'customer_id': order.customer_id,
            'total_amount': order.total_amount,
            'order_status': order.order_status,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None
        } for order in orders]
    
    def get_order_status_summary(self) -> Dict:
        """
        Get summary of orders by status.
        
        Returns:
            Dict: Order count by status
        """
        if not self.db_session:
            raise ValueError("Database session is required")
        
        from sqlalchemy import func
        # Import Order here to avoid circular import
        from modules.Order.order import Order
        
        status_counts = self.db_session.query(
            Order.order_status,
            func.count(Order.id).label('count')
        ).group_by(Order.order_status).all()
        
        summary = {status.value: 0 for status in OrderStatus}
        
        for status, count in status_counts:
            summary[status] = count
        
        return summary
    
    def _handle_pre_transition_actions(self, order, current_status: str, new_status: str) -> Dict:
        """
        Handle actions that need to occur before status transition.
        
        Args:
            order (Order): Order object
            current_status (str): Current status
            new_status (str): Target status
        
        Returns:
            Dict: Pre-transition action results
        """
        actions_performed = []
        
        try:
            # Handle stock reservation when confirming order
            if (current_status == OrderStatus.PENDING.value and 
                new_status == OrderStatus.CONFIRMED.value):
                
                if self.stock_manager and order.order_items:
                    for item in order.order_items:
                        stock_result = self.stock_manager.reserve_stock(
                            product_id=item.product_id,
                            quantity=item.quantity,
                            order_id=order.id
                        )
                        
                        if not stock_result['success']:
                            return {
                                'success': False,
                                'message': f"Cannot confirm order: {stock_result['message']}",
                                'actions_performed': actions_performed
                            }
                        
                        actions_performed.append(f"Reserved {item.quantity} units of product {item.product_id}")
            
            # Handle stock release when cancelling order
            elif (current_status in [OrderStatus.CONFIRMED.value, OrderStatus.PROCESSING.value] and
                  new_status == OrderStatus.CANCELLED.value):
                
                if self.stock_manager and order.order_items:
                    for item in order.order_items:
                        stock_result = self.stock_manager.release_stock(
                            product_id=item.product_id,
                            quantity=item.quantity,
                            order_id=order.id
                        )
                        
                        if stock_result['success']:
                            actions_performed.append(f"Released {item.quantity} units of product {item.product_id}")
            
            return {
                'success': True,
                'actions_performed': actions_performed
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f"Pre-transition actions failed: {str(e)}",
                'actions_performed': actions_performed
            }
    
    def _handle_post_transition_actions(self, order: 'Order', old_status: str, new_status: str) -> Dict:
        """
        Handle actions that need to occur after status transition.
        
        Args:
            order (Order): Order object
            old_status (str): Previous status
            new_status (str): New status
        
        Returns:
            Dict: Post-transition action results
        """
        actions_performed = []
        
        try:
            # Update order pricing when confirming
            if new_status == OrderStatus.CONFIRMED.value:
                pricing_result = order.update_pricing(save_changes=False)
                actions_performed.append(f"Updated order pricing: ${pricing_result.get('final_total', 0):.2f}")
            
            # Send notifications (placeholder)
            if new_status in [OrderStatus.CONFIRMED.value, OrderStatus.SHIPPED.value, OrderStatus.DELIVERED.value]:
                actions_performed.append(f"Notification sent for status: {new_status}")
            
            return {
                'success': True,
                'actions_performed': actions_performed
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f"Post-transition actions failed: {str(e)}",
                'actions_performed': actions_performed
            }
    
    def _log_status_change(self, order_id: str, old_status: str, new_status: str,
                          reason: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """
        Log order status change for audit purposes.
        
        Args:
            order_id (str): Order ID
            old_status (str): Previous status
            new_status (str): New status
            reason (str, optional): Reason for change
            user_id (str, optional): User making the change
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'order_id': order_id,
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason,
            'user_id': user_id
        }
        
        # In a production system, this would be saved to a database table
        print(f"Order Status Change Log: {log_entry}")
    
    def validate_order_business_rules(self, order: 'Order') -> Dict:
        """
        Validate business rules for an order.
        
        Args:
            order (Order): Order to validate
        
        Returns:
            Dict: Validation results
        """
        validation_errors = []
        warnings = []
        
        # Check if order has items
        if not order.order_items or len(order.order_items) == 0:
            validation_errors.append("Order must have at least one item")
        
        # Check order total
        if order.total_amount <= 0:
            validation_errors.append("Order total must be greater than zero")
        
        # Check customer limits (placeholder for business rules)
        if order.total_amount > 10000:  # Example: high-value order warning
            warnings.append("High-value order requires additional verification")
        
        # Check stock availability for confirmed orders
        if (order.order_status in [OrderStatus.CONFIRMED.value, OrderStatus.PROCESSING.value] and
            self.stock_manager and order.order_items):
            
            for item in order.order_items:
                stock_check = self.stock_manager.check_stock_availability(
                    item.product_id, item.quantity
                )
                
                if not stock_check['available']:
                    validation_errors.append(
                        f"Insufficient stock for product {item.product_id}: "
                        f"requested {item.quantity}, available {stock_check['current_stock']}"
                    )
        
        return {
            'is_valid': len(validation_errors) == 0,
            'errors': validation_errors,
            'warnings': warnings
        }